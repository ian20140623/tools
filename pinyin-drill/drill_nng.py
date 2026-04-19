#!/usr/bin/env python3
"""pinyin-drill 聚焦變體 — 只練 n/ng 單字，嚴格模式，不收簡拼。

適合單純想補 n/ng 前後鼻音知識缺口時用（不被 apostrophe 詞題、
n/ng 雙字詞、jianpin 容錯干擾）。

用法：
    python3 drill_nng.py              # 預設 20 題
    python3 drill_nng.py --count 30   # 自訂題數
    python3 drill_nng.py --stats      # 只看累計統計
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import drill


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--stats", action="store_true", help="只顯示歷史統計")
    args = ap.parse_args()

    # 驅動 drill.main() 時改寫 sys.argv：固定 n/ng 單字 + 嚴格
    new_argv = ["drill.py", "--category", "nng-char", "--strict", "--count", str(args.count)]
    if args.stats:
        new_argv.append("--stats")
    sys.argv = new_argv
    drill.main()


if __name__ == "__main__":
    main()
