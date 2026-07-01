// ocr_clip — 讀剪貼簿圖片 → Vision OCR → 聰明拆換行 → 寫回剪貼簿
//
// 設計重點：
//  1. usesLanguageCorrection = false
//     終端指令 / token / 路徑不是自然語言，開語言修正會把 `ls -la`、base64、
//     旗標亂改。OCR 要的是「照抄」不是「讀懂」。
//  2. 座標拆換行（dewrap）
//     終端把超長字串硬折成多行時，被折的那一行右緣會頂到畫面右側。
//     某一行 boundingBox 的右緣 (maxX) >= threshold → 視為螢幕硬折，
//     下一行直接接上去、不插任何分隔（終端在字元格中斷、斷點無空白）。
//     右緣沒到底就結束 → 真換行，保留 \n。
//
// 用法：
//   ocr_clip                 預設 threshold 0.92，結果寫回剪貼簿並印到 stdout
//   ocr_clip --threshold 0.9 調右緣判定門檻（越小越容易判定為「折行」）
//   ocr_clip --no-dewrap     關閉拆換行，逐行保留（debug 用）
//   ocr_clip -q              安靜模式，不印 stdout

import Foundation
import AppKit
import Vision

// ---- 參數 ----
var marginThreshold = 0.92   // 行右緣 >= 此比例 → 判定為螢幕硬折
var dewrap = true
var quiet = false

var argi = 1
let argv = CommandLine.arguments
while argi < argv.count {
    switch argv[argi] {
    case "--threshold":
        argi += 1
        if argi < argv.count, let v = Double(argv[argi]) { marginThreshold = v }
    case "--no-dewrap":
        dewrap = false
    case "-q", "--quiet":
        quiet = true
    case "-h", "--help":
        print("usage: ocr_clip [--threshold 0.92] [--no-dewrap] [-q]")
        exit(0)
    default:
        break
    }
    argi += 1
}

func die(_ msg: String) -> Never {
    FileHandle.standardError.write(Data((msg + "\n").utf8))
    exit(1)
}

// ---- 從剪貼簿取圖 ----
let pb = NSPasteboard.general
guard let nsimg = NSImage(pasteboard: pb),
      let tiff = nsimg.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cg = bitmap.cgImage else {
    die("ocr_clip: 剪貼簿裡沒有圖片（先截圖到剪貼簿：⌃⇧⌘4 框選）")
}

// ---- Vision OCR — Algorithm G: 2x upscale + 語言自動偵測 ----
// 盲測 round 2（n=240，真實 Menlo 字型）：upscale 讓 Vision 更容易分辨 l vs 1。
// l1_rate 0.030% vs H 0.049%（-40%）；terminal CER 0.0203 vs H 0.0236；
// 速度 ~181ms vs H ~242ms；單 pass、無 CJK 分支、code 最簡單。
//
// 語言設定（2026-07-01 n=1000 真實指令盲測補測）：單純把 zh-Hant 加進
// recognitionLanguages 列表（不論排哪個順序）不會做真正的逐區域雙語混合辨識——
// Vision 幾乎只吃列表第一個語言，第二個形同無效（en-US 優先時結果跟純 en-US
// 逐位元組相同；zh-Hant 優先時中文辨識變好但 ASCII CER 從 1.73% 惡化到 4.11%，
// 引號/括號被「修正」成全形）。真正有效的是 `automaticallyDetectsLanguage = true`
// ——這會讓 Vision 逐區域自動判斷語言，而非固定套用列表順序。額外測過拿掉
// `recognitionLanguages` 裡的 zh-Hant（只留 en-US + automaticallyDetectsLanguage）
// 跟保留 zh-Hant 的版本在 n=1000 上逐位元組完全相同——證實 automaticallyDetectsLanguage
// 開啟時，recognitionLanguages 列表內容不影響結果（Spock 審查要求驗證的假設），
// 所以只留 en-US，不留形同虛設的 zh-Hant。n=1000 結果：整體加權 CER 3.77%→3.02%
// （-20%）、中文 CER 9.93%→6.83%（-31%）、ASCII CER 幾乎持平（1.73%→1.76%），
// 時間成本 +10~15ms（~170ms→~185ms）。
func upscale2x(_ src: CGImage) -> CGImage {
    let w = src.width * 2; let h = src.height * 2
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8,
        bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.interpolationQuality = .high
    ctx.draw(src, in: CGRect(x: 0, y: 0, width: w, height: h))
    return ctx.makeImage()!
}

let cgUp = upscale2x(cg)
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = ["en-US"]
request.automaticallyDetectsLanguage = true
try? VNImageRequestHandler(cgImage: cgUp, options: [:]).perform([request])

guard let results = request.results, !results.isEmpty else {
    die("ocr_clip: 圖片裡認不出文字")
}

