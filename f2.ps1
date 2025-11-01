# 이 스크립트는 이제 URL과 이름을 인자로 받아 처리하는 '엔진' 역할만 합니다.
param (
    [Parameter(Mandatory=$true)] [string]$Url,
    [Parameter(Mandatory=$true)] [string]$Name
)
$date = Get-Date -Format "yyMMdd"; $baseName = "${Name}_${date}"; $number = 1
$outputPattern = "${baseName}_s($number)_%02d.mkv"; $firstFileCheck = $outputPattern.Replace("%02d", "01")
while (Test-Path -Path $firstFileCheck) { $number++; $outputPattern = "${baseName}_s($number)_%02d.mkv"; $firstFileCheck = $outputPattern.Replace("%02d", "01") }
Write-Host "정보: 최종 저장 파일 패턴 결정 -> $outputPattern" -ForegroundColor Cyan
ff.ps1 -i "$Url" -f segment -segment_time 3600 -reset_timestamps 1 -segment_start_number 1 -y "$outputPattern"

