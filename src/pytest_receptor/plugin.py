import os
import re
import time
import threading
import pytest
from _pytest.terminal import TerminalReporter


def pytest_addhooks(pluginmanager):
    from pytest_receptor import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_addoption(parser):
    group = parser.getgroup("receptor")
    group.addoption(
        "--receptor",
        action="store",
        default="human",
        choices=["human", "llm", "ci"],
        help="Specify the receptor for pytest output (human, llm, ci).",
    )
    group.addoption(
        "--receptor-stats",
        action="store_true",
        help="Show comparative token statistics at the end of execution.",
    )
    group.addoption(
        "--receptor-dump-dir",
        action="store",
        default=None,
        help="Directory where to dump debug log files (human and llm) with a unique signature.",
    )
    group.addoption(
        "--receptor-artifact",
        action="store",
        default=None,
        help="Path to write the lossless JSONL evidence artifact.",
    )
    group.addoption(
        "--receptor-budget",
        action="store",
        default="1500",
        help="Character budget limit for exception message truncation to save LLM tokens.",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    receptor = config.getoption("--receptor")
    artifact_path = config.getoption("--receptor-artifact")

    if receptor in ("llm", "ci") or artifact_path:
        from pytest_receptor.collector import EventCollector

        collector = EventCollector(config)
        config._receptor_collector = collector
        config.pluginmanager.register(collector, "receptor_collector")
        collector.log_session_start()

    if receptor == "llm":
        standard_reporter = config.pluginmanager.getplugin("terminalreporter")
        if standard_reporter is not None:
            config.pluginmanager.unregister(standard_reporter)
        llm_reporter = LlmTerminalReporter(config)
        config.pluginmanager.register(llm_reporter, "terminalreporter")
    elif receptor == "ci":
        standard_reporter = config.pluginmanager.getplugin("terminalreporter")
        if standard_reporter is not None:
            config.pluginmanager.unregister(standard_reporter)
        ci_reporter = CiTerminalReporter(config)
        config.pluginmanager.register(ci_reporter, "terminalreporter")


class DummyTerminalWriter:
    def __init__(self, original_tw, config=None):
        self._original_tw = original_tw
        self.quiet = True
        self.captured_lines = []
        self.capture_enabled = False
        if config is not None:
            try:
                self.capture_enabled = bool(
                    config.getoption("--receptor-stats", False)
                    or config.getoption("--receptor-dump-dir", None) is not None
                )
            except ValueError:
                pass

    def write(self, msg, **kwargs):
        if self.quiet:
            if self.capture_enabled:
                self.captured_lines.append(msg)
        else:
            self._original_tw.write(msg, **kwargs)

    def line(self, msg="", **kwargs):
        if self.quiet:
            if self.capture_enabled:
                self.captured_lines.append(msg + "\n")
        else:
            self._original_tw.line(msg, **kwargs)

    def sep(self, sep, title=None, fullwidth=None, **kwargs):
        if self.quiet:
            if self.capture_enabled:
                title_str = f" {title} " if title else ""
                self.captured_lines.append(f"{sep * 10}{title_str}{sep * 10}\n")
        else:
            self._original_tw.sep(sep, title, fullwidth, **kwargs)

    def __getattr__(self, name):
        return getattr(self._original_tw, name)


class LlmTerminalReporter(TerminalReporter):
    def __init__(self, config, file=None):
        super().__init__(config, file)
        self._original_tw = self._tw
        self._tw = DummyTerminalWriter(self._tw, config)
        self._llm_start_time = time.monotonic()
        self._test_durations = {}

    def pytest_runtest_logreport(self, report):
        super().pytest_runtest_logreport(report)
        nodeid = report.nodeid
        self._test_durations[nodeid] = (
            self._test_durations.get(nodeid, 0.0) + report.duration
        )

    @pytest.hookimpl(wrapper=True)
    def pytest_sessionfinish(self, session, exitstatus):
        result = yield

        report_str = self.format_llm_report(exitstatus)
        self._original_tw.line("")  # Start on a new line
        self._original_tw.write(report_str)

        if self.config.getoption("--receptor-stats"):
            human_output = "".join(self._tw.captured_lines)
            try:
                import tiktoken

                encoding = tiktoken.get_encoding("cl100k_base")
                human_tokens = len(encoding.encode(human_output))
                llm_tokens = len(encoding.encode(report_str))
            except Exception:
                human_tokens = len(human_output) // 4
                llm_tokens = len(report_str) // 4

            savings_percent = (1 - (llm_tokens / max(1, human_tokens))) * 100
            stats_comment = f"\n<!-- [Receptor Stats] Human: {human_tokens} tokens | LLM: {llm_tokens} tokens | Saved: {savings_percent:.2f}% -->\n"
            self._original_tw.write(stats_comment)

        dump_dir = self.config.getoption("--receptor-dump-dir")
        if dump_dir:
            try:
                os.makedirs(dump_dir, exist_ok=True)
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pid = os.getpid()

                human_filename = f"pytest_human_{timestamp}_{pid}.log"
                llm_filename = f"pytest_llm_{timestamp}_{pid}.log"

                human_output = "".join(self._tw.captured_lines)

                with open(
                    os.path.join(dump_dir, human_filename),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(human_output)
                with open(
                    os.path.join(dump_dir, llm_filename), "w", encoding="utf-8"
                ) as f:
                    f.write(report_str)
            except Exception as e:
                self._original_tw.line(
                    f"Warning: Failed to write receptor logs to {dump_dir}: {e}"
                )

        return result

    def _xml_escape(self, val):
        if val is None:
            return ""
        val = str(val)
        val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        val = val.replace('"', "&quot;").replace("'", "&apos;")
        val = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", val)
        return val

    def _build_slow_tests_xml(self, root_dir):
        slow_tests = sorted(
            [
                (nodeid, dur)
                for nodeid, dur in self._test_durations.items()
                if dur >= 0.5
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:3]
        if not slow_tests:
            return ""
        xml = ["<slow_tests>"]
        for nodeid, dur in slow_tests:
            short_nodeid = nodeid
            if root_dir and os.path.isabs(nodeid.split("::")[0]):
                try:
                    parts_nid = nodeid.split("::", 1)
                    rel_path = os.path.relpath(parts_nid[0], start=root_dir)
                    short_nodeid = rel_path + "::" + parts_nid[1]
                except ValueError:
                    pass
            esc_name = self._xml_escape(short_nodeid)
            xml.append(f'<test name="{esc_name}" duration="{dur:.2f}s"/>')
        xml.append("</slow_tests>")
        return "".join(xml)

    def _get_report_reason(self, r):
        if hasattr(r, "wasxfail") and r.wasxfail:
            return str(r.wasxfail)
        if isinstance(r.longrepr, tuple) and len(r.longrepr) == 3:
            return str(r.longrepr[2])
        if hasattr(r.longrepr, "reprcrash") and r.longrepr.reprcrash:
            return str(r.longrepr.reprcrash.message)
        return str(getattr(r, "longrepr", ""))

    def _build_skips_xfails_xpassed_xml(self):
        xml = []
        skipped_reports = self.stats.get("skipped", [])
        if skipped_reports:
            skips_by_reason = {}
            for r in skipped_reports:
                reason = self._get_report_reason(r)
                skips_by_reason[reason] = skips_by_reason.get(reason, 0) + 1
            xml.append("<skipped_tests>")
            for reason, count in skips_by_reason.items():
                esc_reason = self._xml_escape(reason)
                xml.append(f'<group reason="{esc_reason}" count="{count}"/>')
            xml.append("</skipped_tests>")

        xfailed_reports = self.stats.get("xfailed", [])
        if xfailed_reports:
            xfails_by_reason = {}
            for r in xfailed_reports:
                reason = self._get_report_reason(r)
                xfails_by_reason[reason] = xfails_by_reason.get(reason, 0) + 1
            xml.append("<xfailed_tests>")
            for reason, count in xfails_by_reason.items():
                esc_reason = self._xml_escape(reason)
                xml.append(f'<group reason="{esc_reason}" count="{count}"/>')
            xml.append("</xfailed_tests>")

        xpassed_reports = self.stats.get("xpassed", [])
        if xpassed_reports:
            xml.append("<xpassed_tests>")
            for r in xpassed_reports:
                reason = self._get_report_reason(r)
                esc_nodeid = self._xml_escape(r.nodeid)
                esc_reason = self._xml_escape(reason)
                xml.append(f'<test name="{esc_nodeid}" reason="{esc_reason}"/>')
            xml.append("</xpassed_tests>")

        return "".join(xml)

    def _build_warnings_xml(self):
        warning_reports = self.stats.get("warnings", [])
        if not warning_reports:
            return ""
        warning_groups = {}
        for w in warning_reports:
            msg = str(getattr(w, "message", getattr(w, "warning", "")))
            category = str(getattr(w, "category", ""))
            if category == "None":
                category = ""
            fpath = str(getattr(w, "fpath", getattr(w, "filename", "")))
            if fpath == "None":
                fpath = ""
            line = str(getattr(w, "line", getattr(w, "lineno", "")))
            if line == "None":
                line = ""

            # Parse preformatted pytest warning messages if necessary
            if (not category or not fpath) and msg:
                m = re.match(
                    r"^(.+?):(\d+):\s*([a-zA-Z0-9_]+Warning):\s*(.*)$", msg, re.DOTALL
                )
                if m:
                    fpath = m.group(1)
                    line = m.group(2)
                    category = m.group(3)
                    msg = m.group(4).strip()

            if hasattr(category, "__name__"):
                category = category.__name__
            elif not isinstance(category, str):
                category = str(category)

            root_dir = getattr(
                self.config, "rootpath", getattr(self.config, "rootdir", None)
            )
            if root_dir and fpath and os.path.isabs(fpath):
                try:
                    fpath = os.path.relpath(fpath, start=root_dir)
                except ValueError:
                    pass

            norm_msg = self._normalize_message(msg)
            key = (category, norm_msg)
            if key not in warning_groups:
                warning_groups[key] = {
                    "category": category,
                    "message": msg,
                    "file": fpath,
                    "line": line,
                    "count": 0,
                }
            warning_groups[key]["count"] += 1

        xml = ["<warnings>"]
        for key, info in warning_groups.items():
            esc_cat = self._xml_escape(info["category"])
            esc_msg = self._xml_escape(info["message"])
            esc_file = self._xml_escape(info["file"])
            esc_line = self._xml_escape(info["line"])
            xml.append(
                f'<warning category="{esc_cat}" message="{esc_msg}" file="{esc_file}" line="{esc_line}" count="{info["count"]}"/>'
            )
        xml.append("</warnings>")
        return "".join(xml)

    def format_llm_report(self, exitstatus):
        exit_val = int(exitstatus)
        is_green = exit_val == 0

        if exit_val == 0:
            outcome_label = "OK"
        elif exit_val == 1:
            outcome_label = "FAILED"
        elif exit_val == 2:
            outcome_label = "INTERRUPTED"
        elif exit_val == 3:
            outcome_label = "INTERNAL_ERROR"
        elif exit_val == 4:
            outcome_label = "USAGE_ERROR"
        elif exit_val == 5:
            outcome_label = "NO_TESTS"
        else:
            outcome_label = "FAILED"

        collector = getattr(self.config, "_receptor_collector", None)
        if collector:
            # Group test phases by nodeid to count logical test results
            logical_tests = {}
            for phase_event in collector.test_phases:
                nid = phase_event.nodeid
                if nid not in logical_tests:
                    logical_tests[nid] = []
                logical_tests[nid].append(phase_event)

            passed_count = 0
            failed_count = 0
            skipped_count = 0
            xfailed_count = 0
            xpassed_count = 0
            error_count = 0

            for nid, phases in logical_tests.items():
                outcomes = [p.outcome for p in phases]
                if "failed" in outcomes:
                    failed_phase = next(p for p in phases if p.outcome == "failed")
                    if failed_phase.phase in ("setup", "teardown"):
                        error_count += 1
                    else:
                        failed_count += 1
                elif "error" in outcomes:
                    error_count += 1
                elif "xpassed" in outcomes:
                    xpassed_count += 1
                elif "xfailed" in outcomes:
                    xfailed_count += 1
                elif "skipped" in outcomes:
                    skipped_count += 1
                elif "passed" in outcomes:
                    passed_count += 1

            collected_count = (
                self._numtests if hasattr(self, "_numtests") else len(logical_tests)
            )
            warnings_count = len(collector.warnings)
        else:
            passed_count = len(self.stats.get("passed", []))
            skipped_count = len(self.stats.get("skipped", []))
            xfailed_count = len(self.stats.get("xfailed", []))
            xpassed_count = len(self.stats.get("xpassed", []))
            failed_count = len(self.stats.get("failed", []))
            error_count = len(self.stats.get("error", []))
            collected_count = (
                self._numtests
                if hasattr(self, "_numtests")
                else (
                    passed_count
                    + skipped_count
                    + xfailed_count
                    + xpassed_count
                    + failed_count
                    + error_count
                )
            )
            warnings_count = len(self.stats.get("warnings", []))

        duration = time.monotonic() - self._llm_start_time
        root_dir = getattr(
            self.config, "rootpath", getattr(self.config, "rootdir", None)
        )

        if is_green:
            report_str = f"OK exit=0 collected={collected_count} passed={passed_count} skipped={skipped_count} xfailed={xfailed_count} xpassed={xpassed_count} duration={duration:.2f}s warnings={warnings_count}\n"
            meta_xml = []
            meta_xml.append(self._build_slow_tests_xml(root_dir))
            meta_xml.append(self._build_skips_xfails_xpassed_xml())
            meta_xml.append(self._build_warnings_xml())

            meta_str = "".join([b for b in meta_xml if b])
            if meta_str:
                report_str += meta_str + "\n"
            return report_str

        # If not green
        report_str = f"{outcome_label} exit={exit_val} collected={collected_count} passed={passed_count} failed={failed_count} error={error_count} skipped={skipped_count} xfailed={xfailed_count} xpassed={xpassed_count} duration={duration:.2f}s warnings={warnings_count}\n"

        output = ["<test_failures>"]

        if collector:
            failed_events = [
                p for p in collector.test_phases if p.outcome in ("failed", "error")
            ]
            if failed_events:
                groups = {}
                for fe in failed_events:
                    exc = fe.exception
                    if not exc:
                        continue
                    exc_type = exc.exc_type
                    message = exc.message

                    normalized_msg = self._normalize_message(message)
                    key = (exc_type, normalized_msg)

                    path = fe.nodeid.split("::")[0]
                    if root_dir and os.path.isabs(path):
                        try:
                            path = os.path.relpath(path, start=root_dir)
                        except ValueError:
                            pass
                    line_no = 0
                    if exc.traceback:
                        last_frame = exc.traceback[-1]
                        m = re.search(r"at\s+(.+?):(\d+)\s+->", last_frame)
                        if m:
                            line_no = int(m.group(2))

                    sections_dict = {}
                    if fe.captured_stdout:
                        sections_dict["captured_stdout"] = fe.captured_stdout
                    if fe.captured_stderr:
                        sections_dict["captured_stderr"] = fe.captured_stderr
                    if fe.captured_log:
                        sections_dict["captured_log"] = fe.captured_log

                    local_tb = "\n" + "\n".join(exc.traceback) if exc.traceback else ""

                    if key not in groups:
                        groups[key] = {
                            "exc_type": exc_type,
                            "message": self._compress_message(
                                message, nodeid=fe.nodeid, phase=fe.phase
                            ),
                            "file": path,
                            "line": line_no,
                            "local_tb": local_tb,
                            "sections": sections_dict,
                            "tests": [],
                        }
                    groups[key]["tests"].append(
                        {
                            "nodeid": fe.nodeid,
                            "phase": fe.phase,
                            "captured_stdout": fe.captured_stdout,
                            "captured_stderr": fe.captured_stderr,
                            "captured_log": fe.captured_log,
                        }
                    )

                for key, g in groups.items():
                    exc_type_esc = self._xml_escape(g["exc_type"])
                    file_path_esc = self._xml_escape(g["file"])
                    line_no_esc = self._xml_escape(g["line"])
                    msg_content_esc = self._xml_escape(g["message"])
                    output.append(
                        f'<failure_group exception="{exc_type_esc}" file="{file_path_esc}" line="{line_no_esc}">'
                    )
                    output.append(f"<message>{msg_content_esc}</message>")

                    if len(g["tests"]) == 1:
                        rerun_cmd = f"pytest {g['tests'][0]['nodeid']} -q"
                    else:
                        rerun_cmd = f"pytest {g['file']} -q"
                    output.append(f"<rerun>{self._xml_escape(rerun_cmd)}</rerun>")

                    hint = self._get_correction_hint(
                        g["exc_type"], g["message"], root_dir
                    )
                    if hint:
                        output.append(f"<hint>{self._xml_escape(hint)}</hint>")

                    if g["local_tb"]:
                        output.append(
                            f"<local_traceback>{self._xml_escape(g['local_tb'])}</local_traceback>"
                        )

                    for sec_tag, sec_val in g["sections"].items():
                        output.append(
                            f"<{sec_tag}>{self._xml_escape(sec_val)}</{sec_tag}>"
                        )

                    tests_xml = ["<tests>"]
                    prefix = g["file"] + "::"
                    for t in g["tests"]:
                        nodeid = t["nodeid"]
                        if nodeid.startswith(prefix):
                            nodeid = nodeid[len(prefix) :]
                        esc_nodeid = self._xml_escape(nodeid)
                        esc_phase = self._xml_escape(t["phase"])

                        captures = []
                        if t.get("captured_stdout"):
                            captures.append(
                                f"<captured_stdout>{self._xml_escape(t['captured_stdout'])}</captured_stdout>"
                            )
                        if t.get("captured_stderr"):
                            captures.append(
                                f"<captured_stderr>{self._xml_escape(t['captured_stderr'])}</captured_stderr>"
                            )
                        if t.get("captured_log"):
                            captures.append(
                                f"<captured_log>{self._xml_escape(t['captured_log'])}</captured_log>"
                            )

                        if captures:
                            tests_xml.append(
                                f'<test name="{esc_nodeid}" phase="{esc_phase}">'
                                + "".join(captures)
                                + "</test>"
                            )
                        else:
                            tests_xml.append(
                                f'<test name="{esc_nodeid}" phase="{esc_phase}"/>'
                            )
                    tests_xml.append("</tests>")
                    output.append("".join(tests_xml))

                    output.append("</failure_group>")
        else:
            failed_reports = self.stats.get("failed", []) + self.stats.get("error", [])
            if failed_reports:
                groups = {}
                for report in failed_reports:
                    path = getattr(report, "fspath", "unknown_path")
                    lineno = 0
                    message = ""

                    if (
                        hasattr(report.longrepr, "reprcrash")
                        and report.longrepr.reprcrash is not None
                    ):
                        crash = report.longrepr.reprcrash
                        path = crash.path
                        lineno = crash.lineno
                        message = crash.message
                    elif report.longrepr:
                        message = str(report.longrepr)

                    if root_dir and os.path.isabs(path):
                        try:
                            path = os.path.relpath(path, start=root_dir)
                        except ValueError:
                            pass

                    # Extract exception type
                    exc_type = "Exception"
                    for line in message.splitlines():
                        line_str = line.strip()
                        if line_str.startswith("E   ") and ":" in line_str:
                            parts = line_str[4:].split(":", 1)
                            first_part = parts[0].strip()
                            if first_part.isidentifier() or all(
                                p.isidentifier() for p in first_part.split(".")
                            ):
                                exc_type = first_part
                                break
                        elif line_str.startswith("E ") and ":" in line_str:
                            parts = line_str[2:].split(":", 1)
                            first_part = parts[0].strip()
                            if first_part.isidentifier() or all(
                                p.isidentifier() for p in first_part.split(".")
                            ):
                                exc_type = first_part
                                break
                    if exc_type == "Exception" and ":" in message:
                        first_line = message.split("\n", 1)[0]
                        if ":" in first_line:
                            first_part = first_line.split(":", 1)[0].strip()
                            if first_part.isidentifier() or all(
                                p.isidentifier() for p in first_part.split(".")
                            ):
                                exc_type = first_part

                    sections_dict = {}
                    sections = getattr(report, "sections", [])
                    for section_name, section_content in sections:
                        tag_name = section_name.lower().replace(" ", "_")
                        if "stdout" in tag_name:
                            sections_dict["captured_stdout"] = section_content.strip()
                        elif "stderr" in tag_name:
                            sections_dict["captured_stderr"] = section_content.strip()
                        elif "log" in tag_name:
                            sections_dict["captured_log"] = section_content.strip()

                    local_tb = self._extract_local_traceback(report, root_dir)

                    # Normalize the raw message first (before truncation)
                    normalized_msg = self._normalize_message(message)
                    key = (exc_type, normalized_msg)

                    # Compress huge message for display
                    compressed_msg = self._compress_message(
                        message, nodeid=report.nodeid, phase=report.when
                    )

                    if key not in groups:
                        groups[key] = {
                            "exc_type": exc_type,
                            "message": compressed_msg,
                            "file": path,
                            "line": lineno,
                            "local_tb": local_tb,
                            "sections": sections_dict,
                            "tests": [],
                        }

                    groups[key]["tests"].append(
                        {
                            "nodeid": report.nodeid,
                            "phase": report.when,
                            "captured_stdout": sections_dict.get("captured_stdout"),
                            "captured_stderr": sections_dict.get("captured_stderr"),
                            "captured_log": sections_dict.get("captured_log"),
                        }
                    )

                for key, g in groups.items():
                    exc_type_esc = self._xml_escape(g["exc_type"])
                    file_path_esc = self._xml_escape(g["file"])
                    line_no_esc = self._xml_escape(g["line"])
                    msg_content_esc = self._xml_escape(g["message"])

                    output.append(
                        f'<failure_group exception="{exc_type_esc}" file="{file_path_esc}" line="{line_no_esc}">'
                    )
                    output.append(f"<message>{msg_content_esc}</message>")

                    if len(g["tests"]) == 1:
                        rerun_cmd = f"pytest {g['tests'][0]['nodeid']} -q"
                    else:
                        rerun_cmd = f"pytest {g['file']} -q"
                    output.append(f"<rerun>{self._xml_escape(rerun_cmd)}</rerun>")

                    hint = self._get_correction_hint(
                        g["exc_type"], g["message"], root_dir
                    )
                    if hint:
                        output.append(f"<hint>{self._xml_escape(hint)}</hint>")

                    if g["local_tb"]:
                        output.append(
                            f"<local_traceback>{self._xml_escape(g['local_tb'])}</local_traceback>"
                        )

                    for sec_tag, sec_val in g["sections"].items():
                        output.append(
                            f"<{sec_tag}>{self._xml_escape(sec_val)}</{sec_tag}>"
                        )

                    tests_xml = ["<tests>"]
                    prefix = g["file"] + "::"
                    for t in g["tests"]:
                        nodeid = t["nodeid"]
                        if nodeid.startswith(prefix):
                            nodeid = nodeid[len(prefix) :]
                        esc_nodeid = self._xml_escape(nodeid)
                        esc_phase = self._xml_escape(t["phase"])

                        captures = []
                        if t.get("captured_stdout"):
                            captures.append(
                                f"<captured_stdout>{self._xml_escape(t['captured_stdout'])}</captured_stdout>"
                            )
                        if t.get("captured_stderr"):
                            captures.append(
                                f"<captured_stderr>{self._xml_escape(t['captured_stderr'])}</captured_stderr>"
                            )
                        if t.get("captured_log"):
                            captures.append(
                                f"<captured_log>{self._xml_escape(t['captured_log'])}</captured_log>"
                            )

                        if captures:
                            tests_xml.append(
                                f'<test name="{esc_nodeid}" phase="{esc_phase}">'
                                + "".join(captures)
                                + "</test>"
                            )
                        else:
                            tests_xml.append(
                                f'<test name="{esc_nodeid}" phase="{esc_phase}"/>'
                            )
                    tests_xml.append("</tests>")
                    output.append("".join(tests_xml))

                    output.append("</failure_group>")

        output.append(self._build_slow_tests_xml(root_dir))
        output.append(self._build_skips_xfails_xpassed_xml())
        output.append(self._build_warnings_xml())

        output.append("</test_failures>")
        return report_str + "".join([b for b in output if b]) + "\n"

    def _extract_local_traceback(self, report, root_dir):
        if (
            not hasattr(report.longrepr, "reprtraceback")
            or report.longrepr.reprtraceback is None
        ):
            return ""

        frames = []
        for entry in report.longrepr.reprtraceback.reprentries:
            if not hasattr(entry, "reprfileloc") or entry.reprfileloc is None:
                continue

            path = entry.reprfileloc.path
            lineno = entry.reprfileloc.lineno
            msg_snippet = entry.reprfileloc.message

            is_local = True
            if "site-packages" in path or "lib/python" in path:
                is_local = False
            elif os.path.isabs(path) and root_dir:
                try:
                    rel = os.path.relpath(path, start=root_dir)
                    if rel.startswith(".."):
                        is_local = False
                    else:
                        path = rel
                except ValueError:
                    is_local = False

            if is_local:
                frames.append(f"  at {path}:{lineno} -> {msg_snippet}")

        if frames:
            return "\n" + "\n".join(frames)
        return ""

    def _compress_message(self, msg, max_len=1500, nodeid=None, phase=None):
        budget_opt = self.config.getoption("--receptor-budget", None)
        if budget_opt is not None:
            try:
                max_len = int(budget_opt)
            except ValueError:
                pass

        if len(msg) <= max_len:
            return msg

        import hashlib

        msg_hash = hashlib.md5(msg.encode("utf-8", errors="ignore")).hexdigest()

        # Calculate split sizes
        head_len = int(max_len * 0.65)
        tail_len = int(max_len * 0.3)

        ref_info = ""
        if nodeid and phase:
            collector = getattr(self.config, "_receptor_collector", None)
            art_path = (
                collector.artifact_path
                if (collector and collector.artifact_path)
                else ".pytest-receptor.jsonl"
            )
            art_name = os.path.basename(art_path)
            ref_info = f", full evidence: {art_name} for nodeid={nodeid} phase={phase}"

        notice = f"\n... [truncated: original_size={len(msg)} bytes, md5={msg_hash}{ref_info}] ...\n"
        return msg[:head_len] + notice + msg[-tail_len:]

    def _normalize_message(self, msg):
        # 1. Normalize Hex Addresses (e.g. 0x7f83ad910)
        msg = re.sub(r"0x[0-9a-fA-F]+", "[HEX_ADDR]", msg)
        # 2. Normalize Dynamic Timestamps (e.g. 2026-07-17 09:15:47.123)
        msg = re.sub(
            r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?", "[DATETIME]", msg
        )
        return msg

    def _get_package_manager_command(self, root_dir):
        if not root_dir:
            return "pip install"
        if os.path.exists(os.path.join(root_dir, "poetry.lock")):
            return "poetry add"
        if os.path.exists(os.path.join(root_dir, "uv.lock")):
            return "uv pip install"
        if os.path.exists(os.path.join(root_dir, "pdm.lock")):
            return "pdm add"
        if os.path.exists(os.path.join(root_dir, "Pipfile.lock")) or os.path.exists(
            os.path.join(root_dir, "Pipfile")
        ):
            return "pipenv install"
        return "pip install"

    def _get_correction_hint(self, exc_type, message, root_dir):
        msg_lower = message.lower()
        if exc_type == "ModuleNotFoundError" or "modulenotfounderror" in msg_lower:
            m = re.search(r"No module named ['\"]([^'\"]+)['\"]", message)
            module = m.group(1) if m else "module"
            pm_cmd = self._get_package_manager_command(root_dir)
            return f"{pm_cmd} {module}"
        elif (
            exc_type == "ConnectionRefusedError"
            or "connection refused" in msg_lower
            or "operationalerror" in msg_lower
        ):
            return "Check if the database server or external API service is running on the expected port."
        elif exc_type == "PermissionError" or "permission denied" in msg_lower:
            return "Check file read/write permissions on the target path."
        elif (
            exc_type == "FileNotFoundError" or "no such file or directory" in msg_lower
        ):
            return "Check if the target file path exists and is spelled correctly."
        return None


class CiTerminalReporter(TerminalReporter):
    def __init__(self, config, file=None):
        super().__init__(config, file)
        # Disable colors for CI output
        self.config.option.color = "no"
        self._original_tw = self._tw
        self._tw = DummyTerminalWriter(self._tw, config)
        self._ci_start_time = time.monotonic()
        self._last_heartbeat_time = time.monotonic()
        self._test_durations = {}

        self._current_test = None
        self._current_test_start = None
        self._stop_watchdog = threading.Event()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop, daemon=True
        )
        self._watchdog_thread.start()

    def pytest_runtest_setup(self, item):
        self._current_test = item.nodeid
        self._current_test_start = time.monotonic()

    def pytest_runtest_teardown(self, item, nextitem):
        self._current_test = None
        self._current_test_start = None

    def _watchdog_loop(self):
        while not self._stop_watchdog.wait(10.0):
            if self._stop_watchdog.is_set():
                break
            current = self._current_test
            start = self._current_test_start
            if current and start:
                elapsed = time.monotonic() - start
                if elapsed >= 30.0:
                    self._original_tw.line(
                        f"CI WARNING: Test '{current}' has been running for {elapsed:.1f}s (possible hang)."
                    )

    def pytest_runtest_logreport(self, report):
        super().pytest_runtest_logreport(report)
        nodeid = report.nodeid
        self._test_durations[nodeid] = (
            self._test_durations.get(nodeid, 0.0) + report.duration
        )
        self._report_ci_progress()

    def _report_ci_progress(self):
        now = time.monotonic()
        if now - self._last_heartbeat_time >= 5.0:
            completed = (
                len(self.stats.get("passed", []))
                + len(self.stats.get("failed", []))
                + len(self.stats.get("skipped", []))
                + len(self.stats.get("error", []))
                + len(self.stats.get("xfailed", []))
                + len(self.stats.get("xpassed", []))
            )
            if self._numtests:
                percent = (completed * 100) // self._numtests
                elapsed = now - self._ci_start_time
                self._original_tw.line(
                    f"CI Progress: {percent}% (after {elapsed:.1f}s)"
                )
                self._last_heartbeat_time = now

    @pytest.hookimpl(wrapper=True)
    def pytest_sessionfinish(self, session, exitstatus):
        # The base class runs and writes its summary to DummyTerminalWriter (quietly)
        result = yield

        # Print our clean, flat CI output to the original terminal writer
        failed_reports = self.stats.get("failed", []) + self.stats.get("error", [])
        if failed_reports or exitstatus != 0:
            self._original_tw.line("")  # Start on a new line
            self._original_tw.line(
                "=================================== FAILURES ==================================="
            )
            # Swap self._tw back to original temporarily to call standard summary
            self._tw = self._original_tw
            self.summary_failures()
            self.summary_errors()
            # Restore DummyTerminalWriter
            self._tw = DummyTerminalWriter(self._original_tw, self.config)

        # Print our simple final CI summary line
        collector = getattr(self.config, "_receptor_collector", None)
        if collector:
            logical_tests = {}
            for phase_event in collector.test_phases:
                nid = phase_event.nodeid
                if nid not in logical_tests:
                    logical_tests[nid] = []
                logical_tests[nid].append(phase_event)

            passed_count = 0
            failed_count = 0
            skipped_count = 0
            xfailed_count = 0
            xpassed_count = 0
            error_count = 0

            for nid, phases in logical_tests.items():
                outcomes = [p.outcome for p in phases]
                if "failed" in outcomes:
                    failed_phase = next(p for p in phases if p.outcome == "failed")
                    if failed_phase.phase in ("setup", "teardown"):
                        error_count += 1
                    else:
                        failed_count += 1
                elif "error" in outcomes:
                    error_count += 1
                elif "xpassed" in outcomes:
                    xpassed_count += 1
                elif "xfailed" in outcomes:
                    xfailed_count += 1
                elif "skipped" in outcomes:
                    skipped_count += 1
                elif "passed" in outcomes:
                    passed_count += 1
        else:
            passed_count = len(self.stats.get("passed", []))
            skipped_count = len(self.stats.get("skipped", []))
            xfailed_count = len(self.stats.get("xfailed", []))
            xpassed_count = len(self.stats.get("xpassed", []))
            failed_count = len(self.stats.get("failed", []))
            error_count = len(self.stats.get("error", []))

        parts = []
        if failed_count > 0:
            parts.append(f"{failed_count} failed")
        if error_count > 0:
            parts.append(f"{error_count} error")
        if passed_count > 0:
            parts.append(f"{passed_count} passed")
        if skipped_count > 0:
            parts.append(f"{skipped_count} skipped")
        if xfailed_count > 0:
            parts.append(f"{xfailed_count} xfailed")
        if xpassed_count > 0:
            parts.append(f"{xpassed_count} xpassed")

        if exitstatus != 0 and failed_count == 0 and error_count == 0:
            parts.insert(0, f"FAILED (exitcode={int(exitstatus)})")

        if not parts:
            parts.append("0 passed")

        duration = time.monotonic() - self._ci_start_time
        status_str = ", ".join(parts)

        self._original_tw.line("")
        self._original_tw.line(f"CI: {status_str} in {duration:.2f}s")

        # Report slowest tests (>0.5s)
        slow_tests = sorted(
            [
                (nodeid, dur)
                for nodeid, dur in self._test_durations.items()
                if dur >= 0.5
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:3]
        if slow_tests:
            self._original_tw.line("")
            self._original_tw.line("Slowest tests (>0.5s):")
            for nodeid, dur in slow_tests:
                root_dir = getattr(
                    self.config, "rootpath", getattr(self.config, "rootdir", None)
                )
                short_nodeid = nodeid
                if root_dir and os.path.isabs(nodeid.split("::")[0]):
                    try:
                        parts_nid = nodeid.split("::", 1)
                        rel_path = os.path.relpath(parts_nid[0], start=root_dir)
                        short_nodeid = rel_path + "::" + parts_nid[1]
                    except ValueError:
                        pass
                self._original_tw.line(f"- {short_nodeid} ({dur:.2f}s)")

        if hasattr(self, "_stop_watchdog"):
            self._stop_watchdog.set()
            if hasattr(self, "_watchdog_thread"):
                self._watchdog_thread.join(timeout=1.0)

        return result
