// Make the end-card QR code with CoreImage, then prove it decodes.
//
//   swift production/tools/qr.swift https://nandaindex.org production/player/assets/qr-nandaindex.svg
//
// Writes an SVG (dark modules on white, 4-module quiet zone) and prints the string that
// CoreImage's own QR detector reads back from a rendered copy. No network, no app UI.
import AppKit
import CoreImage
import Foundation

let args = CommandLine.arguments
let message = args.count > 1 ? args[1] : "https://nandaindex.org"
let svgPath = args.count > 2 ? args[2] : "qr.svg"

guard let gen = CIFilter(name: "CIQRCodeGenerator") else { fatalError("CIQRCodeGenerator missing") }
gen.setValue(message.data(using: .utf8), forKey: "inputMessage")
gen.setValue("M", forKey: "inputCorrectionLevel")
guard let qr = gen.outputImage else { fatalError("no QR image") }

let ctx = CIContext()
guard let cg = ctx.createCGImage(qr, from: qr.extent) else { fatalError("render failed") }
let rep = NSBitmapImageRep(cgImage: cg)
var dark: [[Bool]] = []
for y in 0..<rep.pixelsHigh {
    var row: [Bool] = []
    for x in 0..<rep.pixelsWide {
        row.append((rep.colorAt(x: x, y: y)?.brightnessComponent ?? 1) < 0.5)
    }
    dark.append(row)
}
// Trim CoreImage's own margin, then add a standard 4-module quiet zone.
let rows = dark.indices.filter { dark[$0].contains(true) }
let cols = (0..<rep.pixelsWide).filter { x in dark.contains { $0[x] } }
guard let top = rows.first, let bottom = rows.last, let left = cols.first, let right = cols.last else { fatalError("empty QR") }
let n = bottom - top + 1
let quiet = 4
let size = n + 2 * quiet
var path = ""
for y in 0..<n {
    for x in 0..<n where dark[top + y][left + x] {
        path += "M\(x + quiet) \(y + quiet)h1v1h-1z"
    }
}
_ = right
let svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 \(size) \(size)" shape-rendering="crispEdges" role="img" aria-label="QR code for \(message)">
<rect width="\(size)" height="\(size)" fill="#ffffff"/>
<path fill="#00142b" d="\(path)"/>
</svg>

"""
try svg.write(toFile: svgPath, atomically: true, encoding: .utf8)

// Verify: draw the trimmed matrix at 12 px per module with the quiet zone, then detect.
let scale = 12
let px = size * scale
let canvas = NSImage(size: NSSize(width: px, height: px))
canvas.lockFocus()
NSColor.white.setFill(); NSRect(x: 0, y: 0, width: px, height: px).fill()
NSColor(red: 0, green: 0.078, blue: 0.169, alpha: 1).setFill()
for y in 0..<n {
    for x in 0..<n where dark[top + y][left + x] {
        NSRect(x: (x + quiet) * scale, y: (size - 1 - (y + quiet)) * scale, width: scale, height: scale).fill()
    }
}
canvas.unlockFocus()
guard let tiff = canvas.tiffRepresentation, let ci = CIImage(data: tiff) else { fatalError("verify render failed") }
let detector = CIDetector(ofType: CIDetectorTypeQRCode, context: nil, options: [CIDetectorAccuracy: CIDetectorAccuracyHigh])
let decoded = (detector?.features(in: ci) as? [CIQRCodeFeature])?.first?.messageString ?? "<none>"
print("modules \(n), quiet zone \(quiet), svg \(svgPath)")
print("decoded: \(decoded)")
print(decoded == message ? "QR OK" : "QR MISMATCH")
