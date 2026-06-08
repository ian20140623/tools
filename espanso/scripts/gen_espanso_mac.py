"""
Mac 版：掃描 ClaudeProjects/ 生成 espanso 專案 trigger YAML。

跟 gen_espanso.py 的分工：
- gen_espanso.py（Windows）：寫無蝦米 liu.box，因為 NB/DESKTOP 用無蝦米
- gen_espanso_mac.py（本檔）：寫 espanso match YAML，因為 Mac 沒無蝦米、用 espanso

重用 gen_espanso.py 的掃描 + trigger 邏輯（get_projects / build_trigger_map），
只新增 espanso YAML 的 output writer（OCP：不動原檔）。

trigger 形狀沿用：前 4 字母 + ';'（例：know; -> knowledge-system），跟 Windows 一致。

輸出：~/Library/Application Support/espanso/match/projects.yml
（獨立檔，不碰 espanso 預設的 base.yml）

用法：python3 gen_espanso_mac.py
"""

import os
from pathlib import Path

import gen_espanso as base

# espanso 設定目錄（可用 ESPANSO_CONFIG 覆寫；預設 macOS 標準路徑）
_ESPANSO_DIR = Path(
    os.environ.get(
        "ESPANSO_CONFIG",
        Path.home() / "Library" / "Application Support" / "espanso",
    )
)
OUTPUT_FILE = _ESPANSO_DIR / "match" / "projects.yml"


def yaml_escape(s: str) -> str:
    """espanso trigger/replace 用雙引號包，內部雙引號轉義。"""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def generate_yaml(trigger_map) -> str:
    """從 trigger_map 生成 espanso match YAML 字串。撞名（一 trigger 多專案）跳過。"""
    lines = [
        "# 自動生成 by gen_espanso_mac.py — 請勿手動編輯",
        "# 重生：cd tools/espanso/scripts && python3 gen_espanso_mac.py",
        "",
        "matches:",
    ]
    written = 0
    skipped = []
    for trigger, names in sorted(trigger_map.items()):
        if len(names) > 1:
            skipped.append(f"{trigger} ({', '.join(names)})")
            continue
        t = yaml_escape(trigger)
        r = yaml_escape(names[0])
        lines.append(f'  - trigger: "{t}"')
        lines.append(f'    replace: "{r}"')
        written += 1
    return "\n".join(lines) + "\n", written, skipped


def generate():
    projects = base.get_projects()
    trigger_map = base.build_trigger_map(projects)

    yaml_text, written, skipped = generate_yaml(trigger_map)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(yaml_text, encoding="utf-8")

    print(f"[espanso] wrote {written} project triggers -> {OUTPUT_FILE}")
    if skipped:
        print(f"[espanso] skipped {len(skipped)} (撞名): {', '.join(skipped)}")
    print()
    print("--- 專案 triggers ---")
    for trigger, names in sorted(trigger_map.items()):
        if len(names) == 1:
            print(f"  {trigger:10s} -> {names[0]}")
    print()
    print("套用：espanso restart（或 open -a Espanso）")


if __name__ == "__main__":
    generate()
