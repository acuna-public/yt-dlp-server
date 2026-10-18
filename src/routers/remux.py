import pathlib

from fastapi import APIRouter
from starlette import status
from yt_dlp import FFmpegVideoRemuxerPP

from schema import RemuxRequest, ApiResponse
from utils import make_response

router = APIRouter (
  prefix = '/remux',
  tags = ['Remux']
)

@router.post ('')
def remux (
	request: RemuxRequest
) -> ApiResponse:
	
	if not request.input_file:
		return make_response (
			'error',
			status.HTTP_400_BAD_REQUEST,
			'Missing input file'
		)
		
	if not request.format:
		return make_response (
			'error',
			status.HTTP_400_BAD_REQUEST,
			'Missing format'
		)
		
	remuxer = FFmpegVideoRemuxerPP (preferedformat = request.format)
	
	try:
		
		input_path = pathlib.Path (request.input_file)
		
		files_to_delete, updated_info = remuxer.run ({
			
			'filepath': request.input_file,
			'ext': input_path.suffix,
			
		})
		
		return make_response (
			status = 'success',
			code = status.HTTP_200_OK,
			message = 'File remuxed successfully',
			saved_to = updated_info['filepath']
		)
		
	except Exception as e:
		
		return make_response (
			'error',
			status.HTTP_500_INTERNAL_SERVER_ERROR,
			str (e)
		)