from pathlib import Path
import unittest

import pandas as pd
from analyze import investigate

ROOT = Path(__file__).resolve().parent

class AnalysisChecks(unittest.TestCase):
    def setUp(self):
        self.frame = pd.read_csv(ROOT/'data/events_synthetic.csv')

    def test_known_totals_intervals_and_repeats(self):
        df, polls = investigate(self.frame.sample(frac=1, random_state=42))
        self.assertEqual(len(df), 10)
        self.assertEqual(df.cumulative_tokens.tolist(),
                         [120, 920, 1320, 1620, 1920, 2220, 2520, 2820, 3420, 3620])
        self.assertTrue(pd.isna(polls.check_gap_s.iloc[0]))
        self.assertEqual(polls.check_gap_s.dropna().tolist(), [30]*4)
        self.assertEqual(polls.repeat_index.tolist(), [0, 1, 2, 3, 4])
        self.assertEqual(polls.same_result_as_previous.tolist(), [False, True, True, True, False])
        self.assertEqual(int(df.repeat_index.gt(0).sum()), 5)
        self.assertEqual(int(polls.tokens.sum()), 1500)
        self.assertEqual(df.tool_gap_s.dropna().tolist(), [10,10,10,30,30,30,30,10,10])

    def test_sessions_do_not_share_intervals_or_consumption(self):
        second = self.frame.assign(session_id='second')
        df, polls = investigate(pd.concat([self.frame, second], ignore_index=True))
        self.assertEqual(df.groupby('session_id').cumulative_tokens.last().tolist(), [3620,3620])
        self.assertEqual(polls.groupby('session_id').check_gap_s.count().tolist(), [4,4])
        self.assertEqual(int(df.tool_gap_s.isna().sum()), 2)
        self.assertEqual(int(df.repeat_index.gt(0).sum()), 10)

    def test_invalid_inputs_are_rejected(self):
        cases = [pd.concat([self.frame, self.frame.iloc[[0]]]),
                 self.frame.assign(tokens=-1), self.frame.assign(tokens=float('nan')),
                 self.frame.assign(tokens=1.5), self.frame.assign(tokens=float('inf')),
                 self.frame.assign(started_at='bad'), self.frame.assign(command=None),
                 self.frame.assign(provenance='production')]
        for frame in cases:
            with self.subTest(), self.assertRaises((ValueError, TypeError)):
                investigate(frame)

    def test_missing_results_are_never_success(self):
        df, _ = investigate(self.frame)
        tests = df[df.tool.eq('test')]
        self.assertEqual(int(tests.exit_code.eq(0).sum()), 2)
        self.assertEqual(int(tests.exit_code.isna().sum()), 1)

if __name__ == '__main__':
    unittest.main()
