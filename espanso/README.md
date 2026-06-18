# espanso — 專案名稱快速輸入

在任何輸入框打幾個字 + `;`，自動展開成專案全名。英數模式和無蝦米模式都能用。 ^ck-8dbeb9-0

### 檔案

| 檔案 | 說明 |
|------|------|
| `espanso_projects.json` | 設定哪些路徑要掃子資料夾 |
| `scripts/gen_espanso.py` | 掃 ClaudeProjects/ 生成 Espanso config + 更新 liu.box |
| `scripts/start_espanso.bat` | 開機啟動：先更新 triggers 再啟動 Espanso |
| `liu.box` | 無蝦米自定義字典(與 Dropbox 雙向同步) |
^ck-999723-1 ^ck-fa5c93-1

### 每個專案一個 trigger

前 4 字母 + `;` — 例如 `know;` → `knowledge-system`

- 後綴 `;` 觸發(跟無蝦米打法一致)
- 數字開頭的名稱會跳過數字(`2026-disneysea` → `disn;`)
- 一律 4 字母，避免短 key 干擾無蝦米正常輸入 ^ck-61e1bc-2

### 分工：espanso 管專案名，嘸蝦米管自訂字串

兩者同時監聽鍵盤，重疊的 trigger 會打架（吃字、短 key 搶先觸發），所以各管各的：

1. **Espanso config**(`%APPDATA%/espanso/match/claude_projects.yml`) — 英數模式，只寫專案 trigger
2. **無蝦米 liu.box**(`Dropbox/設定檔/liu.box`) — 中文輸入法模式，手動條目 + 專案 trigger

**撞名規則：手動條目優先**
- 專案 trigger 和 liu.box 手動條目撞名時跳過，兩邊都不寫 ^ck-32657a-3

### 子專案

預設只掃 `ClaudeProjects/` 第一層。想掃某個專案底下的子資料夾，在 `espanso_projects.json` 加路徑：

```json
{
  "scan_children": [
    "trip-doc-generator/trips",
    "某專案/某子資料夾"
  ]
}
``` ^ck-4fadb5-4

### 更新 triggers

新增專案後跑一次：

```bash
cd ClaudeProjects/tools/espanso/scripts && python gen_espanso.py
espanso restart
```

開機時 `scripts/start_espanso.bat` 會自動跑。 ^ck-fbf4ea-5

### Mac 版（espanso 直接展開，不經無蝦米）

Windows 用無蝦米接 liu.box；Mac 沒無蝦米，改讓 espanso 自己展開專案名。

- `scripts/gen_espanso_mac.py` — 掃 `~/Projects/` 生成 espanso match YAML（重用 `gen_espanso.py` 的掃描 + trigger 邏輯，只換 output writer）
- 輸出：`~/Library/Application Support/espanso/match/projects.yml`（獨立檔，不碰 `base.yml`）
- trigger 形狀沿用 Windows：前 4 字母 + `;`（例 `know;` → `knowledge-system`）
- 自訂字串（email、簽名等）手動加在 `base.yml`，跑 `espanso edit` 編輯即可

更新 triggers（新增專案資料夾後）：

```bash
cd ~/Projects/tools/espanso/scripts && python3 gen_espanso_mac.py
```

**⚠️ Mac 啟動陷阱**：espanso 必須以 GUI App 身份啟動（`open -a Espanso` 或 `espanso service start`），**不能**從終端機 `espanso worker` 拉起來——後者 macOS 把輔助使用權限歸給終端機，注入會被靜默擋掉（worker log 看似正常、字卻打不出來）。開機自啟靠 `espanso service register`（寫 `~/Library/LaunchAgents` plist，`RunAtLoad=true`）。

**⚠️ Mac 啟動陷阱 2（launchctl EIO，macOS 26 Tahoe 實測，2026-06-17 Air）**：`espanso service register` 成功後，`espanso service start` / `launchctl bootstrap` 可能撞 `Bootstrap failed: 5: Input/output error`（errno 5 EIO），launchd 根本沒 exec（`/tmp/espanso.err` 空）。根因是服務被留在 **disabled** 狀態（前面失敗的 start 嘗試造成）。解法：bootstrap 前先 enable——
```bash
launchctl enable gui/$(id -u)/com.federicoterzi.espanso
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.federicoterzi.espanso.plist
```
enable 後 bootstrap exit=0、`espanso status` = running、`launchctl list | grep espanso` 看得到 PID。首裝完整流程：`open -a Espanso`（觸發輔助使用權限 wizard）→ 系統設定授權 → 上述 enable + bootstrap 註冊自啟。

### 依賴

- [Espanso](https://espanso.org/) v2.3+
  - Windows：`winget install Espanso.Espanso`
  - Mac：`brew install --cask espanso`，首跑需到 系統設定 → 隱私權與安全性 → 輔助使用 開啟 Espanso
- Python + pyyaml ^ck-127f40-6

### 安裝紀錄

每台機器安裝後，在 `env.machines.md` 記錄 Espanso 版本與安裝日期。其他小工具也一樣 — 裝了就記，確保兩台機器同步。 ^ck-fb97dc-7
