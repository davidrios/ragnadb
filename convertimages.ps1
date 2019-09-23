if (!(Get-Command magick.exe -EA SilentlyContinue)) {
    Write-Host "ImageMagick is not installed or not in PATH, aborting." -ForegroundColor red -BackgroundColor black
    exit
}

$toConvert = Get-ChildItem -File -Filter '*.bmp'
$toConvert | ForEach-Object -Begin { $i = 0 } -Process {
    $oldName = $_.Name
    $newName = $oldName.Replace(".bmp", ".png")
    magick.exe convert -transparent "#ff00ff" "$oldName" "$newName"
    if ($?) {
        Remove-Item "$oldName"
    }
    $i = $i + 1
    Write-Progress -Activity "Converting images" -Status "Progress:" -PercentComplete ($i/$toConvert.count*100)
}