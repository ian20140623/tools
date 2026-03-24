# espanso — 專案名稱快速輸入

在任何輸入框打幾個字 + `;`，自動展開成專案全名。英數模式和無蝦米模式都能用。

### 檔案

| 檔案 | 說明 |
|------|------|
| `espanso_projects.json` | 設定哪些路徑要掃子資料夾 |
| `scripts/gen_espanso.py` | 掃 ClaudeProjects/ 生成 Espanso config + 更新 liu.box |
| `scripts/start_espanso.bat` | 開機啟動：先更新 triggers 再啟動 Espanso |
| `liu.box` | 無蝦米自定義字典(與 Dropbox 雙向同步) |

### 每個專案一個 trigger

前 4 字母 + `;` — 例如 `know;` → `knowledge-system`

- 後綴 `;` 觸發(跟無蝦米打法一致)
- 數字開頭的名稱會跳過數字(`2026-disneysea` → `disn;`)
- 一律 4 字母，避免短 key 干擾無蝦米正常輸入

### 分工：espanso 管專案名，嘸蝦米管自訂字串

兩者同時監聽鍵盤，重疊的 trigger 會打架（吃字、短 key 搶先觸發），所以各管各的：

1. **Espanso config**(`%APPDATA%/espanso/match/claude_projects.yml`) — 英數模式，只寫專案 trigger
2. **無蝦米 liu.box**(`Dropbox/設定檔/liu.box`) — 中文輸入法模式，手動條目 + 專案 trigger

**撞名規則：手動條目優先**
- 專案 trigger 和 liu.box 手動條目撞名時跳過，兩邊都不寫

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
cd ClaudeProjects/tools/espanso/scripts && python gen_espanso.py
espanso restart
```

開機時 `scripts/start_espanso.bat` 會自動跑。

### 依賴

- [Espanso](https://espanso.org/) v2.3+(`winget install Espanso.Espanso`)
- Python + pyyaml

### 安裝紀錄

每台機器安裝後，在 `env.machines.md` 記錄 Espanso 版本與安裝日期。其他小工具也一樣 — 裝了就記，確保兩台機器同步。
