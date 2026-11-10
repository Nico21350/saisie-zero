# Convertit chaque page HTML de exemples/sources en PDF dans exemples/, avec Microsoft Edge sans fenêtre.
# Utilisation : powershell -ExecutionPolicy Bypass -File exemples\generer-pdf.ps1

$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$dossier = $PSScriptRoot

Get-ChildItem (Join-Path $dossier "sources") -Filter *.html | ForEach-Object {
    $pdf = Join-Path $dossier ($_.BaseName + ".pdf")
    $url = ([System.Uri]$_.FullName).AbsoluteUri
    & $edge --headless --disable-gpu --no-pdf-header-footer "--print-to-pdf=$pdf" $url | Out-Null
    Write-Output "PDF créé : $($_.BaseName).pdf"
}
