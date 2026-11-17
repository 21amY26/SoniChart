#!/bin/zsh
# Export a .docx to PDF with Microsoft Word (AppleScript).  Usage: report/render.sh in.docx out.pdf
osascript -e "with timeout of 300 seconds
tell application \"Microsoft Word\"
open POSIX file \"$1\"
set d to active document
save as d file name \"$2\" file format format PDF
close d saving no
end tell
end timeout"
