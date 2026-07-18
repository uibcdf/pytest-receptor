# MolSysMT Warning-Group Evidence

## Run

- pytest-receptor commit: `11b3785`
- command: `python -m pytest --receptor=llm -n 12`
- result: 9,336 passed, 2 skipped, 216 warnings in 60 groups
- source: MolSysMT's generated full report at
  `.pytest_cache/d/receptor/last-run.txt`

## Untruncated warning section

```text
warnings: 216 in 60 groups
  UnknownAtomNameWarning x50 | ../argdigest/argdigest/core/decorator.py:376 | Atom name 'Atom name 'Ar' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.
  GpuNotAvailableWarning x18 | ../argdigest/argdigest/core/decorator.py:376 | GPU acceleration was requested but is not available: GPU acceleration was requested but is not available: no CUDA GPU is accessible The calculation falls back to the CPU kernel and the result is unchanged. Set molsysmt.configure.gpu_mode = False to stop requesting the GPU. Docs: https://www.uibcdf.org/MolSysMT The calculation falls back to the CPU kernel and the result is unchanged. Set molsysmt.configure.gpu_mode = False to stop requesting the GPU. Docs: https://www.uibcdf.org/MolSysMT
  UnitStrippedWarning x10 | molsysmt/basic/compare.py:255 | The unit of the quantity is stripped when downcasting to ndarray.
  UserWarning x7 | formats/pdb/pdbfile.py:214 | Unlikely unit cell vectors detected in PDB file likely resulting from a dummy CRYST1 record. Discarding unit cell vectors.
  UserWarning x5 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_index': (1441,) vs (605,). Returning False.
  UserWarning x5 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'component_index': (141,) vs (1,). Returning False.
  UserWarning x5 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'component_type': (141,) vs (1,). Returning False.
  UserWarning x5 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'molecule_index': (141,) vs (1,). Returning False.
  UserWarning x5 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'molecule_type': (141,) vs (1,). Returning False.
  UserWarning x5 | molsysmt/basic/compare.py:542 | Shape mismatch for 'coordinates': (1, 1441, 3) vs (1, 605, 3). Returning False.
  UnknownAtomNameWarning x4 | ../argdigest/argdigest/core/decorator.py:376 | Atom name 'Atom name 'XX' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.
  UserWarning x4 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'chain_index': (6,) vs (1,). Returning False.
  UserWarning x4 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'chain_id': (6,) vs (1,). Returning False.
  UserWarning x4 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'chain_name': (6,) vs (1,). Returning False.
  UserWarning x4 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'chain_type': (6,) vs (1,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_id': (1441,) vs (605,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_name': (1441,) vs (605,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_type': (1441,) vs (605,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_index': (302,) vs (38,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_id': (302,) vs (38,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_name': (302,) vs (38,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_type': (302,) vs (38,). Returning False.
  UserWarning x3 | molsysmt/basic/compare.py:452 | Size mismatch for attribute 'bonded_atom_pairs': 1322 vs 611. Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:261 | Size mismatch for attribute 'inner_bond_index': 1441 vs 605. Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'component_id': (141,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'component_name': (141,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'molecule_id': (141,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'molecule_name': (141,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'entity_index': (5,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'entity_id': (5,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'entity_name': (5,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'entity_type': (5,) vs (1,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'bond_index': (1322,) vs (611,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_index': (1441,) vs (1289,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_id': (1441,) vs (1289,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_name': (1441,) vs (1289,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'atom_type': (1441,) vs (1289,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_index': (302,) vs (162,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_id': (302,) vs (162,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_name': (302,) vs (162,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'group_type': (302,) vs (162,). Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:452 | Size mismatch for attribute 'bonded_atom_pairs': 1322 vs 1309. Returning False.
  UserWarning x2 | molsysmt/basic/compare.py:512 | Size mismatch for attribute 'inner_bonded_atom_pairs': 1322 vs 611. Returning False.
  MemoryPressureWarning x1 | molsysmt/_private/execution/chunked_executor.py:329 | molsysmt._private.smonitor.warnings.MemoryPressureWarning: RAM usage (1195278336 bytes) has exceeded 119528% of the configured budget (1000000 bytes) at chunk 0. Consider reducing chunk_size, freeing memory, or increasing molsysmt.configure.max_ram_usage.
  UnknownAtomNameWarning x1 | ../argdigest/argdigest/core/decorator.py:376 | Atom name 'Atom name 'X' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.
  UnknownAtomNameWarning x1 | ../argdigest/argdigest/core/decorator.py:376 | Atom name 'Atom name 'Na' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.' is not recognized; atom type 'UNK' will be used. Provide an explicit atom type when the name uses a non-standard convention.
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1282 | Found no information for attr: 'altLocs' Using default value of ' '
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1282 | Found no information for attr: 'icodes' Using default value of ' '
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1282 | Found no information for attr: 'chainIDs' Using default value of ''
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1282 | Found no information for attr: 'occupancies' Using default value of '1.0'
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1282 | Found no information for attr: 'tempfactors' Using default value of '0.0'
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1282 | Found no information for attr: 'elements' Using default value of ' '
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1282 | Found no information for attr: 'record_types' Using default value of 'ATOM'
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:1336 | Found missing chainIDs. Corresponding atoms will use value of 'X'
  UserWarning x1 | MDAnalysis/coordinates/PDB.py:885 | Unit cell dimensions not found. CRYST1 record set to unitary values.
  UserWarning x1 | MDAnalysis/core/universe.py:272 | No coordinate reader found for <Topology; 1 chains, 7 residues, 62 atoms, 61 bonds>. Skipping this file.
  UserWarning x1 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'chain_index': (2,) vs (1,). Returning False.
  UserWarning x1 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'chain_id': (2,) vs (1,). Returning False.
  UserWarning x1 | molsysmt/basic/compare.py:270 | Size mismatch for attribute 'chain_type': (2,) vs (1,). Returning False.
  UserWarning x1 | molsysmt/basic/compare.py:542 | Shape mismatch for 'coordinates': (1, 1441, 3) vs (1, 1289, 3). Returning False.
```

