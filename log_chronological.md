# tools — 開發記錄
^ck-a77d40-0

## 2026-03-17（一）
^ck-1acc91-1

### 12:00 [NB] 初始建立 + espanso-projects 工具

- 建立 tools repo，定義 8 條建新工具的規則(README.md)
- 完成第一個工具 espanso(專案名稱快速輸入)
- 在 env.machines.md 記錄 Espanso 安裝，DT 待辦也記了 ^ck-c3b5b3-2

### 12:50 [NB] 定義新工具流程 + 基礎建設

- 討論新開工具的標準流程：先討論(痛點 → 方案比較 → 選定) → 再建置 → commit
- 建立 tools/CLAUDE.md：環境需求、新工具三階段流程、env.machines.md 更新時機
- 建立 tools/ROADMAP.md：用 Incubator 區放未成熟的想法，成熟後移入階段目標
- 建立 tools/log_chronological.md：tools 根目錄的開發記錄
- env.machines.md 更新規則：有新外部依賴才記，純用既有環境不用動 ^ck-48965d-3

### 13:23 [NB] espanso 大幅升級：後綴觸發 + 雙輸入法同步

- espanso-projects 改名為 espanso
- trigger 從前綴 `;esp` 改為後綴 `esp;`（跟無蝦米打法一致）
- 經多輪迭代：縮寫+多長度 → 最短2字母 → 最終簡化為一律前4字母（短key會干擾無蝦米）
- gen_espanso.py 同時寫入 Espanso yml 和無蝦米 liu.box，兩個輸入法模式都能快速輸入專案名
- 撞名規則：各管各的（無蝦米保留手動中文條目，Espanso 全部生成）
- liu.box 備份進 repo，與 Dropbox 雙向同步 ^ck-58b70f-4

### 13:31 [NB] liu-updater：時間字根自動更新

- 痛點：liu.box 裡的時間字根（年度、月份、季度）以前手動更新，放了四年沒改
- 建立 liu-updater 工具，一鍵更新所有時間字根
- 年度字根：LLY/LY/TY/NY/NNY（前年～後年）、TM（這個月）
- 季度字根：EQ/RQ/SQ/FQ（嘸蝦米數字 E=1 R=2 S=3 F=4）、ERQ（上半年）、ESQ（前三季累計）、QARP（年報）
- 臨近2季度原則：當季±1季年份明確，距離2季時 1Q↔3Q 明確、2Q↔4Q 模糊不帶年
- 一次性清理：刪掉過時的 `TD; TD-SCDMA` 條目 ^ck-7f41b0-5

## 2026-03-18（三）
^ck-8754a3-6

### 12:00 [NB] liu-updater 季度更新

- 手動跑 liu-updater，更新 liu.box 時間字根 ^ck-97b8b6-7

### 13:46 [NB] wifi-keepalive 開案：iPhone 熱點斷線自動重連

- 痛點：iPhone 個人熱點連 NB，30-60 分鐘自動斷線（iOS 省電機制已知問題）
- 方案討論：PowerShell vs Python → 選 PowerShell（零依賴、系統指令原生、不跨平台）
- 建立 wifi-keepalive 工具：keep-alive ping + 斷線自動重連 + CSV log
- 支援多 SSID（兩支 iPhone），斷線時優先重連最近用過的
- 設定直接寫腳本頂部變數（最簡單），log 用 CSV（最精簡）
- 實測發現問題：netsh 輸出 Unicode 右單引號（U+2019）被轉成 `?`，SSID 比對失敗
- 嘗試 Get-NetConnectionProfile 可保留 Unicode，待下次 session 繼續修正
- 建立 wifi-keepalive/ROADMAP.md：三階段（核心功能 → 穩定運行 → 觀察分析） ^ck-0e1982-8

## 2026-03-20（五）
^ck-7aedfb-9

### 21:58 [DESKTOP] espanso：liu.box 升為 single source of truth

- liu.box 手動區現在是 Espanso 和嘸蝦米的共用字串來源
- gen_espanso.py 讀 liu.box 手動條目 → 同時寫入 Espanso config 和 liu.box 自動區
- 以後只要改 liu.box 手動區，跑一次 gen_espanso.py 兩邊都更新
- 579 筆手動條目 + 24 筆專案 trigger，0 衝突 ^ck-7d9e0c-10

