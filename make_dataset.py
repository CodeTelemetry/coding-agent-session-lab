"""Deterministic invented teaching data; never a reconstruction of Fable."""
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    rows = [
        (0, 'read', 'example.py', 'source-v1', '', 120, 1),
        (10, 'edit', 'example.py', 'source-v2', '', 800, 4),
        (20, 'test', 'python -m unittest test_fast', '5 tests OK', 0, 400, 2),
        (30, 'pr_check', 'gh pr checks 42', 'pending', 8, 300, 1),
        (60, 'pr_check', 'gh pr checks 42', 'pending', 8, 300, 1),
        (90, 'pr_check', 'gh pr checks 42', 'pending', 8, 300, 1),
        (120, 'pr_check', 'gh pr checks 42', 'pending', 8, 300, 1),
        (150, 'pr_check', 'gh pr checks 42', 'pass', 0, 300, 1),
        (160, 'test', 'python -m unittest test_example', '9 tests OK', 0, 600, 2),
        (170, 'test', 'python -m unittest test_example', 'missing result', '', 200, ''),
    ]
    fields = ['session_id', 'event_id', 'started_at', 'tool', 'command',
              'result', 'exit_code', 'tokens', 'duration_s', 'provenance']
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with (ROOT / 'data/events_synthetic.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for i, (seconds, tool, command, result, code, tokens, duration) in enumerate(rows):
            writer.writerow(dict(zip(fields, ['synthetic-demo', f'e{i+1:02}',
                (start + timedelta(seconds=seconds)).isoformat(), tool, command,
                result, code, tokens, duration, 'synthetic'])))

if __name__ == '__main__':
    main()
