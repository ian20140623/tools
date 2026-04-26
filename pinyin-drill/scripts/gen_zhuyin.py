#!/usr/bin/env python3
"""Build-time tool: 給 seed JSON 加 zhuyin 欄位（無聲調）。

策略：
- nng-char / nng-word：preferred 是全拼，greedy longest-match 拆 syllable
- apostrophe：找 accepted 裡含 ' 的，用 ' 拆 syllable
- 每 syllable 查 SYLLABLE_TO_ZHUYIN
- 未知 syllable raise，由人工補

用法： python3 scripts/gen_zhuyin.py [--check]
  --check：只報 missing syllable 不寫檔
"""
import argparse
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

SYLLABLE_TO_ZHUYIN = {
    "an": "ㄢ", "ang": "ㄤ",
    "bai": "ㄅㄞ", "ban": "ㄅㄢ", "bang": "ㄅㄤ", "bao": "ㄅㄠ",
    "bei": "ㄅㄟ", "ben": "ㄅㄣ", "beng": "ㄅㄥ", "bu": "ㄅㄨ",
    "chan": "ㄔㄢ", "chang": "ㄔㄤ", "cheng": "ㄔㄥ",
    "chong": "ㄔㄨㄥ", "chu": "ㄔㄨ",
    "da": "ㄉㄚ", "dan": "ㄉㄢ", "dang": "ㄉㄤ",
    "dian": "ㄉㄧㄢ", "dong": "ㄉㄨㄥ",
    "en": "ㄣ", "er": "ㄦ",
    "fan": "ㄈㄢ", "fang": "ㄈㄤ", "fen": "ㄈㄣ", "feng": "ㄈㄥ", "fu": "ㄈㄨ",
    "gan": "ㄍㄢ", "gen": "ㄍㄣ", "geng": "ㄍㄥ",
    "gong": "ㄍㄨㄥ", "guo": "ㄍㄨㄛ",
    "ji": "ㄐㄧ", "jin": "ㄐㄧㄣ", "jing": "ㄐㄧㄥ",
    "ken": "ㄎㄣ", "keng": "ㄎㄥ",
    "lin": "ㄌㄧㄣ", "ling": "ㄌㄧㄥ",
    "men": "ㄇㄣ", "meng": "ㄇㄥ", "min": "ㄇㄧㄣ", "ming": "ㄇㄧㄥ",
    "nao": "ㄋㄠ", "nian": "ㄋㄧㄢ", "ning": "ㄋㄧㄥ", "nv": "ㄋㄩ",
    "ou": "ㄡ",
    "peng": "ㄆㄥ", "pin": "ㄆㄧㄣ", "ping": "ㄆㄧㄥ",
    "qing": "ㄑㄧㄥ",
    "ren": "ㄖㄣ", "reng": "ㄖㄥ", "rong": "ㄖㄨㄥ",
    "shen": "ㄕㄣ", "sheng": "ㄕㄥ",
    "tai": "ㄊㄞ", "ti": "ㄊㄧ", "tian": "ㄊㄧㄢ",
    "wan": "ㄨㄢ", "wen": "ㄨㄣ", "weng": "ㄨㄥ",
    "xi": "ㄒㄧ", "xian": "ㄒㄧㄢ", "xiang": "ㄒㄧㄤ",
    "xiao": "ㄒㄧㄠ", "xin": "ㄒㄧㄣ", "xing": "ㄒㄧㄥ", "xue": "ㄒㄩㄝ",
    "yan": "ㄧㄢ", "yin": "ㄧㄣ", "ying": "ㄧㄥ", "you": "ㄧㄡ", "yun": "ㄩㄣ",
    "zhen": "ㄓㄣ", "zheng": "ㄓㄥ", "zhi": "ㄓ", "zhong": "ㄓㄨㄥ",
}

KNOWN = sorted(SYLLABLE_TO_ZHUYIN.keys(), key=len, reverse=True)


def split_pinyin(s):
    """Greedy longest-match split. 'anning' → ['an','ning']."""
    out = []
    i = 0
    while i < len(s):
        for syl in KNOWN:
            if s.startswith(syl, i):
                out.append(syl)
                i += len(syl)
                break
        else:
            return None  # unknown
    return out


def syllables_for(item):
    cat = item["category"]
    if cat in ("nng-char", "nng-word"):
        # preferred 全拼；個別含 ' 的（少數）也支援
        s = item["preferred"].replace("'", "")
        return split_pinyin(s)
    if cat == "apostrophe":
        for a in item.get("accepted", []):
            if "'" in a:
                return [seg for seg in a.split("'") if seg]
        # fallback：accepted 裡找 fullpin（最長無 ' 的）
        cands = [a for a in item.get("accepted", []) if "'" not in a and len(a) > 3]
        if cands:
            return split_pinyin(max(cands, key=len))
    return None


def to_zhuyin(syls):
    parts = []
    for s in syls:
        z = SYLLABLE_TO_ZHUYIN.get(s)
        if z is None:
            return None, s
        parts.append(z)
    return " ".join(parts), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只報 missing 不寫檔")
    args = ap.parse_args()

    files = ["seed_nng_chars.json", "seed_nng_words.json", "seed_apostrophe.json"]
    missing = []
    updated = {}

    for fname in files:
        path = DATA_DIR / fname
        items = json.loads(path.read_text(encoding="utf-8"))
        for it in items:
            syls = syllables_for(it)
            if syls is None:
                missing.append((fname, it["hanzi"], it.get("preferred"), "split-failed"))
                continue
            zhuyin, miss = to_zhuyin(syls)
            if zhuyin is None:
                missing.append((fname, it["hanzi"], it.get("preferred"), f"missing:{miss}"))
                continue
            it["zhuyin"] = zhuyin
        updated[fname] = items

    if missing:
        print("⚠ 有未處理項目：")
        for m in missing:
            print(f"  {m[0]:25s}  {m[1]:8s}  pref={m[2]:15s}  {m[3]}")
        if not args.check:
            print("\n中止寫檔。請補 SYLLABLE_TO_ZHUYIN 後重跑。")
            sys.exit(1)
    else:
        print("✓ 全部 syllable 命中")

    if args.check:
        return

    for fname, items in updated.items():
        path = DATA_DIR / fname
        path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"  寫入 {fname}  ({len(items)} 筆)")


if __name__ == "__main__":
    main()
