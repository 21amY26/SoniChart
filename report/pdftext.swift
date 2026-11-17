import PDFKit
// Print each page's text separated by a form feed, for report pagination checks.
let doc = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
for i in 0..<doc.pageCount { print(doc.page(at: i)!.string ?? "", terminator: "\u{0C}") }
