#!/usr/bin/env python3
"""Mac 拼音練習遊戲 — 弱點自動加強。

純英文輸入 + 字串比對。練習前請切到 ABC 英文輸入法。

判定：
  - 輸入 ∈ accepted → 對（IME 真能出字）
  - 輸入 = preferred → 對 + 效率滿分
  - 其他 → 錯

權重：
  - 錯 ×2；對但慢 ×1.5；對且快 ×0.7；未見過 +1.5 boost
"""
import argparse
import json
import random
import sqlite3
import statistics
import sys
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = Path(__file__).parent / "stats.sqlite"

BASELINE_MS = {
    "nng-char": 1500,
    "nng-word": 3000,
    "apostrophe": 3000,
}

SEED_FILES = {
    "apostrophe": "seed_apostrophe.json",
    "nng-char": "seed_nng_chars.json",
    "nng-word": "seed_nng_words.json",
}


def load_seeds(categories):
    items = []
    for cat in categories:
        path = DATA_DIR / SEED_FILES[cat]
        with open(path, encoding="utf-8") as f:
            items.extend(json.load(f))
    return items


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            hanzi TEXT NOT NULL,
            category TEXT NOT NULL,
            user_input TEXT NOT NULL,
            correct INTEGER NOT NULL,
            matched_preferred INTEGER NOT NULL,
            time_ms INTEGER NOT NULL,
            tags TEXT
        )
    """)
    conn.commit()
    return conn


def global_stats(conn, categories):
    """回傳 (total, correct) — 指定 categories 的全期累計。"""
    placeholders = ",".join("?" * len(categories))
    row = conn.execute(
        f"SELECT COUNT(*), COALESCE(SUM(correct),0) FROM attempts WHERE category IN ({placeholders})",
        categories,
    ).fetchone()
    return row[0], row[1]


def median_correct_ms(conn, category):
    rows = conn.execute(
        "SELECT time_ms FROM attempts WHERE category=? AND correct=1 ORDER BY ts DESC LIMIT 50",
        (category,),
    ).fetchall()
    if len(rows) < 5:
        return BASELINE_MS.get(category, 3000)
    return statistics.median(r[0] for r in rows)


def history_for(conn, hanzi, limit=5):
    return conn.execute(
        "SELECT correct, matched_preferred, time_ms FROM attempts WHERE hanzi=? ORDER BY ts DESC LIMIT ?",
        (hanzi, limit),
    ).fetchall()


def compute_weight(item, conn, slow_threshold_ms):
    hist = history_for(conn, item["hanzi"])
    if not hist:
        return 2.5  # 未見過，高優先
    w = 1.0
    for correct, _pref, time_ms in hist:
        if not correct:
            w *= 2.0
        elif time_ms > slow_threshold_ms:
            w *= 1.5
        else:
            w *= 0.7
    # 連續 3 次快對 → 移出熱池
    if len(hist) >= 3 and all(
        c and t <= slow_threshold_ms for c, _p, t in hist[:3]
    ):
        w *= 0.3
    return max(w, 0.1)


def weighted_pick(items, weights, excluded):
    pool = [(it, w) for it, w in zip(items, weights) if it["hanzi"] not in excluded]
    if not pool:
        return None
    total = sum(w for _, w in pool)
    r = random.uniform(0, total)
    acc = 0
    for it, w in pool:
        acc += w
        if r <= acc:
            return it
    return pool[-1][0]


def grade(item, user_input, strict=False):
    ui = user_input.strip()
    if ui == item.get("preferred"):
        return "preferred"
    if strict:
        return "wrong"
    if ui in item.get("accepted", []):
        return "accepted"
    return "wrong"


def ask(item):
    print()
    print(f"  \033[1;36m{item['hanzi']}\033[0m")
    if item["category"].startswith("nng"):
        print(f"  類別：n/ng  — 打完整拼音")
    else:
        print(f"  類別：apostrophe  — 用簡拼 + ' 最順")
    t0 = time.perf_counter()
    try:
        ui = input("  > ")
    except EOFError:
        return None, 0
    t1 = time.perf_counter()
    return ui, int((t1 - t0) * 1000)


def give_feedback(item, user_input, result, time_ms, strict=False):
    ui = user_input.strip()
    pref = item.get("preferred", "")
    if result == "preferred":
        print(f"  \033[1;32m✓ 完美\033[0m  ({time_ms} ms)")
    elif result == "accepted":
        print(f"  \033[32m✓ 對\033[0m  preferred [{pref}]  ({time_ms} ms)")
    else:
        trap = item.get("trap", [])
        if strict and ui in item.get("accepted", []):
            ctx = " (嚴格模式：IME 吃但不算)"
        elif ui in trap:
            ctx = " (典型陷阱)"
        else:
            ctx = ""
        zh = item.get("zhuyin")
        zh_part = f"  注音 {zh}" if zh else ""
        print(f"  \033[1;31m✗ 錯\033[0m  正解 [{pref}]{zh_part}{ctx}")
    if item.get("note"):
        print(f"  備註：{item['note']}")


def save_attempt(conn, item, user_input, result, time_ms):
    conn.execute(
        "INSERT INTO attempts (ts, hanzi, category, user_input, correct, matched_preferred, time_ms, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            time.time(),
            item["hanzi"],
            item["category"],
            user_input.strip(),
            1 if result != "wrong" else 0,
            1 if result == "preferred" else 0,
            time_ms,
            ",".join(item.get("tags", [])),
        ),
    )
    conn.commit()


def print_report(session_log):
    n = len(session_log)
    if n == 0:
        print("\n（無紀錄）")
        return
    correct = sum(1 for r in session_log if r["result"] != "wrong")
    preferred = sum(1 for r in session_log if r["result"] == "preferred")
    times = [r["time_ms"] for r in session_log if r["result"] != "wrong"]
    avg_ms = int(statistics.mean(times)) if times else 0

    print("\n" + "=" * 40)
    print("  本輪結果")
    print("=" * 40)
    print(f"  題數        {n}")
    print(f"  本局正確率  {correct}/{n} ({100*correct//n}%)")
    print(f"  效率命中    {preferred}/{n} ({100*preferred//n}%)")
    print(f"  平均用時    {avg_ms} ms（正確題）")

    # 按 category 分
    by_cat = {}
    for r in session_log:
        by_cat.setdefault(r["category"], []).append(r)
    if len(by_cat) > 1:
        print("\n  各類別：")
        for cat, rs in sorted(by_cat.items()):
            c = sum(1 for r in rs if r["result"] != "wrong")
            p = sum(1 for r in rs if r["result"] == "preferred")
            ts_ms = [r["time_ms"] for r in rs if r["result"] != "wrong"]
            avg = int(statistics.mean(ts_ms)) if ts_ms else 0
            print(f"    {cat:14s}  {c}/{len(rs)} 正確  {p}/{len(rs)} 效率  avg {avg}ms")

    # 最慢/最常錯
    wrongs = [r for r in session_log if r["result"] == "wrong"]
    if wrongs:
        print("\n  錯的題：")
        for r in wrongs:
            zh = r.get("zhuyin", "")
            zh_part = f"  注音 {zh}" if zh else ""
            print(f"    {r['hanzi']}  正解 [{r.get('preferred', '?')}]{zh_part}")
    slow = sorted(
        (r for r in session_log if r["result"] != "wrong"),
        key=lambda r: -r["time_ms"],
    )[:3]
    if slow:
        print("\n  最慢 3 題：")
        for r in slow:
            print(f"    {r['hanzi']}  {r['time_ms']} ms")


def print_history_summary(conn):
    total = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    if total == 0:
        print("（首次練習，無歷史資料）")
        return
    rows = conn.execute(
        "SELECT category, COUNT(*), SUM(correct), SUM(matched_preferred), AVG(time_ms) FROM attempts GROUP BY category"
    ).fetchall()
    print(f"\n  累計題數：{total}")
    for cat, n, c, p, avg in rows:
        print(f"    {cat:14s}  {n} 題  正確率 {100*c//n}%  效率 {100*p//n}%  avg {int(avg)}ms")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--category",
        choices=["apostrophe", "nng-char", "nng-word", "all"],
        default="all",
    )
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--strict", action="store_true", help="嚴格模式：只接受 preferred 形式（n/ng 要全拼、apostrophe 要用 ' 簡拼）")
    ap.add_argument("--stats", action="store_true", help="只顯示歷史統計，不練習")
    args = ap.parse_args()

    conn = init_db()

    if args.stats:
        print_history_summary(conn)
        return

    cats = [args.category] if args.category != "all" else list(SEED_FILES.keys())
    items = load_seeds(cats)
    if not items:
        print("題庫空")
        return

    print("\n  Mac 拼音練習 — pinyin-drill")
    print("  ⚠ 請先切到 ABC 英文輸入法")
    mode = "嚴格（只認 preferred）" if args.strict else "寬鬆（accept 全部）"
    print(f"  類別：{args.category}   題數：{args.count}   模式：{mode}")
    print("  （空行 Enter = 跳過退出）")
    print_history_summary(conn)

    session_log = []
    excluded = set()
    for i in range(args.count):
        # rebuild weights each round — newest history matters
        weights = []
        for it in items:
            st = median_correct_ms(conn, it["category"]) * 1.5
            weights.append(compute_weight(it, conn, st))
        pick = weighted_pick(items, weights, excluded)
        if pick is None:
            break
        print(f"\n[{i+1}/{args.count}]", end="")
        ui, time_ms = ask(pick)
        if ui is None or ui.strip() == "":
            print("  （跳過/結束）")
            break
        result = grade(pick, ui, strict=args.strict)
        give_feedback(pick, ui, result, time_ms, strict=args.strict)
        save_attempt(conn, pick, ui, result, time_ms)
        session_log.append(
            {
                "hanzi": pick["hanzi"],
                "category": pick["category"],
                "user_input": ui.strip(),
                "preferred": pick.get("preferred", ""),
                "zhuyin": pick.get("zhuyin", ""),
                "result": result,
                "time_ms": time_ms,
            }
        )
        excluded.add(pick["hanzi"])
        # 本局 / 全局 正確率（每題秀一行）
        sc = sum(1 for r in session_log if r["result"] != "wrong")
        sn = len(session_log)
        gn, gc = global_stats(conn, cats)
        sp = 100 * sc // max(sn, 1)
        gp = 100 * gc // max(gn, 1)
        print(f"  本局 {sc}/{sn} ({sp}%)   全局 {gc}/{gn} ({gp}%)")

    print_report(session_log)
    gn, gc = global_stats(conn, cats)
    if gn > 0:
        print(f"  全局累計    {gc}/{gn} ({100*gc//gn}%)  （依類別：{','.join(cats)}）")


if __name__ == "__main__":
    main()
