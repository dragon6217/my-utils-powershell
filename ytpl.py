import sys
import os
import yt_dlp
import re
import time
import random
import urllib.parse

# --- 터미널 색상 출력을 위한 설정 ---
os.system('') # Windows에서 ANSI 이스케이프 코드 활성화
class Colors:
    HEADER = '\033[93m'; HIGHLIGHT = '\033[92m'; RESET = '\033[0m'
    CYAN = '\033[96m'; RED = '\033[91m'

def sanitize_filename(name):
    """파일/폴더 이름으로 사용할 수 없는 문자를 '_'로 대체합니다."""
    if not name or name.isspace(): return "Untitled"
    name = name.replace('%', '_'); return re.sub(r'[\\/*?:"<>|]', "_", name)

def get_unique_foldername(base_path):
    """기본 경로가 이미 존재할 경우, 중복되지 않는 새 폴더 경로를 생성합니다."""
    folder_name, dir_path = os.path.basename(base_path), os.path.dirname(base_path)
    if not dir_path: dir_path = '.'; counter, new_path = 2, base_path
    while os.path.exists(new_path):
        new_name = f"{folder_name} ({counter})"; new_path = os.path.join(dir_path, new_name); counter += 1
    return new_path

def format_line_to_string(format_dict):
    """포맷 정보를 출력용 문자열로 변환합니다."""
    height_val, width_val = format_dict.get('height'), format_dict.get('width')
    resolution_str = f"{width_val}x{height_val}" if isinstance(height_val, int) else "audio only"
    fps_str = str(format_dict.get('fps', '')); resolution_fps_str = f"{resolution_str} {fps_str}".strip()
    return (f"{format_dict.get('format_id', 'ID'):<8}{format_dict.get('ext', 'EXT'):<8}"
            f"{resolution_fps_str:<20}{format_dict.get('vcodec', 'none'):<25}"
            f"{format_dict.get('acodec', 'none'):<15}{format_dict.get('format_note', 'NOTE')}")

def select_formats(formats, quality, language=None):
    """주어진 조건에 맞는 최적의 비디오/오디오 포맷을 선택합니다."""
    def is_valid_video(f):
        height = f.get('height')
        return isinstance(height, int) and height <= quality

    selected_video, selected_audio = None, None
    video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and is_valid_video(f)]
    if video_formats: selected_video = sorted(video_formats, key=lambda x: x['height'], reverse=True)[0]
    
    audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
    
    priority_checks = []
    if language: priority_checks.append({'type': 'lang', 'value': language})
    priority_checks.extend([{'type': 'note', 'value': 'original'}, {'type': 'lang', 'value': 'und'}, {'type': 'lang', 'value': 'en'}])

    for check in priority_checks:
        found_formats = []
        if check['type'] == 'lang':
            found_formats = [f for f in audio_formats if f.get('language') and f.get('language').startswith(check['value'])]
        elif check['type'] == 'note':
            found_formats = [f for f in audio_formats if check['value'] in f.get('format_note', '').lower()]
        if found_formats:
            selected_audio = sorted(found_formats, key=lambda x: x.get('abr', 0), reverse=True)[0]; break
    
    if selected_audio is None and audio_formats:
        selected_audio = sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True)[0]

    if (not selected_video or not selected_audio) and not (selected_video and selected_video.get('acodec') != 'none'):
        general_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and is_valid_video(f)]
        if general_formats:
            selected_video = sorted(general_formats, key=lambda x: x['height'], reverse=True)[0]; selected_audio = None
            
    return selected_video, selected_audio

def print_available_formats(formats, selected_video, selected_audio, quality):
    """필터링된 전체 포맷 목록을 출력하고 선택된 항목을 강조합니다."""
    print(f"\n--- {Colors.HEADER}사용 가능한 포맷 목록 (화질: {quality}p 이하, 음질: Medium 이상){Colors.RESET} ---")
    header = (f"{'ID':<8}{'EXT':<8}{'RESOLUTION FPS':<20}{'VCODEC':<25}{'ACODEC':<15}{'NOTE'}")
    print(Colors.HEADER + header + Colors.RESET); print("-" * 100)
    
    filtered_formats = [f for f in formats if (f.get('vcodec') != 'none' and isinstance(f.get('height'), int) and f.get('height') <= quality) or \
                                             (f.get('acodec') != 'none' and isinstance(f.get('abr'), (int, float)) and f.get('abr') >= 100)]
    if not filtered_formats: print("조건에 맞는 포맷이 없습니다."); return

    for f in filtered_formats:
        line = format_line_to_string(f)
        is_selected = (selected_video and f.get('format_id') == selected_video.get('format_id')) or \
                      (selected_audio and f.get('format_id') == selected_audio.get('format_id'))
        if is_selected: print(Colors.HIGHLIGHT + ">> " + line + Colors.RESET)
        else: print("   " + line)

