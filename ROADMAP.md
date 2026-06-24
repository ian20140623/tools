# ROADMAP — tools
^ck-97a6ad-0 ^ck-0ba9d4-0

## 痛點

跨專案重複操作耗時，手動做容易出錯或遺漏。需要一組小工具來自動化這些日常瑣事。 ^ck-15316d-1

## 理想功能

- 常用操作一鍵完成，不用記指令
- 工具跨機器可用，裝好就能跑
- 新工具有標準流程，不用每次從零想 ^ck-6d51b3-2

## 階段目標

- [x] A. espanso — 專案名稱快速輸入（Windows：無蝦米 liu.box；Mac：espanso match YAML 直接展開，gen_espanso_mac.py，2026-06-08）
- [x] B. liu-updater — liu.box 時間字根自動更新（年度 + 季度，臨近2季度原則）
- [ ] C. wifi-keepalive — iPhone 熱點 keep-alive + 斷線自動重連（PowerShell，僅 NB）
- [ ] D. pinyin-drill — Mac 拼音練習遊戲（Python，Mac mini 本機，純英文輸入判定）
  - 痛點：Mac 原生拼音想用順，但簡拼遇裸母音第二字（方案 f'an）要靠 apostrophe；n/ng 前後鼻音常打錯
  - 設計：純英文輸入 + 字串比對（遊戲本身不碰 IME），accepted 清單以「Mac IME 真能出字」為準
  - 三類題：apostrophe 反射（詞）、n/ng 辨識（字）、n/ng 辨識（詞）
  - 核心機制：時間也當弱點訊號（對但慢 → 加權重出），per-tag 追蹤最弱類型
  - 技術：Python 3.14 標準庫（sqlite3 + json + time）、ANSI CLI，無外部依賴 ^ck-1c3b69-3
- [x] E. cco — 手機一鍵開 repo session（bash + tmux，Mac mini，2026-06-20）
  - 痛點：人在手機上用 SSH 進 mini，不想小螢幕手打 `tmux new -s … -c …` + 起 claude + 跑 open-session
  - 設計：`cco <repo> [name]` create-or-attach tmux + 自動 `claude "/open-session"`；idempotent，`cco`/`cco -k` 輔助
  - 手機端零打字靠 SSH app snippet / host 啟動指令 / Apple Shortcuts（待定 app 給確切設定）
- [x] F. ocr-clip — 截圖 OCR 換剪貼簿（Swift + Vision，Mac mini，2026-06-24）
  - 痛點：終端指令截圖，超長字串（token/hash/URL）在螢幕上被硬折成多行，貼出來帶假換行
  - 設計：剪貼簿圖 → Vision OCR（離線、`usesLanguageCorrection=false` 照抄不修正）→ 座標拆換行 → 原地換回剪貼簿
  - 拆換行：行右緣 maxX≥0.92 視為螢幕硬折→接上一行；沒到底→真換行
  - 熱鍵 ⌘⇧2：無 Hammerspoon/skhd，用系統「捷徑」綁 Run Shell（一次性 GUI 設定）
  - 技術：Swift 6.3.2 + Vision framework，二進位 gitignore，換機跑 build.sh

## Incubator

*還在想的工具點子，經過討論後移入階段目標。*

- ~~**單一來源架構**~~ — ✅ 已完成（2026-03-20）。liu.box 手動區是 single source of truth，gen_espanso.py 同時寫 Espanso config 和 liu.box
- **Espanso + liu.box 同步腳本** — 自動化 Dropbox ↔ repo 備份流程，手動改 liu.box 後一鍵同步回 repo ^ck-33ff3b-4

## 現況

A、B、E、F 完成。C 建置中（腳本完成，待實測）。D 開案中（Mac mini 本機小工具，跟其他專案無連動）。tools 基礎建設(README 規則、CLAUDE.md 流程、ROADMAP)已建立。liu.box 已備份進 repo。 ^ck-3c8342-5
