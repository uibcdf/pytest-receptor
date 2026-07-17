import pytest


@pytest.hookspec(firstresult=True)
def pytest_receptor_extension_event(
    namespace: str, kind: str, payload: dict, relationships: dict = None
):
    """Hook to log custom namespaced extension events to the receptor event stream.

    :param namespace: The unique namespace of the producer (e.g.
        "org.uibcdf.smonitor")
    :param kind: The kind/type of event (e.g. "diagnostic")
    :param payload: The custom JSON-serializable dictionary containing the event
        data
    :param relationships: Optional dictionary correlating this event to specific
        contexts (e.g. {"nodeid": "...", "phase": "..."})
    """
