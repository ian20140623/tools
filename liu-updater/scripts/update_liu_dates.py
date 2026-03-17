"""
更新 liu.box 裡的時間相關字根為當前日期。

字根對照（以 2026-03 = 1Q26 為例）：
  年度：
    LLY  → 前年（2024年）
    LY   → 去年（2025年）
    TY   → 今年（2026年）
    NY   → 明年（2027年）
    NNY  → 後年（2028年）
    TM   → 這個月（2026-03-）

  季度（嘸蝦米數字：E=1, R=2, S=3, F=4）：
    EQ   → 1Q26（當季）
    RQ   → 2Q26（後1季）
    SQ   → 3Q25（前2季，1Q↔3Q 年份明確）
    FQ   → 4Q25（前1季）

  季度衍生：
    ERQ  → 1-2Q26（上半年）
    ESQ  → 9M26累計（前三季累計）
    QARP → [2026年報]（年報）

  臨近2季度原則：
    - 當季、前1季、後1季：年份明確
    - 距離2季：1Q↔3Q 永遠明確，2Q↔4Q 年份不確定只秀 XQ

每次跑都用系統時間重算，寫回 Dropbox + repo 備份。

用法：python update_liu_dates.py
"""

import os
from datetime import datetime
from pathlib import Path

LIU_DROPBOX = Path(os.environ["USERPROFILE"]) / "Dropbox" / "設定檔" / "liu.box"
LIU_BACKUP = Path(__file__).resolve().parent.parent.parent / "espanso" / "liu.box"


def current_quarter(now: datetime) -> int:
    return (now.month - 1) // 3 + 1


def quarter_value(q: int, year: int, ambiguous: bool) -> str:
    """生成季度值。ambiguous=True 時不帶年份。"""
    if ambiguous:
        return f"{q}Q"
    return f"{q}Q{year % 100}"


def quarter_entries(now: datetime) -> dict[str, str]:
    """根據臨近2季度原則，算出 EQ/RQ/SQ/FQ 的值。"""
    cq = current_quarter(now)
    cy = now.year

    # 計算每個季度的年份和是否模糊
    # 臨近2季度原則：
    #   當季、前1季、後1季 → 年份明確
    #   距離2季 → 1Q↔3Q 明確（取最近的），2Q↔4Q 模糊（不帶年）
    result = {}
    for target_q in range(1, 5):
        if target_q == cq:
            result[target_q] = quarter_value(target_q, cy, ambiguous=False)
            continue

        # 用環形距離算方向：正=後1季，負=前1季
        diff = (target_q - cq + 4) % 4  # 1=後1季, 2=對角, 3=前1季
        if diff == 3:
            diff = -1  # 前1季

        if abs(diff) == 1:
            # 前1季或後1季：年份明確
            if diff == -1:
                # 前1季：target_q > cq 代表跨年（如 cq=1, target=4 → 4Q of prev year）
                y = cy - 1 if target_q > cq else cy
            else:
                # 後1季：target_q < cq 代表跨年（如 cq=4, target=1 → 1Q of next year）
                y = cy + 1 if target_q < cq else cy
            result[target_q] = quarter_value(target_q, y, ambiguous=False)
        else:
            # 距離2季
            if {target_q, cq} == {2, 4}:
                # 2Q↔4Q：模糊，不帶年
                result[target_q] = quarter_value(target_q, cy, ambiguous=True)
            else:
                # 1Q↔3Q：取最近的（前2季）
                # cq=1 → 3Q 是前2季 → 3Q of prev year
                # cq=3 → 1Q 是前2季 → 1Q of same year
                y = cy - 1 if target_q > cq else cy
                result[target_q] = quarter_value(target_q, y, ambiguous=False)

    # 嘸蝦米 key 對照：E=1, R=2, S=3, F=4
    key_map = {1: "EQ", 2: "RQ", 3: "SQ", 4: "FQ"}
    return {key_map[q]: v for q, v in result.items()}


def half_year_entries(now: datetime) -> dict[str, str]:
    """ERQ（上半年）、ESQ（前三季累計）、QARP（年報）。"""
    cy = now.year
    y2 = cy % 100
    return {
        "ERQ": f"1-2Q{y2}",
        "ESQ": f"9M{y2}累計",
        "QARP": f"[{cy}年報]",
    }


def time_entries(now: datetime) -> dict[str, str]:
    entries = {
        "LLY": f"{now.year - 2}年",
        "LY": f"{now.year - 1}年",
        "TY": f"{now.year}年",
        "NY": f"{now.year + 1}年",
        "NNY": f"{now.year + 2}年",
        "TM": f"{now.year}-{now.month:02d}-",
    }
    entries.update(quarter_entries(now))
    entries.update(half_year_entries(now))
    return entries


TIME_KEYS = {"LLY", "LY", "TY", "NY", "NNY", "TM",
             "EQ", "RQ", "SQ", "FQ", "ERQ", "ESQ", "QARP"}


def read_liu(path: Path) -> list[str]:
    data = path.read_bytes()
    text = data.decode("utf-16-le")
    if text and text[0] == "\ufeff":
        text = text[1:]
    return text.splitlines()


def write_liu(path: Path, lines: list[str]):
    text = "\r\n".join(lines) + "\r\n"
    path.write_bytes(b"\xff\xfe" + text.encode("utf-16-le"))


def update(lines: list[str], now: datetime) -> tuple[list[str], list[str]]:
    entries = time_entries(now)
    updated = []
    changed = []

    for line in lines:
        if "; " in line:
            key = line.split("; ", 1)[0].strip()
            if key in TIME_KEYS:
                old_val = line.split("; ", 1)[1]
                new_val = entries[key]
                if old_val != new_val:
                    changed.append(f"  {key}: {old_val} → {new_val}")
                updated.append(f"{key}; {new_val}")
                continue
        updated.append(line)

    return updated, changed


def main():
    now = datetime.now()
    cq = current_quarter(now)
    print(f"Current date: {now.strftime('%Y-%m-%d')} ({cq}Q{now.year % 100})")

    # 從 Dropbox 讀（有最新手動修改）
    source = LIU_DROPBOX if LIU_DROPBOX.exists() else LIU_BACKUP
    lines = read_liu(source)

    updated, changed = update(lines, now)

    if not changed:
        print("All time entries are up to date.")
        return

    print(f"Updated {len(changed)} entries:")
    for c in changed:
        print(c)

    # 寫回
    if LIU_DROPBOX.exists():
        write_liu(LIU_DROPBOX, updated)
        print(f"Written to Dropbox: {LIU_DROPBOX}")

    write_liu(LIU_BACKUP, updated)
    print(f"Written to backup: {LIU_BACKUP}")


if __name__ == "__main__":
    main()
