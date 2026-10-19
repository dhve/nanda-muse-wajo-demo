import Foundation
import CoreImage
let path = CommandLine.arguments[1]
guard let image=CIImage(contentsOf:URL(fileURLWithPath:path)) else { fatalError("Cannot read image") }
let detector=CIDetector(ofType:CIDetectorTypeQRCode,context:nil,options:[CIDetectorAccuracy:CIDetectorAccuracyHigh])
let results=(detector?.features(in:image) as? [CIQRCodeFeature] ?? []).compactMap { $0.messageString }
print(results)
if !results.contains("https://nandaindex.org") { exit(1) }
