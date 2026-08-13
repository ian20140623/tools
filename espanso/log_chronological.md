# espanso — 開發記錄
^ck-b6a511-0 ^ck-e5a126-0

## 2026-03-17（一）
^ck-bdc1e1-1 ^ck-8cbb0c-1

### 12:00 [NB] 初始建立

- **起因**：在 Claude Code 聊天中引用其他專案名要打全名太麻煩
- **方案選擇**：評估過 VS Code snippets（只在編輯器內）、zoxide（只跳目錄）、AutoHotkey（Windows 限定腳本），最後選 Espanso（跨平台、YAML 設定、AI 好維護）
- **核心設計**：`gen_espanso.py` 掃 `ClaudeProjects/` 自動生成 triggers，不維護靜態列表
- **兩種 trigger**：首字母縮寫（`;ks`）+ 前 4 字母（`;know`）
- **撞名處理**：同一 trigger 對應多個專案時，生成 Espanso choice 選單讓用戶選
- **數字開頭**：`2026-disneysea` 跳過數字部分，用 `disn` 生成 trigger
- **子專案**：透過 `espanso_projects.json` 設定要掃的子資料夾（如 `trip-doc-generator/trips`）
- **開機自啟**：`start_espanso.bat` 先跑 gen 再啟動 Espanso，放 Windows Startup
- **tools/ 憲法**：建立 `tools/README.md`，8 條規則（資料夾隔離、README、log、env 記錄、scripts/scratch 等）
- **DT 待辦**：記在 `env.machines.md`，等回家裝 ^ck-172955-2

### 13:13 [NB] trigger 改後綴 + tools/espanso 納入管理 + liu.box 備份

- **資料夾改名**：`espanso-projects` → `espanso`，更簡潔
- **trigger 改後綴**：從前綴 `;esp` 改為後綴 `esp;`，跟無蝦米的打法一致（先打字根再打 `;` 送出）
- **trigger 多長度**：從只有前 4 字母，改為前 2/3/4 字母都產生 trigger（`es;` `esp;` `espa;` 都能用）
- **tools 也納入**：`tools` 從 SKIP 移除，`espanso_projects.json` 加入 `"tools"` 掃子資料夾，tools 和子工具都有 trigger
- **liu.box 備份**：無蝦米自定義字典（595 筆）複製進 `tools/espanso/liu.box` 做版本控制，原檔繼續在 Dropbox
- **未來方向**：gen_espanso.py 同時寫入 liu.box，讓兩個輸入法（英數 Espanso + 無蝦米）都能用同一套字根觸發專案名，解決「忘記切輸入法」的痛點 ^ck-7d7b61-3

### 13:23 [NB] Espanso + liu.box 雙輸入法同步

- **gen_espanso.py 同時寫 Espanso yml + liu.box**：跑一次同時更新兩個系統
- **liu.box 自動區**：末尾用 `ZZAUTO` marker 分隔，marker 前是手動條目（不動），marker 後是自動生成的專案 trigger
- **雙向同步**：以 Dropbox liu.box 為手動條目來源，gen_espanso.py 讀取後加入自動條目，同時寫回 Dropbox 和 repo 備份
- **撞名規則**：各管各的互不干擾。無蝦米手動條目優先（中文模式打字根是要中文），Espanso 全部生成不跳過（英數模式重點是專案名和防誤按）
- **結果**：52 個專案 trigger 寫入 liu.box，23 個因手動條目已存在而跳過（如 BR=品牌、TW=台灣、AI=AI 等常用術語） ^ck-53b684-4

### 13:31 [NB] 簡化 trigger 規則：一律前 4 字母

- **問題**：短 key（2/3 字母、縮寫）在無蝦米模式會搶先跳出專案名，干擾正常中文輸入
- **決定**：Espanso 和 liu.box 兩邊同步，每個專案只生成一個 trigger — 前 4 字母 + `;`
- **拿掉的規則**：首字母縮寫（`ks;`）、前 2 字母（`kn;`）、前 3 字母（`kno;`）全部移除，單字母更早就移除了
- **結果**：78 → 21 個 trigger，每個專案一個，零撞名
- **撞名規則不變**：如果前 4 字母撞到 liu.box 手動條目，liu.box 跳過、Espanso 照生成 ^ck-16f2eb-5

