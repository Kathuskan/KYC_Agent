import Foundation
import Vision
import ImageIO
import CoreGraphics
let data = FileHandle.standardInput.readDataToEndOfFile()
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesCPUOnly = true
request.usesLanguageCorrection = false
guard let source = CGImageSourceCreateWithData(data as CFData, nil), let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { exit(1) }
let handler = VNImageRequestHandler(cgImage: image, options: [:])
do {
    try handler.perform([request])
    let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    let json = try JSONSerialization.data(withJSONObject: lines)
    FileHandle.standardOutput.write(json)
} catch {
    FileHandle.standardError.write(Data("Image recognition failed: \(error)".utf8))
    exit(1)
}