## 2026-03-21（六）
^ck-241edf-11

### 15:22 [DESKTOP] Dropbox 路徑改環境變數 + 首筆共用字串測試

- DESKTOP 的 Dropbox 在 D:\Dropbox，NB 在 %USERPROFILE%\Dropbox，寫死路徑會壞
- gen_espanso.py 改用 DROPBOX_PATH 環境變數，沒設時 fallback 讀 repo 備份
- DESKTOP 已設 `setx DROPBOX_PATH "D:\Dropbox"`，NB 待設
- 首筆共用字串測試：加入 OBS; Obsidian，確認嘸蝦米和 Espanso 兩邊都生效 ^ck-d2f0cf-12

## 2026-03-25（二）
^ck-fdcf62-13

### 05:50 [DESKTOP] espanso 與嘸蝦米分工：各管各的

- 發現 espanso 和嘸蝦米同時監聽鍵盤會打架：短 key（如 `i;`）搶先觸發、`word: true` 會吃字
- 嘗試過 `word: true`（吃字）、IME 偵測自動切換（防毒擋 C# interop）、最低長度門檻（workaround）
- 最終決策：espanso 只管專案 trigger，手動條目留給嘸蝦米，兩邊不重疊
- 關閉 espanso 的 Alt+Space 搜尋快捷鍵（default.yml 加 `search_shortcut: "off"`） ^ck-cb83dc-14

### 22:38 [DESKTOP] 停用 espanso，trigger 全部交給嘸蝦米

- espanso 和嘸蝦米兩套 low-level keyboard hook 並存，疑似造成系統不穩（視窗高速閃爍、無法操作、只能重開機）
- 問題在裝 espanso 之後才出現，重開機後仍會復發（espanso 有開機自啟）
- 決策：停用 espanso，所有 trigger 統一由嘸蝦米 liu.box 處理（ZZAUTO 區已有 26 個專案 trigger）
- 做了什麼：
  - 停止 espanso 服務
  - 刪除 Startup 資料夾的 espanso.lnk（不再開機自啟）
  - gen_espanso.py 移除 espanso 產出邏輯（generate_espanso()、import yaml、ESPANSO_MATCH），只更新 liu.box ^ck-a21b87-15

## 2026-04-18（六）
^ck-628110-16

### 19:15 [MAC-MINI] pinyin-drill v0.1.0 開案（階段目標 D）

**痛點**：Mac 原生拼音日常可用，但兩類場景卡：
1. 簡拼遇第二字裸母音（方案 fang-an）要用 apostrophe `f'an`，否則 `fa` 被解成單音節
2. n/ng 前後鼻音（台灣口音盲點），生/深、京/金常誤判

**設計決策**：
- 純英文輸入 + 字串比對（遊戲本身不碰 IME；練習前切 ABC 輸入法）
- accepted 清單以「Mac IME 真能出字」為準（curated 非規則推導）
- 時間當弱點訊號（對但慢 →×1.5 加權，錯 ×2，連續快對 ×0.7 淡出）
- 三類題庫分檔：apostrophe 詞、n/ng 字、n/ng 詞

**產出**：
- `pinyin-drill/drill.py` — Python 3.14 標準庫，無外部依賴（sqlite3 + json + time）
- `data/seed_apostrophe.json` 30 題、`seed_nng_chars.json` 56 題、`seed_nng_words.json` 35 題
- `--strict` flag：只接受 preferred 形式（練習模式）；預設寬鬆（accept 全部 IME-valid，實戰模式）
- SQLite 持久化統計（每題 hanzi/category/time_ms/correct/matched_preferred）

**迭代過程**（保留以供未來參考）：
1. 初版不含 jianpin accepted → 用戶抓到 `zf` for 政府 IME 吃但判錯 → 補 jianpin 到 33 個 nng-word items
2. 嘗試加 注音 feedback 當鷹架 → 用戶指出「多一層 translation 效率差」→ 還原到 pre-zhuyin 狀態當 v0.1.0 baseline
3. 規則分離：判定嚴格度從資料層搬到 `--strict` 模式 flag（遊戲規則 vs 題庫資料解耦）