## 2026-03-20（五）
^ck-c78f33-6 ^ck-363914-6

### 21:58 [DESKTOP] liu.box 升為 single source of truth

- **動機**：想要一個地方維護所有自訂字串，Espanso 和嘸蝦米同步更新
- **做法**：gen_espanso.py 讀 liu.box 手動區 → 同時寫入 Espanso config（英數模式）和 liu.box 自動區（嘸蝦米模式）
- **新增 parse_liu_entries()**：從 liu.box 行列表解析 key-value，供 generate_espanso() 使用
- **generate_espanso() 改版**：先寫 liu.box 手動條目（579 筆），再寫專案 trigger（24 筆），手動優先撞名跳過
- **generate_liu() 簡化**：手動條目讀取和 key 收集移到 generate() 統一處理
- **結果**：603 triggers 生成（579 liu.box + 24 專案），0 衝突 ^ck-a1310b-7

### 15:22 [DESKTOP] Dropbox 路徑改環境變數

- **問題**：DESKTOP Dropbox 在 `D:\Dropbox`，NB 在 `%USERPROFILE%\Dropbox`，寫死路徑只能在一台跑
- **解法**：改用 `DROPBOX_PATH` 環境變數，沒設時 fallback 讀 repo 備份
- **首筆共用字串**：加入 `OBS; Obsidian` 到 liu.box，兩邊都生效 ^ck-5f1d72-8

## 2026-06-08（一）

### 19:26 [MAC-MINI] espanso 上 Mac — gen_espanso_mac.py + 啟動陷阱

- **起因**：espanso 工具從頭到尾只在 Windows 跑過（log 機器標籤全 NB/DESKTOP），Mac 沒有無蝦米接 liu.box，等於 Mac 上沒有「打 4 字母 + `;` 展開專案名」這功能。用戶決定在 Mac 補回來。
- **方案選擇**：比較過 macOS 原生文字替換 vs espanso。原生免裝、能同步 iPhone，但無腳本批次刪除、要手動拖 .plist 匯入；espanso 要裝但「刪一個檔就乾淨」、跨平台一致。用戶選 espanso。
- **gen_espanso_mac.py**（OCP）：`import gen_espanso`，重用 `get_projects` / `build_trigger_map`，只新增 espanso YAML output writer，寫到 `~/Library/Application Support/espanso/match/projects.yml`（獨立檔，不碰 base.yml、不碰 liu.box）。trigger 形狀沿用 `know;`。掃出 28 專案、28 trigger、零撞名。
- **Mac 啟動陷阱（本次最大坑）**：espanso 必須以 GUI App 身份啟動（`open -a Espanso` / `espanso service start`），**不能**從終端機 `nohup espanso worker` 拉。macOS TCC 把輔助使用權限歸給「負責任的父程序」，終端機起的 worker 權限算終端機頭上，注入被靜默擋掉——`espanso match exec` 回 exit 0、worker log 看似正常、字卻打不出來，連測三次「沒反應」才從 GUI 啟動驗證解開。
- **secure input 干擾**：worker log 一直記 `secure input has been acquired`（espanso 猜 loginwindow，官方說此偵測不可靠），會週期性讓監聽瞎掉。本次非主因，但記錄備查。
- **launchd 開機自啟**：中途被 `pkill` 打斷 register/start 流程，殘留 `launchctl exit 3`。乾淨 `service unregister` → `register` → `service start` 一輪修好，launchctl list 出現正規 `com.federicoterzi.espanso` job，plist `RunAtLoad=true`。
- **自訂字串**：示範加 `proj; → projects` 到 base.yml，espanso 自動偵測即時重載，不需重啟。
- **教訓**：「終端機起的 GUI 工具權限歸屬不對」是 macOS 通則，不限 espanso；以後 Mac 上裝需要輔助使用/螢幕錄製權限的工具，一律 GUI 啟動驗證，別用終端機 nohup 判生死。 ^ck-mac-espanso-1

