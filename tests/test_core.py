"""Run: python -m unittest discover -s tests"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from evalloop.core import analyze, check_fresh, load_rubric, table, weighted
from evalloop.__main__ import main

EX = Path(__file__).resolve().parent.parent / "examples"
RUBRIC = load_rubric(EX / "rubric.json")
ROUNDS = json.loads((EX / "rounds.json").read_text(encoding="utf-8"))["rounds"]


def rnd(n, train, blind):
    s = lambda v: {"clarity": v, "evidence": v, "relevance": v, "tone": v}
    return {"round": n, "train": [{"judge": "T1", "scores": s(train)}], "blind": [{"judge": f"B{n}", "scores": s(blind)}]}


class Core(unittest.TestCase):
    def test_weighted_total(self):
        self.assertAlmostEqual(weighted({"clarity": 100, "evidence": 0, "relevance": 0, "tone": 0}, RUBRIC), 30.0)
        with self.assertRaises(ValueError):
            weighted({"clarity": 100}, RUBRIC)

    def test_weights_must_sum_to_one(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "r.json"
            f.write_text(json.dumps({"criteria": [{"name": "a", "weight": 0.5}, {"name": "b", "weight": 0.4}]}))
            with self.assertRaisesRegex(ValueError, "sum to 1"):
                load_rubric(f)

    def test_example_rounds(self):
        rows, stop = analyze(ROUNDS, RUBRIC)
        self.assertEqual([r["round"] for r in rows if "overfit" in r["flags"]], [3, 4])
        self.assertEqual(stop, 8)
        self.assertEqual(rows[4]["gap"], 8.0)
        self.assertEqual(max(rows, key=lambda r: r["blind"])["round"], 5)

    def test_overfit_needs_train_up_and_blind_flat(self):
        rows, _ = analyze([rnd(0, 70, 70), rnd(1, 75, 70), rnd(2, 80, 78), rnd(3, 80, 70)], RUBRIC)
        self.assertEqual([bool(r["flags"]) for r in rows], [False, True, False, False])

    def test_stall_rule(self):
        rows, stop = analyze([rnd(0, 70, 70), rnd(1, 71, 70.5), rnd(2, 70, 70), rnd(3, 70, 71)], RUBRIC, stall_n=3)
        self.assertEqual(stop, 3)
        _, stop = analyze([rnd(0, 70, 70), rnd(1, 70, 72), rnd(2, 70, 74)], RUBRIC, stall_n=1)
        self.assertIsNone(stop)

    def test_blind_panel_must_be_fresh(self):
        bad = copy.deepcopy(ROUNDS)
        bad[2]["blind"][0]["judge"] = bad[1]["blind"][0]["judge"]
        with self.assertRaisesRegex(ValueError, "not fresh"):
            check_fresh(bad)
        bad = copy.deepcopy(ROUNDS)
        bad[0]["blind"][0]["judge"] = "T1"
        with self.assertRaisesRegex(ValueError, "not fresh"):
            check_fresh(bad)

    def test_table_and_cli(self):
        rows, _ = analyze(ROUNDS, RUBRIC)
        md = table(rows)
        self.assertEqual(len(md.strip().splitlines()), 2 + len(ROUNDS))
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "t.md"
            main([str(EX / "rubric.json"), str(EX / "rounds.json"), "--out", str(out)])
            self.assertEqual(out.read_text(encoding="utf-8"), md)


if __name__ == "__main__":
    unittest.main()
