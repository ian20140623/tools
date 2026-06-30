# log — ocr-clip

### 07:20 [Mac mini] v0.2.2 — EES 抓出 v0.2.1 的 regression：空列污染分隔判定
- Eagle Eye + Spock 對 v0.2.1（commit d59d0d4）做 worktree 隔離審查。Spock 第一輪 CLEAR；
  Eagle Eye 更完整的正式報告抓到 2 個真的問題：
  1. id=0400（CJK 混雜行）同列拆段插入多餘空格——跟 Spock 的 SHOULD FIX 同一個問題
     （Vision 切開處不保證是真的視覺間隙），CER 影響極小（+0.004），跟 gap-aware
     join 一起留到下一輪、用 n=1000 harness 量過再動，這次不碰。
  2. **真 regression**：v0.2.1 把全部 observation 分桶成 row 之後，如果整列
     `topCandidates` 全 nil（少見但真的會發生），舊版 `guard...continue` 會讓該列完全
     消失、不影響鄰列分隔；新版該空列仍佔一個 row slot、用自己的幾何位置決定要不要插
     `\n`，嚴重情況會把分隔符整個吃掉、無聲黏合兩個無關列。
- 修復：先用 row-granularity filter（整列全 nil 才丟），重編 + n=1000 回歸確認零
  regression（mean CER 仍 3.42%、無 case 變糟）。Spock 複查時指出殘留語意分歧：部分列
  裡夾雜 textless observation 時，那顆 nil 元素的幾何仍會被 `row.max(maxX)` 採計、
  影響該列自己的 wrap 判定（同一個 class 的 ghost-geometry，從 inter-row 降到
  intra-row）。改成 element-granularity filter（`rows.map { filter nil }.filter
  { !isEmpty }`）一次徹底解決，不留任何 trade-off。重編 + n=1000 最終回歸：數字與
  row-filter 版本完全一致（mean 3.42%、weighted 3.77%、exact 20.5%、max 0.44），
  零 regression。
- 流程教訓：worktree 隔離審查時，agent 看到的程式碼是「分支當下 commit」，working tree
  的未 commit 改動不會帶過去——這次 Spock 第一輪因此審到舊版而判斷「找不到 diff」，
  後來才確認是 worktree 沒同步、不是 agent 出錯。送審前先 commit 是正確順序。

### 06:50 [Mac mini] v0.2.1 — n=1000 真實指令盲測揭露列序錯亂 bug + 修復
- 痛點：之前 Algorithm G 的盲測（n=240）用合成 token 字串，沒測過真實終端指令常見的
  `&&`、引號、redirect 組合。想知道在真實使用情境下準確率到底如何。
- Dataset：從 `~/.claude/projects/*/*.jsonl` 撈過去所有 session 裡 Claude 開過的 Bash
  tool_use 指令，去重、篩單行 3–300 字元，n=9931 取 1000 抽樣。原本想真的開 Terminal
  截圖最擬真，但卡在 Screen Recording 權限（screencapture 對這個 tmux 託管的呼叫鏈拿不到
  授權，需要使用者手動到系統設定開），改用合成圖：抓 Terminal.app 實際設定（Clear Dark
  profile）查出字體是 SF Mono、不是先前用的 Menlo，改用
  `NSFont.monospacedSystemFont`（取得 SF Mono 的公開 API，`.SFMono-Regular` 私有字型名
  直接用會被 CoreText 靜默置換成 Times New Roman）、固定 100 欄寬硬折行。
- 發現：n=1000 平均 CER 5.19%。但 worst-case 分析發現主因不是認錯字——10.7% 案例
  Vision 把同一視覺列拆成多段 observation（`&&`/引號/redirect 前後間隙造成），原本
  `ocr_clip.swift` 只用 `boundingBox.maxY` 排序，同列分段 maxY 幾乎相同、排序不穩定，
  加上右緣判斷誤判成真換行，導致行序顛倒拼接。這 10.7% 案例平均 CER 20%，貢獻全部
  誤差的 41%。
- 修復：排序邏輯改兩段式——先按 `maxY` 容許誤差（行高的 0.6 倍）分桶成「列」，桶內再依
  `minX` 左到右排序，桶間沿用原 dewrap 右緣判斷。重編後同一份 n=1000 重測：平均 CER
  5.19%→3.42%（-34%）、字元加權 CER 5.16%→3.77%、最慘案例 CER 0.90→0.44、完全對
  19.4%→20.5%。
- 殘留問題（待決定要不要追）：拆 ASCII vs 含中文兩組，ASCII-only CER 僅 1.73%（比原本
  Menlo 合成測試的 2.03% 還低），但含中文指令（vault 路徑/grep 中文關鍵字，佔樣本
  20.5%）CER 高達 10.0%，貢獻六成以上剩餘誤差。`en-US`-only 是 Algorithm G 既有取捨
  （避免犧牲 l/1 準確率），中文混排場景目前沒優化，是否值得重新盲測雙語言留待下一輪。

### 21:10 [Mac mini] v0.1.0 開案 — 截圖 OCR + 座標拆換行
- 痛點：終端機指令截圖，超長字串（token/hash/URL）在螢幕上被硬折成多行，貼出來帶一堆假換行；想按熱鍵就把剪貼簿圖片換成「正確不折行」的純文字。
- 方案比較：
  - macOS「捷徑」內建 `Extract Text from Image`（零程式碼）→ 引擎一樣強，但只能無腦刪所有換行，遇多行指令會黏錯。
  - Swift CLI + Vision `VNRecognizeTextRequest` → 拿得到每行 boundingBox，能做座標判定的聰明拆換行。**選此**（Sir 確認截圖常是「混合，含多行指令」）。
- 設計決策：
  - `usesLanguageCorrection = false` — 終端指令不是自然語言，開修正會亂改 `ls -la`/base64/旗標。OCR 要照抄不要讀懂。
  - dewrap：行右緣 `maxX >= 0.92` 視為螢幕硬折 → 下一行直接接上不插分隔；右緣沒到底 → 真換行保留。
  - 語言：開案先鎖 `en-US`；同 session 加 `zh-Hant` 並存（Sir 實測中文沒出來 → 補上），`.accurate`。已知權衡：中文模式偶吐全形標點，純指令截圖可能受影響，待實測決定要不要加終端模式旗標。
- 熱鍵：機器無 Hammerspoon/skhd，用系統「捷徑」綁 ⌘⇧2 當觸發殼（零依賴）。core 是 Swift binary，捷徑只是殼。
- 實測：自製測試圖（line1 撐到右緣 + line2 續行 + line3 獨立指令）→ ocr_clip 正確把 line1+line2 黏成一行、line3 保留新行，剪貼簿原地換成文字。端到端通過。
- 環境：Swift 6.3.2（Command Line Tools）；macOS 26.5.1。二進位 gitignore，換機跑 `bash scripts/build.sh`。

### 09:55 [Air] 安裝上 Air — git pull 帶原始碼、本機 build + 綁 ⌘⇧2
- open-session 的 git pull 帶入 mini 的 `89f5166` 原始碼；binary gitignore 不同步，`bash scripts/build.sh` 用 Air 的 `swiftc` 6.3.1 本機編出 `ocr_clip`（89K）。
- 實測：剪貼簿原有截圖被正確 OCR、dewrap 折行接對、寫回剪貼簿。
- 熱鍵：用「捷徑」App 建 `OCR Clipboard`（執行 Shell 指令 → binary 絕對路徑）綁 ⌘⇧2，捷徑無存檔鈕、關視窗自動存。
- 無新外部依賴（swiftc 既有），env.machines.md 不動。README「已套用」加 Air ✅。
