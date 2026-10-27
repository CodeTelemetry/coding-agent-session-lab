# Commands to run and edit

For a guided Jupyter workbook, install `requirements-notebook.txt`, run
`python -m jupyter lab` from the repository root, and open
[`session_lab.ipynb`](session_lab.ipynb). Run its cells in order. The
commands below are the terminal alternative.

Use a terminal in the repo root with the virtual environment activated.
Everything here uses bundled, offline data. The polling trace and token increments
are invented.

## Look at the raw input first

The notebook prints the CSV header and its first three rows, then displays all
original columns in `raw` and the calculated columns in `df`. From a terminal,
you can also show the source directly:

```sh
head -n 4 data/events_synthetic.csv
```

This is a synthetic CSV fixture, not a raw OpenTelemetry capture.

## 1. Generate the report and chart

```sh
python -m unittest -v test_analysis
python analyze.py
```

Open `output/investigation.png` and `output/summary.json`. There are five PR
check-ins, a 30-second median check-in interval, 3,620 token increments overall,
and 1,500 attached to check-ins.

## 2. Inspect the pandas operations interactively

```sh
python -i explore.py
```

The script loads `df`, `checks` and `keys`. Paste these Python expressions at
the `>>>` prompt (they are expressions, not terminal commands):

```python
# Every occurrence after the first of an exact tool+command is a repeat.
df.loc[df.repeat_index.gt(0), ['event_id', 'command', 'repeat_index']]

# Start-to-start intervals for successive checks of the same PR command.
checks[['event_id', 'result', 'check_gap_s']]

# The operations producing these metrics (already sorted by session/time).
df.groupby(keys).cumcount()
checks.groupby(keys).started_at.diff().dt.total_seconds()
df.groupby('session_id').tokens.cumsum()

# Allocation attached to each tool category, not dollars or measured usage.
df.groupby('tool').tokens.sum()

# A repeated command can return new information.
checks[['event_id', 'repeat_index', 'result', 'same_result_as_previous']]

# A missing test exit remains unknown, never success.
df.loc[df.tool.eq('test'), ['event_id', 'command', 'result', 'exit_code']]
```

Type `exit()` to return to the terminal.

## 3. Make a visible edit

Open `make_dataset.py`. Change a **single** PR check row's token value from
`300` to `600`. Do not edit a generated CSV or add a fake production provenance.

```sh
python make_dataset.py
python analyze.py
```

The total becomes 3,920 and check-in tokens become 1,800. Open the PNG again.
The correctness tests intentionally assert the original fixture, so fixed-value
checks fail while this edit is active. Restore `600` to `300` in that row, then:

```sh
python make_dataset.py
python -m unittest -v test_analysis
python analyze.py
```

Alternatively change one `pending` result to `pass` and inspect which calls
repeat the immediately preceding result. Repeated-call identity does not change.
Restore the result before running the fixed-fixture checks.

## 4. Inspect missing results

The synthetic data includes a test call with no recorded exit code. In the
interactive session, filter the test rows and compare `result` and `exit_code`.
A missing exit code is unknown, not success.

## Files to open

* `make_dataset.py`: ten explicit synthetic rows to edit.
* `analyze.py`: pandas calculations, report and Matplotlib chart.
* `explore.py`: interactive entry point; no notebook dependency.
* `test_analysis.py`: analysis correctness checks.
