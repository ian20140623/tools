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

// ---- Vision OCR — Algorithm G: 2x upscale + en-US only ----
// 盲測 round 2（n=240，真實 Menlo 字型）：upscale 讓 Vision 更容易分辨 l vs 1。
// l1_rate 0.030% vs H 0.049%（-40%）；terminal CER 0.0203 vs H 0.0236；
// 速度 ~181ms vs H ~242ms；單 pass、無 CJK 分支、code 最簡單。
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

// ---- Post-OCR: dash-flag l/1 fix ----
// `-1` 緊跟字母（-1h, -1rth）必是 `-l`；獨立 `-1`（ls -1, head -1）保留不動。
out = out.replacingOccurrences(of: #"-1([a-z])"#, with: "-l$1", options: .regularExpression)

// ---- 寫回剪貼簿 ----
pb.clearContents()
pb.setString(out, forType: .string)

if !quiet { print(out) }
