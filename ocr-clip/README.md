# ocr-clip — 截圖 OCR，剪貼簿原地換成文字

剪貼簿裡有截圖時按熱鍵 → 用 macOS Vision 辨識 → **聰明拆換行** → 剪貼簿原地換成可貼的純文字。專為「終端機指令截圖」設計：螢幕上被硬折成多行的超長字串（token / hash / URL）會自動接回同一行。

- **離線**：用 Apple Vision framework（Live Text 同一顆引擎），不連網、不上傳。
- **照抄不修正**：`usesLanguageCorrection = false`，不會把 `ls -la`、base64、旗標「修正」成自然語言。
- **Algorithm G**（2026-07-01 盲測 n=240 定案）：2x upscale + 語言自動偵測 + dash-flag/全形標點 post-fix。
  - 2x 放大讓 Vision 更容易區分 `l` vs `1`（l/1 混淆率 0.020%，比原始算法 -60%）。
  - Post-fix：`-1x`（-1 緊跟字母）自動修成 `-lx`，獨立 `-1`（`ls -1`、`head -1`）保留不動。
  - **列分桶排序**（2026-07-01 v0.2.1，n=1000 真實指令盲測補修）：單純按 `maxY` 排序時，
    同一視覺列被 Vision 拆成多段 observation（常見於 `&&`、引號、redirect 前後的間隙）會
    順序錯亂；改成先按 `maxY` 容許誤差分桶成列、桶內再依 `minX` 左到右排序。修後 n=1000
    平均 CER 5.19%→3.42%、最慘案例 CER 0.90→0.44。v0.2.2 補修同批 EES 審查抓到的空列
    regression（辨識不出文字的 observation 仍會污染鄰列分隔判定）。
  - **語言自動偵測**（2026-07-01 v0.3.0）：單純把 `zh-Hant` 加進 `recognitionLanguages`
    列表不會做真正逐區域雙語辨識——Vision 幾乎只吃列表第一個語言，第二個形同無效；
    真正有效的是 `automaticallyDetectsLanguage = true`，讓 Vision 逐區域自動判斷語言。
    n=1000 真實指令盲測：整體加權 CER 3.77%→2.94%（-22%）、中文 CER 9.93%→6.56%（-34%）、
    ASCII CER 幾乎持平（1.73%→1.75%），時間成本 +10~15ms。副作用：自動偵測偶爾誤觸發
    zh-Hant、把 ASCII 標點吐成全形（`；`、`（）`、`？` 等），加一組全形→半形 post-fix
    對沖（n=1000 量測：47 案例變好、3 案例微幅變差，淨值再降 CER 0.0302→0.0294）。
  - **v0.3.1**（EES 審查 v0.3.0 補修）：全形→半形 post-fix 移到 dash-flag 修正**之前**
    （若破折號被誤判成全形 `－`，dash-flag regex 只認半形、順序顛倒會永久錯過修正機會）；
    補測後確認 `recognitionLanguages` 裡的 `zh-Hant` 在 `automaticallyDetectsLanguage=true`
    時完全不影響結果（n=1000 逐位元組相同），清掉這個死設定、只留 `["en-US"]`。
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
