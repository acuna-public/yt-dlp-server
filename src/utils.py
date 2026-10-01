import argparse
import io
import os
import shutil
import subprocess
from typing import LiteralString

import requests
from starlette import status
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from schema import ApiResponse, DownloadRequest, VideoDownloadError, InfoRequest

parser = argparse.ArgumentParser ()

parser.add_argument (
  '--port', '-p',
  type = int,
  default = 8000,
  help = f'Port (8000 by default)'
)

parser.add_argument (
  '--verbose', '-v',
  action = 'store_true',
  help = 'Verbose mode'
)

args = vars (parser.parse_args ())

ydl_info = YoutubeDL ()

def process_single_video (
	payload: DownloadRequest,
	info_dict: dict,
	x_exists_action: str
) -> ApiResponse:
	
	"""
	Core logic to download a single video from an already extracted metadata dictionary.
	Guarantees single-pass execution by leveraging process_video_result instead of extract_info.
	"""
	
	if payload:
		
		if payload.download_dir:
			
			ext = info_dict.get ('ext')
			
			if payload.name:
				
				# name = re.sub (r'[:\\*?\'<>|]', '', payload.name).strip ()
				name = payload.name.strip ()
				
				existed_file = os.path.join (payload.download_dir, f'{name}.{ext}')
				
				# Handle deduplication strategies using the centralized response generator
				
				if os.path.exists (existed_file):
					
					if not x_exists_action or x_exists_action == 'skip':
						return make_response ('skipped', status.HTTP_302_FOUND, 'File already exists')
					elif x_exists_action == 'error':
						
						return make_response (
							'error',
							status.HTTP_409_CONFLICT,
							f'File "{name}.{ext}" already exists',
							saved_to = existed_file
						)
					
					elif x_exists_action == 'smaller':
						
						remote_size = info_dict.get ('filesize') or info_dict.get ('filesize_approx')
						
						local_size = os.path.getsize (existed_file)
						
						if remote_size and local_size >= remote_size:
							
							return make_response (
								'skipped',
								status.HTTP_200_OK,
								'File skipped. Local file is intact or larger',
								saved_to = existed_file
							)
						
						else:
							
							try:
								os.remove (existed_file)
							except Exception as e:
								return make_response ('error', status.HTTP_500_INTERNAL_SERVER_ERROR, str (e))
					
					elif x_exists_action == 'rename':  # TODO Tests
						
						base_dir = os.path.dirname (existed_file)
						
						# Take only the first element [0] of the tuple to get the raw string name
						base_name_only = os.path.splitext (os.path.basename (existed_file))[0]
						
						# Now we correctly pass two strings to os.path.join
						existed_file = get_unique_filename (os.path.join (base_dir, base_name_only), ext)
						
						# relpath also returns a tuple from splitext, so we take [0] here as well
						name = os.path.splitext (os.path.relpath (existed_file, payload.download_dir))[0]
					
					ydl_info.params['outtmpl']['default'] = f'{name}.%(ext)s'
					
					if payload.chapter_name:
						
						ydl_info.params['outtmpl']['chapter'] = os.path.join (
							payload.download_dir,
							f'{payload.chapter_name}.%(ext)s'
						)
					
					if payload.makedir:
						os.makedirs (os.path.dirname (existed_file), exist_ok = True)
			
			ydl_info.params['paths'] = { 'home': payload.download_dir + '\\' }  # type: ignore
		
		if payload.type == 'audio':
			
			ydl_info.params['postprocessors'] += [
				{
					
					'key': 'FFmpegExtractAudio',
					'preferredcodec': 'm4a',
					
				}
			]
		
		if 'writethumbnail' in payload.params:
			
			ydl_info.params['postprocessors'] += [
				{
					
					'key': 'EmbedThumbnail',
					'already_have_thumbnail': False,
					
				}
			]
		
		if payload.embed.metadata is not None:
			
			ydl_info.params['postprocessors'] += [
				{
					
					'key': 'FFmpegMetadata',
					'add_metadata': True,
					
				}
			]
		
		if 'writesubtitles' in payload.params or 'writeautomaticsub' in payload.params:
			
			ydl_info.params['postprocessors'] += [
				{
					
					'key': 'FFmpegEmbedSubtitle',
					'already_have_subtitle': False,
					
				}
			]
	
	# pprint.pprint (ydl_info.params)
	
	# YoutubeDL class is completely stateful. The constructor initializes the
	# internal postprocessor pipeline once upon creation based on the initial dictionary.
	# If we reuse the old `ydl_info` instance to call `process_video_result`, the new
	# postprocessors (MKA remuxing, thumbnail embedding) will be silently ignored because
	# the pipeline is hardlocked into the original video-scout state.
	with YoutubeDL (ydl_info.params) as ydl_downloader:
		
		try:
			
			if payload:
				
				if payload.type == 'audio':
					
					# Because we're using separated receiving video info and its downloading -
					# we need to filter formats list behind putting it to process_video_result.
					
					# 1. Locate only the pure m4a audio tracks in the full list of formats
					audio_formats = [
						f for f in info_dict['formats']
						if f.get ('vcodec') == 'none' and f.get ('ext') == 'm4a'
					]
					
					# If for some reason the .m4a file is missing (a rare occurrence) -
					# use any clean audio track.
					if not audio_formats:
						
						audio_formats = [
							f for f in info_dict['formats']
							if f.get ('vcodec') == 'none'
						]
					
					target_audio = audio_formats[-1]
					
					# 2. Force to change format data
					info_dict['format_id'] = target_audio['format_id']
					info_dict['ext'] = target_audio['ext']
					info_dict['vcodec'] = 'none'
					info_dict['acodec'] = target_audio.get ('acodec')
					info_dict['url'] = target_audio['url']
					
					# 3. We leave a single element in the `formats` list. Now, the yt-dlp re-selection
					# algorithms will have no alternatives left.
					info_dict['formats'] = [target_audio]
					
					# 4. Delete service keys that may have remained from the default video selection.
					keys_to_delete = ['requested_formats', 'format', 'requested_downloads']
					
					for key in keys_to_delete:
						if key in info_dict:
							del info_dict[key]
			
			# Execute the low-level custom core downloader method.
			# It processes mutated DTO (info_dict) and flawlessly fires up the entire
			# postprocessing pipeline inside the fresh, modern ydl_downloader context.
			info_dict = ydl_downloader.process_video_result (info_dict, download = True)  # type: ignore
			
			return make_response (
				'success',
				status.HTTP_200_OK,
				f'Video "{info_dict.get ("id")}" downloaded successfully',
				saved_to = ydl_downloader.prepare_filename (info_dict),
				video_id = info_dict.get ('id'),
				title = info_dict.get ('title')
			)
		
		except DownloadError as e:
			return make_response (
				'error',
				status.HTTP_403_FORBIDDEN,
				str (e),
				proxy = ydl_info.params.get ('proxy', None)
			)
		except ExtractorError as e:
			return make_response (
				'error',
				status.HTTP_403_FORBIDDEN,
				str (e),
				proxy = ydl_info.params.get ('proxy', None)
			)