**延伸討論**（不在 tools 專案範圍，記在此避免遺忘）：
- 同 session 討論輸入法主戰場，結論：**長期轉注音** — 母語層（無 translation）、跨裝置通用（iPhone/Mac/Win 內建）、容錯強（錯字仍可讀）、維護成本零
- 無蝦米不廢，降為 Windows 備援（主力舞台轉 Mac mini + iPhone 後時間占比本就下降）
- 小麥注音已 `brew install --cask mcbopomofo` 下載（安裝檔在 `/opt/homebrew/Caskroom/mcbopomofo/3.0/`），用戶未來自行 `open` 安裝
- 注音鍵位練習用 World of Keyboards + typing.tw，不自建

**pinyin-drill 的新定位**：這個 session 走一圈後，pinyin-drill 從「主力工具」降為「備援 + 實驗性小品」。Mac 主力轉注音後使用頻率會降，但作為完整 MVP 保留（跨裝置拼音場景仍有用，例如朋友電腦或舊習慣回補）。 ^ck-26a2c3-17

## 2026-04-19（日）
^ck-565ca7-18

### 13:30 [MAC-MINI] pinyin-drill v0.1.2 — feedback 視覺化 + 雙軌正確率

錯題改 side-by-side 對照（`你打 [X] → 正解 [Y] (情境)`），每題秀本局/全局正確率，session 結算加 filtered 全局累計。不改核心行為、只改顯示。用戶「故意錯會污染」的疑慮由雙軌透明度滿足，不加 undo/skip（retrieval practice 原則）。詳見 pinyin-drill/log_chronological.md。

## 2026-04-20（一）

### 15:30 [MAC-MINI] pinyin-drill 實測 + n/ng drill 價值框架校準

**實測數據**
- 連續多輪 drill_nng，80 題累計 58 對 = 72.5%
- 最弱 cluster：yin/ying（影/英/引 三字均錯）
- 系統權重正在自動強化 yin-ying 這組

**框架校準**（與用戶討論得出）
初版我評估「n/ng 加強對日常 jianpin 打字只有 ~10-15% 影響」→ **低估**。用戶指出兩個我漏掉的成本：
1. **不確定性 flow 殺手**：每次 n/ng 猶豫破壞寫作 flow，損失 >> 多打幾鍵
2. **候選字掃描成本**：jianpin 模式候選字多，n/ng 不熟 = 讀每個候選而非 pattern-match

修正結論：n/ng drill 不只是「拼音基本盤」，是**消除整個輸入 pipeline 的不確定性**（打字+候選+讀拼音+mental lookup 四關都有收益）。

**jianpin 長度甜蜜點**（討論產出，供未來參考）
- 2 字詞 jianpin：高頻詞 OK，低頻詞撞音 → 自訂詞彙補強
- 4-5 字 jianpin：context 鎖定最佳
- 6+ 字純首字母句：Mac 內建 IME 支援弱（Windows 才強）→ 改 chunk 分段
- 前字全拼 + 後字簡拼：實用混合策略

**意外副作用**
我 smoke test 時多次 `rm -f stats.sqlite` 沒意識到會消用戶真實紀錄。這次運氣好只吃掉部分（stats.sqlite 被 gitignore，用戶持續使用下有自恢復）。規則更新：**絕不 rm stats.sqlite，測試需要用 `--db /tmp/test.sqlite` 或臨時目錄**。

**未做（留給未來）**
- 自訂詞彙 guide（建議用戶做 30 個高頻詞）— 屬個人工作流，不進 repo
- 4-5 字詞題庫擴充 — 等 n/ng 單字穩定 80%+ 再議
- 「近 20 題」正確率顯示（替代全期累計）— 若用戶要求再加 ^ck-1a1b8b-19

### 13:01 [MAC-MINI] pinyin-drill v0.1.1 — drill_nng.py 聚焦變體

用戶試用超注音期間仍想補拼音 n/ng 知識缺口。加了 `drill_nng.py` 薄包裝，固定 `--category nng-char --strict`，只暴露 count/stats。OCP：不改 drill.py 核心，用 wrapper 擴充聚焦場景。VERSION 0.1.0 → 0.1.1。詳見 pinyin-drill/log_chronological.md。 ^ck-27c8f4-20
