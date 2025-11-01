# PowerShell 기반 영상 다운로드 자동화 유틸리티

이 프로젝트는 `ffmpeg`과 `yt-dlp`를 기반으로, 스트리밍 영상(예: Chzzk의 .m3u8) 및 YouTube 영상/재생목록 다운로드 과정을 자동화하는 PowerShell 스크립트 모음입니다.

복잡한 명령어 옵션을 기억할 필요 없이, `f1 "영상 이름"` 같은 간단한 단축 명령어를 통해 클립보드의 URL을 자동으로 감지하고 다운로드합니다.

---

## 🌟 아키텍처: 런처(Launcher)와 엔진(Engine)

이 시스템은 PowerShell 프로필(`$PROFILE`)과 실제 스크립트('엔진')를 분리하는 설계를 사용합니다.

1.  **런처 (PowerShell `$PROFILE`)**:
    * `f1`, `f2`, `ytpl` 같은 간단한 단축 함수를 정의합니다.
    * 클립보드에서 URL을 자동으로 가져오고, 사용자 인자(예: "영상 이름", "720p")를 분석하여 '엔진' 스크립트에 전달합니다.
2.  **엔진 (이 레포지토리의 스크립트)**:
    * `f1.ps1`, `f2.ps1`, `ytpl.py` 등 실제 다운로드 로직을 수행합니다.
    * `ff.ps1`은 `ffmpeg.exe`를 한 번 더 감싸는 래퍼(wrapper) 역할을 합니다.

**워크플로우 예시:**
`터미널에 'f1 "영상 이름"' 입력` → `PowerShell $PROFILE` → `_Invoke-FfmpegScript 함수` → `f1.ps1 (엔진)` → `ff.ps1 (래퍼)` → `ffmpeg.exe` 실행

---

## 🚀 주요 기능 (Features)

### 1. `f1` / `f2` (FFmpeg 스트림 다운로더)

`f1`과 `f2`는 클립보드에 복사된 `.m3u8` URL(예: Chzzk 스트림)을 `ffmpeg`을 통해 다운로드합니다.

* **사용법:** `f1 [파일 이름]` 또는 `f2 [파일 이름]`
* **지능형 인자 처리:** `[파일 이름]`은 필수이며, `[URL]`은 생략 가능합니다.
    * `f1 "녹화 1" https://...` (URL 명시적 전달)
    * `f1 "녹화 1"` (클립보드에서 URL 자동 감지)
* **자동 이름 생성:** `[파일 이름]`과 현재 날짜, 중복 방지 번호를 조합하여 파일명을 생성합니다. (예: `녹화 1_251101_f(1).mkv`, 중복 시 `_f(2).mkv`)
* **`f1` vs `f2`:**
    * **`f1`**: 단일 파일로 다운로드합니다.
    * **`f2`**: `-f segment` 옵션을 사용하여 1시간 단위로 스트림을 분할 저장합니다. (파일명 `_s(1)_01.mkv`, `_s(1)_02.mkv`...)

### 2. `ytpl` (YouTube 플레이리스트 다운로더)

`yt-dlp` 라이브러리를 사용하는 Python 스크립트를 호출하여 YouTube 영상 또는 재생목록을 다운로드합니다.

* **사용법:** `ytpl [URL] [화질] [언어]`
* **지능형 인자 처리:**
    * `ytpl`: 클립보드의 URL로, 기본값(1080p, 영어/원본 자막)을 사용하여 다운로드합니다.
    * `ytpl 720`: 클립보드의 URL을 720p 화질로 다운로드합니다.
    * `ytpl https://... 480 ko`: 특정 URL을 480p 화질, 한국어 자막 우선으로 다운로드합니다.
* **고급 포맷 선택:** `ytpl.py` 스크립트는 요청된 화질, 언어 설정에 맞춰 최적의 비디오/오디오 포맷을 자동으로 선택하고 병합합니다.

---

## 🛠️ 필수 의존성 (Dependencies)

이 스크립트가 작동하려면 다음 프로그램들이 로컬 PC에 설치되어 있어야 합니다.

1.  **FFmpeg**: `f1`, `f2` 스크립트의 핵심 의존성입니다. ([다운로드 링크](https://ffmpeg.org/download.html))
2.  **Python 3**: `ytpl.py` 스크립트 실행에 필요합니다.
3.  **yt-dlp** (Python Pkg): `pip install yt-dlp` 명령어로 설치해야 합니다.
4.  **(선택)** **FetchV** (Edge/Chrome 확장 프로그램): `.m3u8` URL을 쉽게 추출하기 위해 권장됩니다.

---

## 🔧 설치 및 적용 방법 (Setup Guide)

1.  **1단계: 엔진 스크립트 `clone`**
    이 레포지토리(`my-utils-powershell`)를 님의 PC 원하는 경로에 `clone`합니다. (예: `C:\projects\my-utils-powershell`)

2.  **2단계: 엔진 스크립트 경로 설정**
    `clone`한 폴더 안의 스크립트 2개를 수정해야 합니다.
    * **`ff.ps1` 수정:** `$ffmpegPath` 변수의 경로를 님의 `ffmpeg.exe` 실제 위치로 변경합니다.
    * **`f1.ps1` / `f2.ps1` 수정 (선택):** 이 스크립트들은 `ff.ps1`을 호출합니다. 만약 `ff.ps1`이 `f1.ps1`과 다른 폴더에 있다면 경로를 수정해야 합니다. (같은 폴더에 있다면 수정 불필요)

3.  **3단계: 런처 함수 프로필에 등록**
    터미널에서 `code $PROFILE` (또는 `notepad $PROFILE`)을 입력하여 님의 PowerShell 프로필 파일을 엽니다.
    프로필 파일 맨 아래에 아래 **[런처 함수 코드]**를 **전체 복사**하여 붙여넣습니다.

4.  **4단계: 런처 함수 경로 설정 (가장 중요!)**
    방금 프로필에 붙여넣은 코드의 **맨 윗부분**을 님의 환경에 맞게 수정합니다.
    * `$myScriptFolder`: **1단계**에서 `clone`한 이 레포지토리의 경로로 수정합니다. (예: `C:\projects\my-utils-powershell`)
    * `$pythonExePath`: 님의 `python.exe` 실제 경로로 수정합니다.

5.  **PowerShell 재시작:** 터미널을 껐다 켜면 `f1`, `f2`, `ytpl` 명령어가 활성화됩니다.

---

## 💻 [ `$PROFILE`에 추가할 런처 함수 코드 ]

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
    # 현재 위치에서 실행되도록 $myScriptFolder 경로 수정
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