def print_available_subtitles(video_info, target_langs):
    """사용자 제작 자막 목록을 출력하고 선택된 항목을 강조합니다."""
    print(f"\n--- {Colors.HEADER}사용자 제작 자막 목록{Colors.RESET} ---")
    manual_subs = video_info.get('subtitles', {})
    if not manual_subs: print("(사용자 제작 자막 없음)"); return
    
    found_target_count = 0
    for lang in manual_subs.keys():
        is_target = any(lang.startswith(target) for target in target_langs)
        if is_target: print(Colors.HIGHLIGHT + f">> {lang} (선택됨)" + Colors.RESET); found_target_count += 1
        else: print(f"   {lang}")
    if found_target_count == 0: print(f"{Colors.CYAN}INFO: 요청하신 사용자 제작 자막({', '.join(target_langs)})을(를) 찾을 수 없습니다.{Colors.RESET}")

def download_playlist(url, quality, language=None):
    MAX_RETRIES, RETRY_DELAY = 3, 5; failed_videos = []
    target_subtitle_langs = ['en']
    if language and language not in target_subtitle_langs: target_subtitle_langs.append(language)
    
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    video_id, playlist_id = query_params.get('v', [None])[0], query_params.get('list', [None])[0]
    if video_id and playlist_id: processed_url, is_explicitly_single_video = f"https://www.youtube.com/watch?v={video_id}", True
    else: processed_url, is_explicitly_single_video = url, False
    if "playlist?list=" in processed_url and not is_explicitly_single_video: print("플레이리스트 정보 가져오는 중...")
    else: print("영상 정보 가져오는 중...")
    try:
        ydl_global_opts = {'quiet': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_global_opts) as ydl:
            info = ydl.extract_info(processed_url, download=False)
            if not info: print(f"{Colors.RED}오류: URL 정보를 가져올 수 없습니다.{Colors.RESET}"); return
    except yt_dlp.utils.DownloadError as e:
        print(f"{Colors.RED}오류: URL 정보를 가져올 수 없습니다. ({e}){Colors.RESET}"); return
    is_playlist = 'entries' in info and info['entries'] and not is_explicitly_single_video
    videos_to_download = info.get('entries', []) if is_playlist else [info]
    if not videos_to_download: print("다운로드할 영상을 찾지 못했습니다."); return
    playlist_folder = '.'
    if is_playlist and not is_explicitly_single_video:
        owner_name = sanitize_filename(info.get('uploader', info.get('channel', 'Unknown Channel')))
        owner_handle = info.get('uploader_id', '')
        playlist_title = sanitize_filename(info.get('title', 'youtube_playlist'))
        if owner_handle: base_folder_name = f"{owner_name}({owner_handle}) - {playlist_title} - ({quality}p)"
        else: base_folder_name = f"{owner_name} - {playlist_title} - ({quality}p)"
        playlist_folder = get_unique_foldername(base_folder_name); os.makedirs(playlist_folder, exist_ok=True); print(f"\n📁 다운로드 폴더: '{playlist_folder}'")

    for i, video_info in enumerate(videos_to_download):
        video_title = video_info.get('title', '제목 없음'); video_url = video_info.get('webpage_url', video_info.get('url'))
        if not video_url:
            failed_videos.append({'title': video_title, 'url': 'URL 없음', 'reason': 'URL 정보 누락'}); continue
        
        print("\n" + "=" * 100); print(f"▶️  처리 시작 ({i+1}/{len(videos_to_download)}): {video_title}"); print(f"🔗 URL: {video_url}"); print("=" * 100)
        
        for attempt in range(MAX_RETRIES):
            try:
                selected_video, selected_audio = select_formats(video_info['formats'], quality, language)
                print_available_formats(video_info['formats'], selected_video, selected_audio, quality)
                print_available_subtitles(video_info, target_subtitle_langs)
                
                if not selected_video: raise yt_dlp.utils.DownloadError(f"{quality}p 이하의 다운로드 가능한 영상 포맷이 없습니다.")
                
                if selected_video and selected_audio: format_string = f"{selected_video['format_id']}+{selected_audio['format_id']}"
                else: format_string = selected_video['format_id']

                actual_height = selected_video.get('height')
                quality_for_filename = actual_height if actual_height else quality
                if is_playlist and not is_explicitly_single_video:
                    filename_base = f"({i + 1:03d}) - %(title)s__({quality_for_filename}p)"
                    output_template = os.path.join(playlist_folder, f"{filename_base}.%(ext)s")
                else:
                    output_template = os.path.join(playlist_folder, f"%(title)s__({quality_for_filename}p).%(ext)s")
                
                ydl_opts = {
                    'format': format_string, 'outtmpl': output_template,
                    'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': target_subtitle_langs,
                    'postprocessors': [{'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'}],
                    'merge_output_format': 'mp4', 
                    'fragment_retries': 'infinite', 'retries': 15, 'socket_timeout': 60,
                    # ⭐️ [수정] 요청에 따라 sleep_interval 옵션 제거
                    # 'sleep_interval': 2, 'max_sleep_interval': 10,
                    'ignoreerrors': True, # 자막 등에서 오류가 발생해도 영상 다운로드는 계속
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    error_code = ydl.download([video_url])
                    if error_code != 0:
                        raise yt_dlp.utils.DownloadError(f"yt-dlp가 다운로드 실패를 보고했습니다 (오류 코드: {error_code}).")
                
                break
            
            except yt_dlp.utils.DownloadError as e:
                print(f"\n{Colors.RED}❌ 다운로드 오류 발생 (시도 {attempt + 1}/{MAX_RETRIES}): {e}{Colors.RESET}")
                if attempt < MAX_RETRIES - 1:
                    sleep_time = random.uniform(8, 15); print(f"{sleep_time:.2f}초 후 재시도합니다..."); time.sleep(sleep_time)
                else:
                    print(f"'{video_title}' 다운로드 최종 실패."); failed_videos.append({'title': video_title, 'url': video_url, 'reason': str(e)})
            
            except Exception as e:
                print(f"\n{Colors.RED}❌ 치명적/내부 오류 발생 (시도 {attempt + 1}/{MAX_RETRIES}): {e}{Colors.RESET}")
                print(f"{Colors.CYAN}INFO: 이 오류는 yt-dlp 내부의 문제일 수 있습니다. 해당 영상은 다음 시도에서 동일한 오류를 발생시킬 가능성이 높습니다.{Colors.RESET}")
                failed_videos.append({'title': video_title, 'url': video_url, 'reason': str(e)})
                break
        
        if i < len(videos_to_download) - 1:
            sleep_time = random.uniform(8, 15); print(f"\nINFO: 다음 영상 처리 전 {sleep_time:.2f}초 대기합니다..."); time.sleep(sleep_time)

    print("\n" + "=" * 100 + "\n🎉 모든 작업이 완료되었습니다.\n" + "=" * 100)
    if failed_videos:
        print(f"\n## {Colors.HEADER}📋 최종 다운로드 실패 목록{Colors.RESET}"); print("-" * 100)
        for item in failed_videos:
            print(f"제목: {item['title']}\nURL: {item['url']}\n사유: {item.get('reason', '알 수 없음')}\n" + "-"*100)
    else:
        print(f"\n{Colors.HIGHLIGHT}✅ 모든 다운로드가 성공적으로 완료되었습니다.{Colors.RESET}")

if __name__ == '__main__':
    if len(sys.argv) < 2: print("사용법: ytpl \"<YouTube URL>\" [화질] [언어]"); sys.exit(1)
    youtube_url = sys.argv[1]; args = sys.argv[2:]
    target_quality = 1080; target_language = None
    for arg in args:
        if arg.isdigit(): target_quality = int(arg)
        else: target_language = arg.lower()
    download_playlist(youtube_url, target_quality, target_language)