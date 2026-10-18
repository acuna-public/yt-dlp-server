from fastapi import APIRouter, Header
from starlette import status
from yt_dlp.utils import DownloadError, ExtractorError

from schema import InfoRequest, ApiResponse, DownloadRequest
from utils import process_params, ydl_info, make_response, process_single_video

router = APIRouter (
  prefix = '/video',
  tags = ['Videos']
)

@router.get ('')
def video_info (
	url: str | None = None,
	payload: InfoRequest | None = None
) -> ApiResponse:
	
	if url:
		
		process_params (payload)
		
		try:
			
			info_dict = ydl_info.extract_info (url, download = False)
			
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
			'Missing video url'
		)
		
@router.put ('')
def download_video (
	url: str | None = None,
	payload: DownloadRequest | None = None,
	x_exists_action: str | None = Header (default = None, alias = 'X-Exists-Action')
) -> ApiResponse:
	
	if url or payload.info:
		
		process_params (payload)
		
		if url:
			
			try:
				info_dict = ydl_info.extract_info (url, download = False)
			except DownloadError as e:
				return make_response ('error', status.HTTP_502_BAD_GATEWAY, str (e))
			except ExtractorError as e:
				return make_response ('error', status.HTTP_502_BAD_GATEWAY, str (e))
			
		else:
			info_dict = payload.info
		
		return process_single_video (payload, info_dict, x_exists_action)
		
	else:
		
		return make_response (
			'error',
			status.HTTP_400_BAD_REQUEST,
			'Missing video url or info'
		)