def get_unique_filename (base_path: LiteralString | str | bytes, ext: str) -> str:
	
	"""Appends a counter index if the file already exists (e.g., file_1.webm)"""
	
	counter = 1
	
	new_path = f'{base_path}.{ext}'
	
	while os.path.exists (new_path):
		
		new_path = f'{base_path}_{counter}.{ext}'
		counter += 1
	
	return new_path

def _video_url (video_id: str) -> str:
	return f'https://www.youtube.com/watch?v={video_id}'

def _playlist_url (playlist_id: str) -> str:
	return f'https://www.youtube.com/playlist?list={playlist_id}'

def normalize_and_parse_cookies (raw_cookies: str) -> io.StringIO:
	
	"""
	Smart cookie parser.
	1. If the input is in Netscape format, it normalizes escaped newlines (\r\n, \\n, etc.).
	2. If the input is a raw HTTP header string, it converts it to Netscape format on the fly.
	Returns an in-memory io.StringIO stream ready for yt-dlp CookieJar.
	"""
	
	# Clean up standard escape sequences that might occur during JSON transport
	normalized = (
		raw_cookies
		.replace ('\\r\\n', '\n')
		.replace ('\\n', '\n')
		.replace ('\r\n', '\n')
	)
	
	# Check if the cleaned text represents a Netscape/Mozilla cookie jar structure
	if '# Netscape' in normalized or 'HTTP Cookie File' in normalized:
		
		verbose ('[INFO] Netscape formatted cookie string detected')
		
		return io.StringIO (normalized)
	
	# If it's not a Netscape format, treat it as a standard HTTP header string (Name=Value; Name2=Value2)
	verbose ('[INFO] Raw HTTP header cookie string detected. Converting to Netscape structure...')
	
	netscape_text = '# Netscape HTTP Cookie File\n'
	
	# Split the HTTP header string by semicolons to extract individual cookies
	pairs = normalized.split (';')
	
	for pair in pairs:
		
		if '=' not in pair:
			continue
		name, value = pair.strip ().split ('=', 1)
		
		# Standard Netscape fields: domain, include_subdomains, path, is_secure, expiry_timestamp, name, value
		# Target .youtube.com domain with far-future expiration timestamp (Unix maximum: Year 2038)
		netscape_text += f'.youtube.com\tTRUE\t/\tTRUE\t2147483647\t{name}\t{value}\n'
	
	return io.StringIO (netscape_text)

def make_response (
	status: str,
	code: int,
	message: str,
	**kwargs
) -> ApiResponse:
	
	"""
	Dynamically builds the response dictionary using kwargs to prevent redundancy.
	Applies the HTTP status code to the FastAPI Response object if provided.
	"""
	
	if status == 'success':
		
		return ApiResponse (
			status = status,
			code = code,
			message = message,
			data = kwargs
		)
	
	else:
		
		raise VideoDownloadError (
			status = status,
			code = code,
			message = message,
			data = kwargs
		)