// ---- 列分桶（同一視覺列常被 Vision 拆成多段 observation，例如 `&&`、引號、redirect
// 前後的間隙）----
// 單純按 maxY 排序時，同列分段的 maxY 幾乎相同、排序不穩定，會被當成獨立列、
// 順序錯亂（n=1000 真實指令盲測撞到：10.7% 案例同列被拆兩段，平均 CER 飆到 20%）。
// 先用 maxY 容許誤差分桶成「列」，桶內再依 minX 由左到右排，桶與桶之間維持由上到下。
let avgH = results.map { $0.boundingBox.height }.reduce(0, +) / CGFloat(results.count)
let yEps = avgH * 0.6

let sortedByY = results.sorted { $0.boundingBox.maxY > $1.boundingBox.maxY }
var rows: [[VNRecognizedTextObservation]] = []
for obs in sortedByY {
    if let anchor = rows.last?.first, abs(anchor.boundingBox.maxY - obs.boundingBox.maxY) <= yEps {
        rows[rows.count - 1].append(obs)
    } else {
        rows.append([obs])
    }
}
for i in rows.indices {
    rows[i].sort { $0.boundingBox.minX < $1.boundingBox.minX }
}
// 辨識不出文字的 observation（topCandidates 為 nil，少見但真的會發生）整個濾掉，
// 不留它的幾何位置去影響分隔判定——舊版 `guard ... else { continue }` 就是這個語意。
// 用逐 observation 粒度過濾（而非只濾整列全 nil 的情況）：同一列裡夾雜 textless
// observation 時，它原本仍會被 `row.max(maxX)` 採計、左右該列自己的 wrap 判定；
// 過濾乾淨才能保證每列的幾何完全由「真的有輸出文字」的 observation 決定。
rows = rows.map { $0.filter { $0.topCandidates(1).first?.string != nil } }.filter { !$0.isEmpty }

// ---- 組字 + 拆換行 ----
// 同列分段之間用空白接（Vision 切開處本來就是視覺間隙）；
// 列與列之間沿用原 dewrap 判定：該列最右段 maxX 頂到右緣 → 螢幕硬折，直接接上不插分隔。
var out = ""
for (idx, row) in rows.enumerated() {
    let rowText = row.compactMap { $0.topCandidates(1).first?.string }.joined(separator: " ")
    out += rowText
    if idx == rows.count - 1 { break }
    let rightmost = row.max { $0.boundingBox.maxX < $1.boundingBox.maxX }!
    let wrapped = dewrap && rightmost.boundingBox.maxX >= marginThreshold
    out += wrapped ? "" : "\n"
}

// ---- Post-OCR: 全形標點 → 半形 ----
// automaticallyDetectsLanguage 逐區域判斷語言時，偶爾會把純 ASCII 標點誤判成中文語境、
// 吐出全形字元（"；"、"（）"、"？" 等），違反本工具「照抄不修正」的設計初衷。
// n=1000 量測過這個 map 的淨效果：47 案例變好、3 案例略微變差（都是本來 CER 就很高、
// 已經救不回的行），加權 CER 再降 0.0302→0.0294，值得做。
// 範圍只涵蓋標點、不含全形數字/字母（０-９、Ａ-Ｚ）：n=1000 同一批語料裡完全沒出現
// 全形數字/字母誤判（0/1000），資料不支持先擴大範圍；之後真的撞到再補。
// 順序：必須排在 dash-flag fix 之前——後者假設輸入已是半形 ASCII，若破折號被誤判成
// 全形 `－` 才做 dash-flag regex，會比對不到、永久錯過修正機會（Spock 審查抓到）。
let fullwidthToHalfwidth: [Character: Character] = [
    "！": "!", "＃": "#", "＄": "$", "％": "%", "＆": "&", "（": "(", "）": ")",
    "＊": "*", "＋": "+", "，": ",", "－": "-", "．": ".", "／": "/",
    "：": ":", "；": ";", "＜": "<", "＝": "=", "＞": ">", "？": "?", "＠": "@",
    "［": "[", "＼": "\\", "］": "]", "＾": "^", "＿": "_", "｀": "`",
    "｛": "{", "｜": "|", "｝": "}", "～": "~", "。": ".", "、": ",",
]
out = String(out.map { fullwidthToHalfwidth[$0] ?? $0 })

// ---- Post-OCR: dash-flag l/1 fix ----
// `-1` 緊跟字母（-1h, -1rth）必是 `-l`；獨立 `-1`（ls -1, head -1）保留不動。
out = out.replacingOccurrences(of: #"-1([a-z])"#, with: "-l$1", options: .regularExpression)

// ---- 寫回剪貼簿 ----
pb.clearContents()
pb.setString(out, forType: .string)

if !quiet { print(out) }
