"""python -m evalloop RUBRIC ROUNDS [--stall N] [--noise X] [--gain X] [--out round-table.md]"""
import argparse
import json
import sys
from pathlib import Path

from .core import analyze, load_rubric, table


def main(argv=None):
    ap = argparse.ArgumentParser(prog="evalloop", description="Aggregate training and blind held-out panels per round.")
    ap.add_argument("rubric")
    ap.add_argument("rounds")
    ap.add_argument("--stall", type=int, default=3, help="stop after N rounds without a blind gain (default 3)")
    ap.add_argument("--noise", type=float, default=1.0, help="blind changes smaller than this are flat (default 1.0)")
    ap.add_argument("--gain", type=float, default=1.0, help="training rise that counts as 'up' (default 1.0)")
    ap.add_argument("--out", help="write the round table as Markdown to this file")
    a = ap.parse_args(argv)
    # The table uses symbols such as Δ; a Windows console defaults to a narrower code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rubric = load_rubric(a.rubric)
    rounds = json.loads(Path(a.rounds).read_text(encoding="utf-8"))["rounds"]
    rows, stop = analyze(rounds, rubric, a.stall, a.noise, a.gain)
    md = table(rows)
    print(md, end="")
    best = max(rows, key=lambda r: r["blind"])
    print(f"best blind: round {best['round']} ({best['blind']:.1f}); "
          f"overfit rounds: {[r['round'] for r in rows if 'overfit' in r['flags']]}; "
          f"stall stop: {'round ' + str(stop) if stop is not None else 'not reached'}")
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
