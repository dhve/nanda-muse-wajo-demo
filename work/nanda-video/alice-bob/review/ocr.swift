import AppKit
import Vision
import Foundation
for path in CommandLine.arguments.dropFirst() {
    let url=URL(fileURLWithPath:path)
    guard let image=NSImage(contentsOf:url), let data=image.tiffRepresentation, let bitmap=NSBitmapImageRep(data:data), let cg=bitmap.cgImage else {continue}
    let request=VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage:cg).perform([request])
    let rows=(request.results ?? []).compactMap{$0.topCandidates(1).first?.string}
    let json=try JSONSerialization.data(withJSONObject:["file":path,"text":rows.joined(separator:"\n")],options:[.sortedKeys])
    print(String(data:json,encoding:.utf8)!)
}
