# ElastNetMT reporting protocol

ElastNetMT implements the issue-backed lifecycle in
`uibcdf/molsyssuite`'s `devguide/reporting_protocol.md`. The suite protocol
defines identity, statuses, closure evidence and bounded exceptions.

Open `uibcdf/elastnetmt#<number>` before adding a queued report. Copy
`devguide/templates/report.md`, remove `severity` for a proposal, and put
analysis and evidence in the report. The issue holds public state and settled
facts. Suite-wide policy belongs to `uibcdf/molsyssuite`.

- `devguide/pending_bugs/` contains open defects;
- `devguide/pending_proposals/` contains open proposals;
- `devguide/archive/` permanently retains resolved, withdrawn and superseded
  reports.

Plans and design notes elsewhere in `devguide/` remain outside these queues
until they describe independently closable, issue-backed themes.

To close a report, set its closed status and date, cite a relevant durable
`guard` or `normative` document, move it to the archive and regenerate the
indexes. Close the issue with the result, evidence and archive path. Preserve
the original text of archived claims; append a dated correction if needed.

The default guard is a pytest selector under `tests/` or `devtools/tests/`.
The offline validator verifies that the selected function, class method or
module contains a statically declared test. A reviewer must also confirm that
the selected assertion protects the reported mechanism. No arbitrary command
text is accepted in `guard`.

Run these offline checks after changing a report:

```bash
python devtools/devguide_index.py
python devtools/devguide_index.py --check
python -m unittest discover -s tests -p test_reporting_protocol.py
```

The independent governance CI job runs the index check and reporting tests
without installing scientific dependencies.