## Stdout truncation assessment

The new bounded warning lines worked as intended in this run: all 60 groups
were present in stdout, long messages were shortened, and the disk report
retained their full text. Category, count, and location remained sufficient to
recognize the long warning groups in this sample.

The full text also exposes repeated wording inside the
`UnknownAtomNameWarning` and `GpuNotAvailableWarning` messages themselves.
That repetition appears in the warning payload received by receptor and is
therefore separate from stdout truncation and grouping. Its source should be
established before receptor attempts to normalize it away.

## Observed variant families

The 60 groups are not 60 independent warning templates. Grouping by category
and origin yields 14 structural families:

| Groups | Category and origin | Assessment |
| ---: | --- | --- |
| 36 | `UserWarning`, `molsysmt/basic/compare.py:270` | One size-mismatch template varying by attribute and shapes |
| 7 | `UserWarning`, `MDAnalysis/coordinates/PDB.py:1282` | One missing-attribute template varying by attribute and default |
| 4 | `UnknownAtomNameWarning`, `argdigest/core/decorator.py:376` | One warning varying by atom name (`Ar`, `XX`, `X`, `Na`) |
| 2 | `UserWarning`, `molsysmt/basic/compare.py:452` | One template varying only by compared sizes |
| 2 | `UserWarning`, `molsysmt/basic/compare.py:542` | One coordinate-shape template varying only by shapes |
| 1 each | nine remaining category/origin pairs | Distinct in this run |

A category-plus-origin key would reduce this sample from 60 to 14 groups, but
it is not recommended as a universal rule. Decorator locations and generic
warning sites can emit unrelated concepts. Moreover, sharing a template does
not automatically make two warnings scientifically interchangeable: the atom
name or mismatched attribute can be the information needed to diagnose the
case. The evidence supports conservative message-template normalization with
an explicit decision about which variable fields remain diagnostically
significant.

## Candidate evidence-based normalizers

1. Consider normalizing the atom token inside the exact
   `Atom name ... is not recognized` template. This merges four groups without
   merging `GpuNotAvailableWarning`, even though both share the decorator line.
   The trade-off is that `Ar`, `XX`, `X`, and `Na` may identify different data
   defects, so the full variant set must remain recoverable without opening a
   second artifact.
2. Normalize scalar and shape values inside the exact
   `Size mismatch for attribute ... Returning False` template. Treat the
   attribute name separately: retaining it creates one group per affected
   attribute, while normalizing it collapses 36 groups to one but hides which
   parts of the molecular-system contract disagreed.
3. Normalize the two shapes inside the exact
   `Shape mismatch for 'coordinates' ... Returning False` template.
4. Normalize numeric sizes inside the exact `bonded_atom_pairs` and
   `inner_bond_index` size-mismatch templates.
5. Normalize default values inside MDAnalysis's exact
   `Found no information for attr ... Using default value ...` template.
   Normalizing the attribute name as well is a stronger policy choice because
   missing `elements` and missing `occupancies`, for example, have different
   scientific consequences.
6. Normalize byte counts, percentages, configured budget, and chunk index in
   `MemoryPressureWarning`; only one instance appears here, so this is sensible
   future-proofing rather than evidence of current fragmentation.

The first five rules are directly motivated by repeated variants in this run,
but only shape and numeric-value normalization is clearly low-risk. Rules that
erase atom or attribute identity should be tested both against counterexamples
and against the information needed to fix the affected tests. A compact report
must not save tokens by removing the discriminant that explains the problem.
