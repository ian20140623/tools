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

// ---- Vision OCR ----
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false      // 照抄，不要修正終端指令
request.recognitionLanguages = ["zh-Hant", "en-US"]   // 繁中 + 英文，順序=優先權

let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([request])
} catch {
    die("ocr_clip: OCR 失敗 — \(error.localizedDescription)")
}

guard let results = request.results, !results.isEmpty else {
    die("ocr_clip: 圖片裡認不出文字")
}

// 由上到下排序（normalized 座標原點在左下，maxY 越大越上面）
let lines = results.sorted { $0.boundingBox.maxY > $1.boundingBox.maxY }

// ---- 組字 + 拆換行 ----
var out = ""
for (idx, line) in lines.enumerated() {
    guard let text = line.topCandidates(1).first?.string else { continue }
    out += text
    if idx == lines.count - 1 { break }
    let wrapped = dewrap && line.boundingBox.maxX >= marginThreshold
    out += wrapped ? "" : "\n"
}

// ---- 寫回剪貼簿 ----
pb.clearContents()
pb.setString(out, forType: .string)

if !quiet { print(out) }
