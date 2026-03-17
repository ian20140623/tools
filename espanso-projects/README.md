# espanso-projects — 專案名稱快速輸入

在任何輸入框打幾個字，自動展開成專案全名。

### 檔案

| 檔案 | 說明 |
|------|------|
| `espanso_projects.json` | 設定哪些路徑要掃子資料夾 |
| `scripts/gen_espanso.py` | 掃 ClaudeProjects/ 生成 Espanso trigger config |
| `scripts/start_espanso.bat` | 開機啟動：先更新 triggers 再啟動 Espanso |

### 每個專案產生兩個 trigger

1. **首字母縮寫** — `;ks` → `knowledge-system`
2. **前 4 字母** — `;know` → `knowledge-system`

- 數字開頭的名稱會跳過數字（`2026-disneysea` → `;disn`）
- 撞名時跳出選單讓用戶選
- trigger 前綴是 `;`

### 子專案

預設只掃 `ClaudeProjects/` 第一層。想掃某個專案底下的子資料夾，在 `espanso_projects.json` 加路徑：

```json
{
  "scan_children": [
    "trip-doc-generator/trips",
    "某專案/某子資料夾"
  ]
}
```

### 更新 triggers

新增專案後跑一次：

```bash
cd ClaudeProjects/tools/espanso-projects/scripts && python gen_espanso.py
espanso restart
```

開機時 `scripts/start_espanso.bat` 會自動跑。

### 依賴

- [Espanso](https://espanso.org/) v2.3+（`winget install Espanso.Espanso`）
- Python + pyyaml

### 安裝紀錄

每台機器安裝後，在 `env.machines.md` 記錄 Espanso 版本與安裝日期。其他小工具也一樣 — 裝了就記，確保兩台機器同步。
