"""
掃描 ClaudeProjects/ 資料夾，自動生成：
  1. Espanso trigger config（英數模式）— 只寫專案名 trigger
  2. 無蝦米 liu.box 專案條目（中文輸入法模式）

分工：espanso 只管專案名，手動條目由嘸蝦米 liu.box 處理。
兩邊不重疊，避免同時觸發打架。

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

# liu.box 路徑（DROPBOX_PATH 環境變數指向 Dropbox 根目錄）
_DROPBOX_DIR = Path(os.environ["DROPBOX_PATH"]) if "DROPBOX_PATH" in os.environ else None
LIU_DROPBOX = _DROPBOX_DIR / "設定檔" / "liu.box" if _DROPBOX_DIR else None
LIU_BACKUP = Path(__file__).resolve().parent.parent / "liu.box"

# 自動生成區的 marker（liu.box 裡用這行標記自動生成的開始）
LIU_MARKER = "ZZAUTO; === ClaudeProjects Auto-Generated ==="

# 不算專案的資料夾/檔案
SKIP = {"shared", "archived", "CLAUDE.md", "env.machines.md", ".git"}


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


def build_trigger_map(projects):
    """建立 trigger → [專案名] 的對應表"""
    trigger_map = {}
    for name in projects:
        prefix = make_prefix(name, 4)
        trigger = f"{prefix};"
        trigger_map.setdefault(trigger, []).append(name)

    return trigger_map


def read_liu_box(path):
    """讀取 liu.box，回傳 (手動條目行list, 自動條目行list)"""
    if not path.exists():
        return [], []

    data = path.read_bytes()
    text = data.decode("utf-16-le")
    if text and text[0] == "\ufeff":
        text = text[1:]

    lines = text.splitlines()

    # 找 marker 位置
    manual = []
    auto = []
    found_marker = False
    for line in lines:
        if line.strip() == LIU_MARKER:
            found_marker = True
            continue
        if found_marker:
            auto.append(line)
        else:
            manual.append(line)

    return manual, auto


def parse_liu_entries(lines):
    """從 liu.box 行列表解析出 [(key, value), ...]"""
    entries = []
    for line in lines:
        if "; " in line:
            key, value = line.split("; ", 1)
            entries.append((key.strip(), value.strip()))
    return entries


def write_liu_box(path, manual_lines, auto_lines):
    """寫入 liu.box（UTF-16LE + BOM + CRLF）"""
    all_lines = manual_lines + [LIU_MARKER] + auto_lines
    text = "\r\n".join(all_lines)
    if not text.endswith("\r\n"):
        text += "\r\n"
    data = b"\xff\xfe" + text.encode("utf-16-le")
    path.write_bytes(data)


def generate_espanso(trigger_map, manual_keys):
    """生成 Espanso YAML config（只寫專案 trigger，手動條目留給嘸蝦米）"""
    matches = []

    for trigger, names in sorted(trigger_map.items()):
        # 手動條目優先，撞名跳過
        if trigger.rstrip(";") in manual_keys:
            continue
        if len(names) == 1:
            matches.append({"trigger": trigger, "replace": names[0]})
        else:
            choices = [{"label": n, "id": n} for n in names]
            matches.append({
                "trigger": trigger,
                "replace": "{{choice}}",
                "vars": [{"name": "choice", "type": "choice", "params": {"values": choices}}],
            })

    config = {"matches": matches}
    out_path = ESPANSO_MATCH / "claude_projects.yml"
    out_path.write_text(yaml.dump(config, allow_unicode=True, default_flow_style=False), encoding="utf-8")

    print(f"[Espanso] Generated {len(matches)} project triggers → {out_path}")
    return matches


def generate_liu(trigger_map, manual_lines, manual_keys):
    """生成無蝦米 liu.box 的專案條目，同時寫入 Dropbox 和 repo 備份"""
    # 生成專案條目（手動條目優先，撞名跳過）
    auto_lines = []
    skipped = []
    for trigger, names in sorted(trigger_map.items()):
        key = trigger.rstrip(";").upper()
        if key in manual_keys:
            skipped.append(f"{key} (手動條目已存在)")
            continue
        if len(names) == 1:
            auto_lines.append(f"{key}; {names[0]}")

    # 寫入 Dropbox
    if LIU_DROPBOX and LIU_DROPBOX.exists():
        write_liu_box(LIU_DROPBOX, manual_lines, auto_lines)
        print(f"[liu.box] Updated Dropbox: {LIU_DROPBOX}")

    # 寫入 repo 備份
    write_liu_box(LIU_BACKUP, manual_lines, auto_lines)
    print(f"[liu.box] Updated backup: {LIU_BACKUP}")

    print(f"[liu.box] Added {len(auto_lines)} project triggers, skipped {len(skipped)}")
    if skipped:
        print(f"  Skipped (manual key exists): {', '.join(skipped)}")

    return auto_lines


def generate():
    projects = get_projects()
    trigger_map = build_trigger_map(projects)

    # 讀 liu.box 手動條目（Dropbox 優先，有最新的手動修改）
    source = LIU_DROPBOX if (LIU_DROPBOX and LIU_DROPBOX.exists()) else LIU_BACKUP
    manual_lines, _ = read_liu_box(source)
    manual_entries = parse_liu_entries(manual_lines)
    manual_keys = {k for k, _ in manual_entries}

    # Espanso（只寫專案 trigger）
    generate_espanso(trigger_map, manual_keys)

    # 無蝦米 liu.box（手動條目不動，加專案自動條目）
    generate_liu(trigger_map, manual_lines, manual_keys)

    # 印出 trigger 對照表
    print(f"\n--- 專案 triggers ---")
    for trigger, names in sorted(trigger_map.items()):
        if len(names) == 1:
            print(f"  {trigger:12s} → {names[0]}")
        else:
            print(f"  {trigger:12s} → [選單] {', '.join(names)}")


if __name__ == "__main__":
    generate()
