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
- 自訂字串（email、簽名等）加在 Dropbox 的 `espanso/base.yml`，所有 Mac 共用

更新 triggers（新增專案資料夾後）：

```bash
cd ~/Projects/tools/espanso/scripts && python3 gen_espanso_mac.py
```

**cd 捷徑（`projects.yml` 一併生成）**：每個第一層專案再多一組 `cd{前4字母};` → `cd ~/Projects/{專案名}`（例 `cdknow;` → `cd ~/Projects/knowledge-system`）。跟專案名 trigger 共用同一套撞名跳過規則——縮寫相同的專案兩邊都不生成。只掃第一層，不含 `scan_children` 子專案（子專案沒有可推導的完整路徑）。

**自動排除 git worktree**：`is_worktree()` 判斷 `.git` 是檔案（worktree，指向主 repo 的 `.git/worktrees/...`）還是資料夾（真正的 repo），worktree 一律不生成 trigger——這類資料夾多半是 Eagle Eye/Spock review 用 `isolation: "worktree"` 留下的暫存工作目錄，不該有專案名/cd 捷徑。

**⚠️ Mac 啟動陷阱**：espanso 必須以 GUI App 身份啟動（`open -a Espanso` 或 `espanso service start`），**不能**從終端機 `espanso worker` 拉起來——後者 macOS 把輔助使用權限歸給終端機，注入會被靜默擋掉（worker log 看似正常、字卻打不出來）。開機自啟靠 `espanso service register`（寫 `~/Library/LaunchAgents` plist，`RunAtLoad=true`）。

**⚠️ Mac 啟動陷阱 2（launchctl EIO，macOS 26 Tahoe 實測，2026-06-17 Air）**：`espanso service register` 成功後，`espanso service start` / `launchctl bootstrap` 可能撞 `Bootstrap failed: 5: Input/output error`（errno 5 EIO），launchd 根本沒 exec（`/tmp/espanso.err` 空）。根因是服務被留在 **disabled** 狀態（前面失敗的 start 嘗試造成）。解法：bootstrap 前先 enable——
```bash
launchctl enable gui/$(id -u)/com.federicoterzi.espanso
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.federicoterzi.espanso.plist
```
enable 後 bootstrap exit=0、`espanso status` = running、`launchctl list | grep espanso` 看得到 PID。首裝完整流程：`open -a Espanso`（觸發輔助使用權限 wizard）→ 系統設定授權 → 上述 enable + bootstrap 註冊自啟。

### Mac 跨機同步（Dropbox single source of truth）

所有 Mac 的手動自訂字串共用一份 Dropbox 原始檔：

- `~/Dropbox/espanso/base.yml` — **唯一可編輯來源**；Dropbox 自動跨機同步
- `~/Library/Application Support/espanso/match/base.yml` — symlink 指向上述 Dropbox 檔
- `match/projects.yml` — 每台依本機 `~/Projects/` 生成，**不跨機同步**
- `mac-config/config/default.yml` — 低頻全域設定，繼續走 repo
- `mac-config/match/base.yml` — 初次安裝 seed／遷移期 fallback，不再是日常編輯來源

每台 Mac 裝好 Espanso 後執行一次：

```bash
python3 ~/Projects/tools/espanso/scripts/install_espanso_shared_mac.py
```

安裝器會先確認 Dropbox 與 Espanso service 真實存在；首次建立 canonical 時優先沿用現有 live 字串。若 Dropbox 與本機設定內容不同，安裝器會停下要求人工合併，不會覆蓋任一側。通過後保留唯一備份、建立 symlink，並把背景程式安裝到穩定的 Application Support 路徑。

背景 LaunchAgent 監看 Dropbox 目錄；檔案 metadata fingerprint（device／inode／size／mtime）改變時先用 `espanso match list` 驗證完整設定，成功且 fingerprint 在驗證期間未改變，才觸碰 live symlink，讓 Espanso 自己重新載入 worker。它不開 GUI、不搶焦點。helper 不直接開啟 Dropbox File Provider 的內容（dev01 實測 launchd ancestry 可能永久卡在 `open()`）。若 Espanso CLI 快速回報 YAML 錯誤，本輪仍拒絕 reload；只有 CLI 因相同 File Provider 限制 timeout 時，才明確記錄 warning，在 metadata 穩定檢查後交給已有 Dropbox 權限的 GUI worker 自行解析。File Provider 事件若被合併，另有每 5 分鐘一次的低成本補查。

symlink 表示 Dropbox 檔案就是 live 設定：上述驗證能避免背景程序主動 reload 已知壞檔，但不能隔離 Dropbox 已同步的壞 YAML；Espanso 登入啟動時仍可能直接讀到它。Dropbox 的版本歷史與 Espanso `backups/` 是復原路徑。

查看背景同步狀態：

```bash
launchctl print gui/$(id -u)/com.user.espanso-shared-reload
tail -20 ~/Library/Logs/espanso-shared-reload.log
```

若 Dropbox 產生 conflicted copy，背景程序只讀固定名稱 `base.yml`，不自動合併衝突檔。這是可執行的可信設定（Espanso 支援 shell match）：Dropbox 帳號與此資料夾不得開放他人寫入，且密碼、token、私鑰不得放進共用字串檔。

### 依賴

- [Espanso](https://espanso.org/) v2.3+
  - Windows：`winget install Espanso.Espanso`
  - Mac：`brew install --cask espanso`，首跑需到 系統設定 → 隱私權與安全性 → 輔助使用 開啟 Espanso
- Python + pyyaml ^ck-127f40-6

### 安裝紀錄

每台機器安裝後，在 `env.machines.md` 記錄 Espanso 版本與安裝日期。其他小工具也一樣 — 裝了就記，確保兩台機器同步。 ^ck-fb97dc-7
