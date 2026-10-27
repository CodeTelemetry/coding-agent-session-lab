"""Offline pandas investigation. No network, account or Code Telemetry required."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Works on headless machines; writes a PNG instead of opening a GUI.
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent


def investigate(frame):
    df = frame.copy()
    required = {'session_id', 'event_id', 'started_at', 'tool', 'command',
                'result', 'exit_code', 'tokens', 'duration_s', 'provenance'}
    if not required.issubset(df.columns) or df.empty:
        raise ValueError('Empty dataset or missing required columns')
    text = ['session_id', 'event_id', 'started_at', 'tool', 'command', 'result', 'provenance']
    if df[text].isna().any().any() or (df[text] == '').any().any():
        raise ValueError('Required text fields must be populated')
    if df.duplicated(['session_id', 'event_id']).any():
        raise ValueError('Duplicate event IDs within a session')
    if not df.provenance.eq('synthetic').all():
        raise ValueError('This teaching schema accepts synthetic rows only')
    df['started_at'] = pd.to_datetime(df.started_at, utc=True, errors='raise', format='ISO8601')
    for col in ['tokens', 'duration_s', 'exit_code']:
        df[col] = pd.to_numeric(df[col], errors='raise')
        values = df[col].dropna()
        if (values.abs() == float('inf')).any():
            raise ValueError(f'{col} must be finite')
    if df.tokens.isna().any() or (df.tokens < 0).any() or (df.tokens % 1 != 0).any():
        raise ValueError('tokens must be known nonnegative integer increments')
    if (df.duration_s.dropna() < 0).any() or (df.exit_code.dropna() % 1 != 0).any():
        raise ValueError('Invalid duration or exit code')
    df = df.sort_values(['session_id', 'started_at', 'event_id']).reset_index(drop=True)
    session = df.groupby('session_id', sort=False)
    df['elapsed_s'] = (df.started_at - session.started_at.transform('min')).dt.total_seconds()
    df['tool_gap_s'] = session.started_at.diff().dt.total_seconds()
    df['cumulative_tokens'] = session.tokens.cumsum()
    # Exact tool+argument identity; no fuzzy grouping or interpretation of shell strings.
    keys = ['session_id', 'tool', 'command']
    df['repeat_index'] = df.groupby(keys).cumcount()  # 0 = first occurrence
    df['same_result_as_previous'] = df.result.eq(df.groupby(keys).result.shift())
    checks = df.loc[df.tool.eq('pr_check')].copy()
    checks['check_gap_s'] = checks.groupby(keys).started_at.diff().dt.total_seconds()
    return df, checks


def plot(df, checks, destination):
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), constrained_layout=True)
    for session_id, rows in df.groupby('session_id'):
        axes[0].step(rows.elapsed_s, rows.cumulative_tokens, where='post', label=session_id)
        for tool, marker in [('pr_check', 'o'), ('test', 's')]:
            points = rows[rows.tool.eq(tool)]
            axes[0].scatter(points.elapsed_s, points.cumulative_tokens, marker=marker,
                            s=45, label=f'{session_id}: {tool}')
    axes[0].set(ylabel='Cumulative token increments', title='SYNTHETIC teaching trace - not Fable or production telemetry')
    axes[0].legend(fontsize=8, loc='upper left')
    for session_id, rows in checks.groupby('session_id'):
        axes[1].plot(rows.elapsed_s, rows.check_gap_s, 'o-', label=session_id)
    axes[1].set(ylabel='Check-in gap (seconds)', title='Start-to-start PR check intervals (first has no interval)')
    for session_id, rows in df.groupby('session_id'):
        axes[2].plot(rows.elapsed_s, rows.tool_gap_s, 'o-', label=session_id)
    axes[2].set(xlabel='Seconds since session start', ylabel='Tool gap (seconds)',
                title='Intervals between all tool-call starts')
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.set_ylim(bottom=0)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'data/events_synthetic.csv')
    parser.add_argument('--out', type=Path, default=ROOT/'output')
    args = parser.parse_args()
    df, checks = investigate(pd.read_csv(args.data))
    args.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out/'events_analyzed.csv', index=False)
    checks.to_csv(args.out/'checkins.csv', index=False)
    records = []
    for sid, rows in df.groupby('session_id'):
        polls = checks[checks.session_id.eq(sid)]
        gaps = polls.check_gap_s.dropna()
        records.append(dict(session_id=sid, calls=len(rows),
            repeated_calls=int(rows.repeat_index.gt(0).sum()),
            checkins=len(polls), repeated_checkins=int(polls.repeat_index.gt(0).sum()),
            unchanged_checkins=int(polls.same_result_as_previous.sum()),
            median_check_gap_s=None if gaps.empty else float(gaps.median()),
            total_tokens=int(rows.tokens.sum()), checkin_tokens=int(polls.tokens.sum()),
            zero_exit_tests=int((rows.tool.eq('test') & rows.exit_code.eq(0)).sum()),
            missing_test_results=int((rows.tool.eq('test') & rows.exit_code.isna()).sum())))
    report = {'synthetic_sessions': records,
              'limits': 'Repeats are exact calls, not proof of wasted work. Gaps are start-to-start, '
              'not idle time. Tokens are invented increments, not dollars or measured agent usage. '
              'An exit status supports only the tested assertions.'}
    (args.out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    plot(df, checks, args.out/'investigation.png')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
