# PowerShell 생산성 스크립트 (my-utils-powershell)

Windows PowerShell 7 환경에서 `yt-dlp` 및 `ffmpeg`을 더 쉽게 사용하기 위한 개인용 자동화 스크립트 모음입니다.

이 프로젝트의 핵심은 실제 로직을 담고 있는 스크립트 '엔진'(`f1.ps1`, `ytpl.py` 등)과, 이 엔진들을 PowerShell 프로필(`$PROFILE`)에 등록된 '단축 함수'(`f1`, `ytpl` 등)로 호출하는 런처(Launcher) 구조를 사용한다는 점입니다.

---

## 🌟 주요 기능 (Features)

이 스크립트들은 PowerShell 터미널에서 복잡한 `yt-dlp`나 `ffmpeg` 옵션 대신, 간단한 단축 명령어로 영상/음악을 다운로드할 수 있게 해줍니다.

* **`f1 [이름] [URL]`**: 단일 영상/음원을 다운로드합니다. 인자 순서가 바뀌거나 URL이 클립보드에 있어도 자동으로 인식합니다. (예: `f1 "영상 이름" https://...`)
* **`f2 [이름] [URL]`**: HLS 스트림 등을 1시간 단위로 분할하여 다운로드합니다. (예: `f2 "라디오 녹화" https://...`)
* **`ytpl [URL] [화질] [언어]`**: `yt-dlp` 파이썬 스크립트를 직접 호출하여 플레이리스트 전체를 다운로드합니다. 화질(예: `720`), 자막 언어(예: `en`) 등을 옵션으로 지정할 수 있습니다. (예: `ytpl https://... 720 ko`)

---

## 🛠️ 필수 의존성 (Dependencies)

이 스크립트들은 로컬 PC에 다음과 같은 **외부 프로그램**들이 설치되어 있고, 스크립트 내의 경로가 올바르게 설정되어 있다고 가정합니다.

1.  **FFmpeg**: `f1`, `f2`, `ff.ps1` 스크립트의 핵심 의존성입니다.
2.  **NirCmd**: `!+d` (오디오 장치 토글) 같은 단축키를 위한 유틸리티입니다.
3.  **Python 3**: `ytpl.py` 스크립트 실행에 필요합니다.
4.  **yt-dlp (Python Pkg)**: `ytpl.py`가 사용하는 파이썬 라이브러리입니다.

---

## 🔧 구조 및 설치 방법 (Setup Guide)

이 레포지토리는 '설치 스크립트'가 아닌, **개인 설정을 백업하고 공유**하기 위한 '참조용'입니다.

### 1. 스크립트 엔진 (본 레포지토리)

이 레포지토리에는 다음과 같은 4개의 '엔진' 스크립트가 포함되어 있습니다.

* **`f1.ps1` / `f2.ps1`**: `f1`, `f2` 단축 명령의 실제 로직을 수행합니다.
* **`ff.ps1`**: `f1`, `f2`가 `ffmpeg.exe`를 쉽게 호출할 수 있도록 돕는 래퍼(wrapper) 스크립트입니다. **(필수)**
* **`ytpl.py`**: `ytpl` 단축 명령의 실제 로직(Python)을 수행합니다.

### 2. 런처 함수 (PowerShell 프로필)

'엔진' 스크립트를 터미널 어디에서나 `f1`, `ytpl` 등의 단축 명령어로 부르려면, 이 '런처 함수'들을 님의 PowerShell `$PROFILE` 파일에 추가해야 합니다.

1.  PowerShell 터미널에서 `code $PROFILE` (또는 `notepad $PROFILE`)을 입력하여 프로필 파일을 엽니다.
2.  아래 코드를 복사하여 프로필 파일 **맨 아래에 붙여넣기** 합니다.

**[ `$PROFILE`에 추가할 런처 함수 코드 ]**

```powershell
# ===================================================================
#          나만의 PowerShell 단축 명령어 및 함수 설정
# ===================================================================

# --- 1. 공통 설정 (사용자 수정 필요) ---
# 이 레포지토리를 clone한 경로로 수정해야 합니다.
$myScriptFolder = "C:\yt-dlp" # 예시: C:\projects\my-utils-powershell

# --- 2. f1, f2 단축 실행 함수 ---
function _Invoke-FfmpegScript {
    param([string]$ScriptName, [object[]]$UserArgs)
    $finalUrl = $null; $nonUrlArgs = @()
    foreach ($arg in $UserArgs) { if ($arg -like "*http*" -or $arg -like "*www*") { $finalUrl = $arg } else { $nonUrlArgs += $arg } }
    if (-not $finalUrl) { $finalUrl = Get-Clipboard }
    if ($nonUrlArgs.Count -eq 0) { Write-Host "오류: [이름]은 반드시 입력해야 합니다." -ForegroundColor Red; return }
    $finalName = $nonUrlArgs -join ' '
    if ([string]::IsNullOrWhiteSpace($finalUrl) -or ($finalUrl -notlike "*http*" -and $finalUrl -notlike "*www*")) { Write-Host "오류: 유효한 URL이 없거나 클립보드가 비어있습니다." -ForegroundColor Red; return }
    & "$myScriptFolder\$ScriptName" -Url $finalUrl -Name $finalName
}
function f1 { _Invoke-FfmpegScript -ScriptName "f1.ps1" -UserArgs $args }
function f2 { _Invoke-FfmpegScript -ScriptName "f2.ps1" -UserArgs $args }

# --- 3. ytpl 단축 실행 함수 (사용자 수정 필요) ---
function ytpl {
    # --- 사용자 수정 필요 (Python 경로) ---
    $pythonExePath = "$env:USERPROFILE\scoop\apps\python\current\python.exe"
    # ---
    $pythonScriptPath = "$myScriptFolder\ytpl.py"
    $finalUrl = $null; $finalQuality = $null; $finalLang = $null; $unidentifiedArgs = @()
    foreach ($arg in $args) {
        if ($arg -like "*http*" -or $arg -like "*www*") { $finalUrl = $arg }
        elseif ($arg -match "^\d+p?$") { $finalQuality = $arg -replace 'p', '' }
        elseif ($arg -match "^[a-zA-Z]{2}$") { $finalLang = $arg }
        else { $unidentifiedArgs += $arg }
    }
    if ($unidentifiedArgs.Count -gt 0) { Write-Host "경고: '$($unidentifiedArgs -join ', ')'는 인식할 수 없는 옵션입니다. 무시합니다." -ForegroundColor Yellow }
    if (-not $finalUrl) { $finalUrl = Get-Clipboard }
    if ([string]::IsNullOrWhiteSpace($finalUrl) -or ($finalUrl -notlike "*http*" -and $finalUrl -notlike "*www*")) { Write-Host "오류: 유효한 URL이 없거나 클립보드가 비어있습니다." -ForegroundColor Red; return }
    $finalArgs = @(); $finalArgs += "$finalUrl";
    if ($finalQuality) { $finalArgs += $finalQuality }
    if ($finalLang) { $finalArgs += $finalLang }
    & $pythonExePath $pythonScriptPath $finalArgs
}

Write-Host "✅ 나만의 단축 명령어 (f1, f2, ytpl)가 모두 로드되었습니다!" -ForegroundColor Green