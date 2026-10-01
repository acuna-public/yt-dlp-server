from fastapi import APIRouter
from starlette import status

from schema import ApiResponse
from utils import make_response, ydl_info

router = APIRouter (
  prefix = '/cache',
  tags = ['Cache']
)

@router.delete ('/')
def clean_cache () -> ApiResponse:
	
	ydl_info.cache.remove ()
	
	return make_response (
		'success',
		status.HTTP_200_OK,
		'Cache cleaned successfully'
	)