## 2026-06-18（四）

### 07:30 [MAC-MINI] 系統重裝後 espanso 還原 + 跨機設定納入版控

- **起因**：開 session 查 espanso 狀態 → binary / cask / app / config dir 全空。對照記錄發現 6/14 Mac mini 系統當機完全重裝，brew cask + 設定被抹掉、env.machines.md 那行還停在重裝前 `✅ 2.3.0` 沒同步現實（drift）。先查證（which / brew list / app bundle / caskroom / launchagent 五項全空）再下結論，沒腦補。
- **還原六步**：(1) `brew install --cask espanso` 2.3.0 → (2) 用戶 GUI 授輔助使用 → (3) `open -a Espanso` GUI 啟動（守 6/08 那條陷阱、process 確認來自 `/Applications/Espanso.app` 非終端機 worker）→ (4) `gen_espanso_mac.py` 重生 29 triggers（`line;` 撞名跳過）→ (5) `espanso service register` 開機自啟 → (6) env.machines.md 補重裝註記。
- **跨機同步（本次新增、用戶要求「進repo」）**：espanso 不會自己跨機同步、設定原本沒走 Dropbox/git。新增 `mac-config/{match/base.yml, config/default.yml}` 進 repo、live 目錄改 symlink 指過去；`projects.yml` 維持各機 `gen_espanso_mac.py` 本機生成不進 repo（內容依本機資料夾而定）。espanso restart 透過 symlink 讀取正常。
- **防覆蓋 gate（重要）**：repo 現存 base.yml 是 Mini 原廠空檔。Air 端 onboarding 時若 live base.yml 已有自訂縮寫，**必須先 cat 併進 repo 版再 symlink**，否則 Mini 空檔會覆蓋 Air 自訂。先 `git pull` 不動 live 檔（symlink 未建前 live 獨立）故安全。README 已記此 gate。
- **待確認**：用戶 Air 上是否真有自訂 base.yml 內容（決定 repo base.yml 該以哪台為 source of truth）。 ^ck-mac-espanso-restore-1

## 2026-08-13（四）

### 12:10 [MAC-AIR] Dropbox 成為 Mac 共用字串 single source of truth

- **架構**：常改的 `base.yml` 以 Dropbox `espanso/base.yml` 為 canonical；Espanso 固定位置 `~/Library/Application Support/espanso/match/base.yml` 改為 symlink。各機專案不同，`projects.yml` 仍由本機 generator 產生；`default.yml` 和安裝機制留在 tools repo。
- **背景 reload**：安裝 `com.user.espanso-shared-reload` LaunchAgent，監看 Dropbox 目錄並每 5 分鐘補查。內容沒變只算 hash；有變先用 Espanso CLI 驗證，再碰 symlink 通知既有 watcher，不開 GUI、不搶焦點。
- **安裝安全性**：先找 Dropbox 真實根目錄、確認 Espanso service 已註冊；首次安裝優先搬現有 live config，既有 Dropbox/live 不一致則停止要求人工合併。symlink、plist、runtime reloader 和新建 source 都有 rollback，重跑不重複備份。
- **已知取捨**：symlink 代表 Dropbox 同步壞 YAML 時，檔案本身已立即出現在 live 路徑；validator 能避免主動 reload，但不能隔離該檔。靠安裝前 YAML 驗證、Dropbox 版本歷史和本機備份復原。此檔屬可執行設定，不放秘密，也不可開放他人寫入 Dropbox 資料夾。
- **防撞名**：`gen_espanso_mac.py` 讀取 shared base triggers，從本機專案 triggers 排除同名項目；因此 `know;` / `cdknow;` 不會再被 `projects.yml` 蓋掉。
- **Air 結果**：`know; → knowledge-system`、`cdknow; → cd ~/Projects/knowledge-system` 已生效；canonical 與 repo seed hash 一致，LaunchAgent 最近一次執行 exit 0。全程用背景 CLI 驗證，未做會搶焦點的 GUI 輸入測試。 ^ck-mac-espanso-dropbox-1
