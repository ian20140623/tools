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

### 雙輸入法支援

`gen_espanso.py` 同時寫入兩個地方：

1. **Espanso config**(`%APPDATA%/espanso/match/claude_projects.yml`) — 英數模式
2. **無蝦米 liu.box**(`Dropbox/設定檔/liu.box`) — 中文輸入法模式

自動生成的條目放在 liu.box 末尾，以 `ZZAUTO` marker 行分隔，不影響手動維護的條目。

**撞名規則：各管各的，互不干擾**
- **無蝦米**（liu.box）— 手動條目永遠優先。撞名時保留手動的中文/術語定義，跳過自動專案名。中文模式下打字根是要打中文。
- **Espanso**（英數模式）— trigger 全部生成，不管 liu.box 有沒有撞。英數模式的重點是快速輸入專案名，以及誤按時不會出意外的中文。

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
