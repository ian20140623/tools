# espanso — 開發記錄
^ck-b6a511-0

## 2026-03-17（一）
^ck-bdc1e1-1

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
^ck-c78f33-6

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
