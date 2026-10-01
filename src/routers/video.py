from fastapi import APIRouter, Header
from starlette import status
from yt_dlp.utils import DownloadError, ExtractorError

from schema import InfoRequest, ApiResponse, DownloadRequest
from utils import process_params, ydl_info, _video_url, make_response, process_single_video

router = APIRouter (
  prefix = '/video',
  tags = ['Videos']
)

@router.get ('/{video_id}')
def video_info (
	video_id: str,
	payload: InfoRequest | None = None
) -> ApiResponse:
	
	if video_id:
		
		process_params (payload)
		
		try:
			
			info_dict = ydl_info.extract_info (_video_url (video_id), download = False)
			
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
			'Missing video id'
		)
	
@router.put ('/{video_id}')
def download_video (
	video_id: str,
	payload: DownloadRequest | None = None,
	x_exists_action: str | None = Header (default = None, alias = 'X-Exists-Action')
) -> ApiResponse:
	
	process_params (payload)
	
	if video_id or (payload and payload.info):
		
		if not payload or not payload.info:
			
			try:
				info_dict = ydl_info.extract_info (_video_url (video_id), download = False)
			except DownloadError as e:
				return make_response ('error', status.HTTP_502_BAD_GATEWAY, str (e))
			except ExtractorError as e:
				return make_response ('error', status.HTTP_502_BAD_GATEWAY, str (e))
		
		else:
			info_dict = payload.info
		
		return process_single_video (payload, info_dict, x_exists_action)
	
	return make_response (
		'error',
		status.HTTP_400_BAD_REQUEST,
		'Missing video id'
	)