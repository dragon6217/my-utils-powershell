# 이 스크립트는 이제 URL과 이름을 인자로 받아 처리하는 '엔진' 역할만 합니다.
param (
    [Parameter(Mandatory=$true)] [string]$Url,
    [Parameter(Mandatory=$true)] [string]$Name
)
$date = Get-Date -Format "yyMMdd"; $baseName = "${Name}_${date}"; $extension = ".mkv"; $number = 1
$outputFile = "${baseName}_f($number)${extension}"
while (Test-Path -Path $outputFile) { $number++; $outputFile = "${baseName}_f($number)${extension}" }
Write-Host "정보: 최종 저장 파일명 결정 -> $outputFile" -ForegroundColor Cyan
ff.ps1 -i $Url -c copy "$outputFile"

