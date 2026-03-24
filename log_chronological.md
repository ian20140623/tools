# tools — 開發記錄

## 2026-03-17（一）

### 12:00 [NB] 初始建立 + espanso-projects 工具

- 建立 tools repo，定義 8 條建新工具的規則(README.md)
- 完成第一個工具 espanso(專案名稱快速輸入)
- 在 env.machines.md 記錄 Espanso 安裝，DT 待辦也記了

### 12:50 [NB] 定義新工具流程 + 基礎建設

- 討論新開工具的標準流程：先討論(痛點 → 方案比較 → 選定) → 再建置 → commit
- 建立 tools/CLAUDE.md：環境需求、新工具三階段流程、env.machines.md 更新時機
- 建立 tools/ROADMAP.md：用 Incubator 區放未成熟的想法，成熟後移入階段目標
- 建立 tools/log_chronological.md：tools 根目錄的開發記錄
- env.machines.md 更新規則：有新外部依賴才記，純用既有環境不用動

### 13:23 [NB] espanso 大幅升級：後綴觸發 + 雙輸入法同步

- espanso-projects 改名為 espanso
- trigger 從前綴 `;esp` 改為後綴 `esp;`（跟無蝦米打法一致）
- 經多輪迭代：縮寫+多長度 → 最短2字母 → 最終簡化為一律前4字母（短key會干擾無蝦米）
- gen_espanso.py 同時寫入 Espanso yml 和無蝦米 liu.box，兩個輸入法模式都能快速輸入專案名
- 撞名規則：各管各的（無蝦米保留手動中文條目，Espanso 全部生成）
- liu.box 備份進 repo，與 Dropbox 雙向同步

### 13:31 [NB] liu-updater：時間字根自動更新

- 痛點：liu.box 裡的時間字根（年度、月份、季度）以前手動更新，放了四年沒改
- 建立 liu-updater 工具，一鍵更新所有時間字根
- 年度字根：LLY/LY/TY/NY/NNY（前年～後年）、TM（這個月）
- 季度字根：EQ/RQ/SQ/FQ（嘸蝦米數字 E=1 R=2 S=3 F=4）、ERQ（上半年）、ESQ（前三季累計）、QARP（年報）
- 臨近2季度原則：當季±1季年份明確，距離2季時 1Q↔3Q 明確、2Q↔4Q 模糊不帶年
- 一次性清理：刪掉過時的 `TD; TD-SCDMA` 條目

## 2026-03-18（三）

### 12:00 [NB] liu-updater 季度更新

- 手動跑 liu-updater，更新 liu.box 時間字根

### 13:46 [NB] wifi-keepalive 開案：iPhone 熱點斷線自動重連

- 痛點：iPhone 個人熱點連 NB，30-60 分鐘自動斷線（iOS 省電機制已知問題）
- 方案討論：PowerShell vs Python → 選 PowerShell（零依賴、系統指令原生、不跨平台）
- 建立 wifi-keepalive 工具：keep-alive ping + 斷線自動重連 + CSV log
- 支援多 SSID（兩支 iPhone），斷線時優先重連最近用過的
- 設定直接寫腳本頂部變數（最簡單），log 用 CSV（最精簡）
- 實測發現問題：netsh 輸出 Unicode 右單引號（U+2019）被轉成 `?`，SSID 比對失敗
- 嘗試 Get-NetConnectionProfile 可保留 Unicode，待下次 session 繼續修正
- 建立 wifi-keepalive/ROADMAP.md：三階段（核心功能 → 穩定運行 → 觀察分析）

## 2026-03-20（五）

### 21:58 [DESKTOP] espanso：liu.box 升為 single source of truth

- liu.box 手動區現在是 Espanso 和嘸蝦米的共用字串來源
- gen_espanso.py 讀 liu.box 手動條目 → 同時寫入 Espanso config 和 liu.box 自動區
- 以後只要改 liu.box 手動區，跑一次 gen_espanso.py 兩邊都更新
- 579 筆手動條目 + 24 筆專案 trigger，0 衝突

## 2026-03-21（六）

### 15:22 [DESKTOP] Dropbox 路徑改環境變數 + 首筆共用字串測試

- DESKTOP 的 Dropbox 在 D:\Dropbox，NB 在 %USERPROFILE%\Dropbox，寫死路徑會壞
- gen_espanso.py 改用 DROPBOX_PATH 環境變數，沒設時 fallback 讀 repo 備份
- DESKTOP 已設 `setx DROPBOX_PATH "D:\Dropbox"`，NB 待設
- 首筆共用字串測試：加入 OBS; Obsidian，確認嘸蝦米和 Espanso 兩邊都生效

## 2026-03-25（二）

### 05:50 [DESKTOP] espanso 與嘸蝦米分工：各管各的

- 發現 espanso 和嘸蝦米同時監聽鍵盤會打架：短 key（如 `i;`）搶先觸發、`word: true` 會吃字
- 嘗試過 `word: true`（吃字）、IME 偵測自動切換（防毒擋 C# interop）、最低長度門檻（workaround）
- 最終決策：espanso 只管專案 trigger，手動條目留給嘸蝦米，兩邊不重疊
- 關閉 espanso 的 Alt+Space 搜尋快捷鍵（default.yml 加 `search_shortcut: "off"`）