def process_params (payload: InfoRequest):
	
	ydl_info.params['postprocessors'] = []
	ydl_info.params['js_runtimes'] = { 'node': { } }  # type: ignore
	ydl_info.params['remote_components'] = { 'ejs:npm' }  # type: ignore
	ydl_info.params['cookiefile'] = None
	ydl_info.params['cookiesfrombrowser'] = None
	ydl_info.params['http_headers'] = { }
	
	if payload:
		
		# if not shutil.which ('ffmpeg'):
		#	ydl_info.params['ffmpeg_location'] = imageio_ffmpeg.get_ffmpeg_exe ()
		
		# Safely merge custom user arguments from the JSON payload (the params dictionary)
		# The dictionary update () method is atomic, completely removing fragile manual loops
		ydl_info.params.update (payload.params)
		
		if payload.type == 'audio':
			
			if 'format' not in ydl_info.params:
				ydl_info.params['format'] = 'ba[acodec=m4a]/ba'
		
		# Inject cookies dynamically if passed in request
		if payload.cookies:
			
			try:
				
				# We convert raw Netscape string into an in-memory stream wrapper.
				# yt-dlp API reads it directly like a virtual disk file. No physical disk I/O!
				ydl_info.params['cookiefile'] = normalize_and_parse_cookies (payload.cookies)  # type: ignore
				
				verbose ('[INFO] Dynamic HTTP/Netscape cookie payload successfully injected into memory context')
			
			except Exception as e:
				make_response ('error', status.HTTP_502_BAD_GATEWAY, str (e))
		
		elif payload.cookies_browser:
			ydl_info.params['cookiesfrombrowser'] = (payload.cookies_browser, None, None, None)  # type: ignore
		
		if payload.proxies:
			ydl_info.params['proxy'] = random.choice (payload.proxies)
	
	if 'format' not in ydl_info.params:
		
		# If a video is only available in 4K using AV1, but only 1080p
		# in VP9, yt-dlp will choose the 4K AV1 stream to prevent losing resolution.
		# If YouTube stops serving H.264 (AVC) entirely, yt-dlp will
		# seamlessly fall back to AV1 without throwing errors or breaking the script.
		ydl_info.params['format_sort'] = ['res', 'vcodec:vp9', 'vcodec:avc']
	
	if 'merge_output_format' not in ydl_info.params:
		
		# Forces yt-dlp to mux the separate video and audio streams into an MKV container.
		# Requires FFmpeg to be installed on system.
		# It performs a direct copy (remux) without re-encoding, so it is instant
		# and preserves 100% of the original video and audio quality.
		ydl_info.params['merge_output_format'] = 'mkv'
	
	ydl_info.params['quiet'] = not args.get ('verbose')
	ydl_info.params['verbose'] = args.get ('verbose')
	
def check_proxy (
	proxy: str,
	video_id: str | None = None,
	timeout: int = 10,
	service: str = 'https://ident.me'
):
	
	proxies = {
		
		'http': proxy,
		'https': proxy,
		
	}
	
	requests.get (service, proxies = proxies, timeout = timeout)
	
	print (f'[SUCCESS] Proxy is working')
	
	# if ':' not in current_ip:
	#  print ('[WARNING] IPv6 proxy returns IPv4 address')
	
	if video_id:
		
		try:
			
			ydl_info.params['quiet'] = True
			ydl_info.params['verbose'] = False
			ydl_info.params['no_warnings'] = True
			ydl_info.params['proxy'] = proxy
			ydl_info.params['simulate'] = 'list_only'
			
			video_url = _video_url (video_id)
			
			ydl_info.extract_info (video_url, download = False)
			
			print ('[SUCCESS] Connected to YouTube successfully')
		
		except DownloadError as e:
			print (f'[ERROR] Can\'t connect: {e}. Maybe proxy network banned by YouTube')

def is_ffmpeg_available () -> bool:
	
	# 1. Searching for an executable file in the PATH (takes .exe extensions into account on Windows)
	ffmpeg_path = shutil.which ('ffmpeg')
	
	if not ffmpeg_path:
		return False
	
	try:
		
		# 2. Test run to verify the binary's functionality
		# The -version flag returns build information and terminates the process
		result = subprocess.run (
			[ffmpeg_path, '-version'],
			stdout = subprocess.PIPE,
			stderr = subprocess.PIPE,
			text = True,
			timeout = 5  # Protection against process hanging
		)
		
		# If the return code is 0, FFmpeg is guaranteed to be installed and working.
		return result.returncode == 0
	
	except (subprocess.SubprocessError, FileNotFoundError, OSError):
		return False

def search (col, name, list):
	return [element for element in list if element[col] == name]

def verbose (message):
	
	if args.get ('verbose'):
		print (message)
