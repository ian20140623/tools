"""
掃描 ClaudeProjects/ 資料夾，自動生成 Espanso trigger config。
每個專案產生兩個 trigger：
  1. 前 4 字母（如 ;know → knowledge-system）
  2. 首字母縮寫（如 ;ks → knowledge-system）

用法：python gen_espanso.py
"""

import json
import os
import re
import yaml
from pathlib import Path

PROJECTS_DIR = Path(__file__).resolve().parent.parent.parent.parent  # ClaudeProjects/
ESPANSO_MATCH = Path(os.environ["APPDATA"]) / "espanso" / "match"
CONFIG_FILE = Path(__file__).resolve().parent.parent / "espanso_projects.json"

# 不算專案的資料夾/檔案
SKIP = {"shared", "tools", "archived", "CLAUDE.md", "env.machines.md", ".git"}


def load_config():
    """讀取設定：哪些路徑要掃子資料夾"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {"scan_children": []}


def get_projects():
    """回傳所有專案名稱（含子專案）"""
    config = load_config()

    # 第一層
    names = []
    for d in os.listdir(PROJECTS_DIR):
        if (PROJECTS_DIR / d).is_dir() and d not in SKIP and not d.startswith("."):
            names.append(d)

    # 設定檔指定的子資料夾
    for rel_path in config.get("scan_children", []):
        parent = PROJECTS_DIR / rel_path
        if parent.is_dir():
            for d in os.listdir(parent):
                if (parent / d).is_dir() and not d.startswith("."):
                    names.append(d)

    return sorted(set(names))


def strip_leading_numbers(name: str) -> str:
    """2026-disney → disney, knowledge-system → knowledge-system"""
    return re.sub(r"^\d+[-_]?", "", name) or name


def make_abbreviation(name: str) -> str:
    """knowledge-system → ks, trip-doc-generator → tdg, 2026-disney → d"""
    clean = strip_leading_numbers(name)
    parts = clean.replace("_", "-").split("-")
    return "".join(p[0] for p in parts if p)


def make_prefix(name: str, length: int = 4) -> str:
    """knowledge-system → know, 2026-disney → disn"""
    clean = strip_leading_numbers(name)
    clean = clean.replace("-", "").replace("_", "")
    return clean[:length].lower()


def generate():
    projects = get_projects()

    # 第一輪：收集所有 trigger → 對應的專案名（可能多個）
    trigger_map = {}  # trigger_str → [name1, name2, ...]
    for name in projects:
        abbr = make_abbreviation(name)
        prefix = make_prefix(name)

        trigger_abbr = f";{abbr}"
        trigger_map.setdefault(trigger_abbr, []).append(name)

        trigger_pre = f";{prefix}"
        if trigger_pre != trigger_abbr:
            trigger_map.setdefault(trigger_pre, []).append(name)

    # 第二輪：無衝突 → 直接替換；有衝突 → choice 選單
    matches = []
    for trigger, names in sorted(trigger_map.items()):
        if len(names) == 1:
            matches.append({"trigger": trigger, "replace": names[0]})
        else:
            # Espanso choice：打 trigger 後跳出選單讓用戶選
            choices = [{"label": n, "id": n} for n in names]
            matches.append({
                "trigger": trigger,
                "replace": "{{choice}}",
                "vars": [{"name": "choice", "type": "choice", "params": {"values": choices}}],
            })

    config = {"matches": matches}
    out_path = ESPANSO_MATCH / "claude_projects.yml"
    out_path.write_text(yaml.dump(config, allow_unicode=True, default_flow_style=False), encoding="utf-8")

    print(f"Generated {len(matches)} triggers for {len(projects)} projects → {out_path}")
    print()
    for trigger, names in sorted(trigger_map.items()):
        if len(names) == 1:
            print(f"  {trigger:12s} → {names[0]}")
        else:
            print(f"  {trigger:12s} → [選單] {', '.join(names)}")


if __name__ == "__main__":
    generate()
