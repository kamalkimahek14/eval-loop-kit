"""Self-improvement loop with blind held-out evaluation.

Each round, one change is scored by two panels with the same weighted rubric:
  - a training panel (the same judges every round; its notes may guide the next change),
  - a blind held-out panel (fresh judges every round; scores only, nobody reads its notes).
The loop reports the train-minus-blind gap, flags overfitting (training up, blind flat or down) and stops
when the blind panel has not gained more than the noise band for N rounds in a row.
"""
import json
import statistics as st
from pathlib import Path


def load_rubric(path):
    rubric = json.loads(Path(path).read_text(encoding="utf-8"))
    total = sum(c["weight"] for c in rubric["criteria"])
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"rubric weights must sum to 1, got {total}")
    return rubric


def weighted(scores, rubric):
    """One judge's weighted total from {criterion: 0-100}."""
    out = 0.0
    for c in rubric["criteria"]:
        v = scores.get(c["name"])
        if not isinstance(v, (int, float)) or not 0 <= v <= 100:
            raise ValueError(f"criterion {c['name']!r} needs a score from 0 to 100, got {v!r}")
        out += c["weight"] * v
    return out


def panel_score(panel, rubric):
    if not panel:
        raise ValueError("empty panel")
    return st.mean(weighted(j["scores"], rubric) for j in panel)


def check_fresh(rounds):
    """Blind judges must be new every round: never seen on an earlier blind panel or on any training panel."""
    train_judges = {j["judge"] for r in rounds for j in r["train"]}
    seen = set()
    for r in rounds:
        ids = [j["judge"] for j in r["blind"]]
        reused = (set(ids) & seen) | (set(ids) & train_judges)
        if reused or len(ids) != len(set(ids)):
            raise ValueError(f"round {r['round']}: blind panel is not fresh (reused: {sorted(reused) or 'duplicate id'})")
        seen |= set(ids)


def analyze(rounds, rubric, stall_n=3, noise=1.0, gain=1.0):
    """Rows per round plus the round where the stall rule stopped the loop (None if it never did).

    overfit: training rose by at least `gain` while the blind panel moved less than `noise` (flat or down).
    stall:   the blind score has not beaten its best so far by more than `noise` for `stall_n` rounds.
    """
    check_fresh(rounds)
    rows, prev, best, since, stop = [], None, None, 0, None
    for r in sorted(rounds, key=lambda r: r["round"]):
        tr, bl = panel_score(r["train"], rubric), panel_score(r["blind"], rubric)
        row = {"round": r["round"], "change": r.get("change", ""), "train": round(tr, 1), "blind": round(bl, 1),
               "gap": round(tr - bl, 1), "d_train": None, "d_blind": None, "flags": []}
        if prev:
            row["d_train"], row["d_blind"] = round(tr - prev[0], 1), round(bl - prev[1], 1)
            if tr - prev[0] >= gain and bl - prev[1] < noise:
                row["flags"].append("overfit")
        if best is None or bl > best + noise:
            best, since = bl, 0
        else:
            since += 1
            if since >= stall_n and stop is None:
                row["flags"].append(f"stall: no blind gain for {stall_n} rounds, stop")
                stop = r["round"]
        rows.append(row)
        prev = (tr, bl)
    return rows, stop


def table(rows):
    f = lambda v: "" if v is None else f"{v:+.1f}"
    out = ["| Round | Change | Train | Blind | Gap | Δ train | Δ blind | Flags |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['round']} | {r['change']} | {r['train']:.1f} | {r['blind']:.1f} | {r['gap']:.1f} | "
                   f"{f(r['d_train'])} | {f(r['d_blind'])} | {', '.join(r['flags'])} |")
    return "\n".join(out) + "\n"
