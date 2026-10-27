"""Run `python -i explore.py` to investigate the fixture interactively."""
from pathlib import Path
import pandas as pd
from analyze import investigate

ROOT = Path(__file__).resolve().parent
raw = pd.read_csv(ROOT / 'data/events_synthetic.csv')
df, checks = investigate(raw)
keys = ['session_id', 'tool', 'command']

if __name__ == '__main__':
    print('SYNTHETIC activity, not Fable. Available: raw, df, checks, keys, pd')
    print(df[['event_id', 'tool', 'tokens', 'cumulative_tokens']].to_string(index=False))
    print('\nTry: checks[["event_id", "result", "check_gap_s"]]')
