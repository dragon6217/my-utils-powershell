# 1. 실행할 ffmpeg.exe의 전체 경로를 변수에 저장합니다.
#    (!! 사용자 수정 필요 !!) 님의 ffmpeg.exe 실제 경로로 변경하세요.
$ffmpegPath = "C:\yt-dlp\ffmpeg-7.1-essentials_build\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe"

# 2. 이 스크립트로 전달된 모든 인수를 ffmpeg.exe에 그대로 넘겨주며 실행합니다.
& $ffmpegPath $args