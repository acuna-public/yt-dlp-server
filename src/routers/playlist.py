import random

from fastapi import APIRouter, Header
from starlette import status
from yt_dlp.utils import DownloadError, ExtractorError

from schema import InfoRequest, ApiResponse, DownloadRequest
from utils import process_params, ydl_info, _playlist_url, make_response, verbose, process_single_video

router = APIRouter (
  prefix = '/playlist',
  tags = ['Playlists']
)

@router.get ('/{playlist_id}')
def playlist_info (
	playlist_id: str,
	payload: InfoRequest | None = None
) -> ApiResponse:
	
	if playlist_id:
		
		process_params (payload)
		
		try:
			
			info_dict = ydl_info.extract_info (_playlist_url (playlist_id), download = False)
			
			return ApiResponse (
				status = 'success',
				code = status.HTTP_200_OK,
				data = info_dict
			)
		
		except DownloadError as e:
			return make_response (
				'error',
				status.HTTP_406_NOT_ACCEPTABLE,
				str (e)
			)
		except ExtractorError as e:
			return make_response (
				'error',
				status.HTTP_406_NOT_ACCEPTABLE,
				str (e)
			)
	
	else:
		return make_response (
			'error',
			status.HTTP_400_BAD_REQUEST,
			'Missing playlist id'
		)

@router.put ('/{playlist_id}')
def download_playlist (
	playlist_id: str,
	payload: DownloadRequest | None = None,
	x_exists_action: str | None = Header (default = None, alias = 'X-Exists-Action')
) -> ApiResponse:
	
	try:
		playlist_data = ydl_info.extract_info (_playlist_url (playlist_id), download = False)
	except DownloadError as e:
		return make_response ('error', status.HTTP_502_BAD_GATEWAY, str (e))
	except ExtractorError as e:
		return make_response ('error', status.HTTP_502_BAD_GATEWAY, str (e))
	
	if not playlist_data:
		return make_response ('error', status.HTTP_404_NOT_FOUND, 'Playlist not found')
	
	entries = list (playlist_data['entries'])  # type: ignore
	
	for index, entry in enumerate (entries, start = 1):
		
		if not entry:
			continue
		
		verbose (f'[PLAYLIST QUEUE] Processing {index} / {len (entries)} (Video ID: {entry.get ("id")})')
		
		if payload.proxies:
			ydl_info.params['proxy'] = random.choice (payload.proxies)
		else:
			ydl_info.params['proxy'] = None
		
		process_single_video (payload, entry, x_exists_action)
	
	return make_response (
		'success',
		status.HTTP_200_OK,
		f'Processed {len (entries)} items from playlist',
		playlist_title = playlist_data.get ('title')
	)