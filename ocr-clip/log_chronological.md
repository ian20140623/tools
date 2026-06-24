# log — ocr-clip

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
