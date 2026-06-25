# ocr-clip — 截圖 OCR，剪貼簿原地換成文字

剪貼簿裡有截圖時按熱鍵 → 用 macOS Vision 辨識 → **聰明拆換行** → 剪貼簿原地換成可貼的純文字。專為「終端機指令截圖」設計：螢幕上被硬折成多行的超長字串（token / hash / URL）會自動接回同一行。

- **離線**：用 Apple Vision framework（Live Text 同一顆引擎），不連網、不上傳。
- **照抄不修正**：`usesLanguageCorrection = false`，不會把 `ls -la`、base64、旗標「修正」成自然語言。
- **繁中 + 英文**：`recognitionLanguages = ["zh-Hant", "en-US"]`（順序=優先權）。中文無空格，跟「折行直接接上不插分隔」天生相容。
  - 注意：開中文後 Vision 在中文模式偶爾把半形標點吐成全形（`:`→`：`、`()`→`（）`），純中文無感，但**純終端指令截圖**遇到時可能貼出去跑不動。真實清晰截圖通常不會發生；若常踩可再加「終端模式」旗標把全形標點轉回半形。
- **平台**：macOS（需 Swift 工具鏈編譯）。已套用：Mac mini ✅、Air ✅（各機 `git pull` 後跑一次 `build.sh` 編本機二進位，binary 不進版控）。

## 聰明拆換行（dewrap）

終端把一行超長字串硬折成多行時，被折的那行右緣會頂到畫面右側。判斷邏輯：

- 某行 boundingBox 右緣 `maxX >= threshold`（預設 0.92）→ 視為螢幕硬折 → 下一行**直接接上、不插分隔**（終端在字元格中斷、斷點無空白）。
- 右緣沒到底就結束 → 真換行，保留 `\n`。

截圖請**只框終端區域**（不要整個螢幕），否則文字右緣離畫面右側太遠會判不出折行。判不準時調 `--threshold`（越小越容易判定為折行）。

## 檔案

| 路徑 | 說明 |
|------|------|
| `scripts/ocr_clip.swift` | 主程式原始碼 |
| `scripts/build.sh` | 編譯成 `ocr_clip` 二進位（gitignore，不進版控） |
| `scripts/scratch/make_test_image.swift` | 測試用：產「折行+真換行」測試圖丟剪貼簿 |

## 怎麼跑

```bash
# 1. 編譯（換機 / git pull 後跑一次）
bash scripts/build.sh            # 產出 ./ocr_clip

# 2. 手動測（剪貼簿要先有截圖）
./ocr_clip                       # 辨識 → 寫回剪貼簿 → 印 stdout
./ocr_clip --threshold 0.9       # 折行判太鬆/太緊時調門檻
./ocr_clip --no-dewrap           # 逐行保留（debug）
./ocr_clip -q                    # 不印 stdout
```

## 綁熱鍵 ⌘⇧2（一次性，用 macOS「捷徑」App）

機器沒裝 Hammerspoon/skhd，用系統內建「捷徑」當觸發殼，零額外依賴：

1. 開「捷徑」App → 新增捷徑，命名 `OCR Clipboard`。
2. 加一個「**執行 Shell 指令搜尋程式**」動作，內容填二進位絕對路徑：
   `/Users/ianchang/Projects/tools/ocr-clip/ocr_clip`
3. 捷徑詳細資料（ⓘ）→「**加入鍵盤快速鍵**」→ 按 `⌘⇧2`。
4. 第一次觸發時系統會問是否允許捷徑跑這支程式，按允許。

之後流程：`⌃⇧⌘4` 框選截圖到剪貼簿 → `⌘⇧2` → 剪貼簿已是辨識文字，直接 `⌘V`。

> ⚠️ `⌘⇧2` 預設沒被系統佔用（截圖是 ⌘⇧3/4/5）。若與其他 App 衝突，改綁別的鍵。
