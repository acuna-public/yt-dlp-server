from urllib.request import Request

from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.responses import JSONResponse
import logging

from schema import VideoDownloadError, ApiResponse

logger = logging.getLogger ('uvicorn.error')

async def video_download_error_handler (request: Request, exc: VideoDownloadError):
	return JSONResponse (
		status_code = exc.code,
		content = ApiResponse (
			status = exc.status,
			code = exc.code,
			message = exc.message,
			data = exc.data,
		).model_dump ()
	)

async def validation_exception_handler (request: Request, exc: RequestValidationError):
	
	"""
	Data validation Interceptor
	"""
	
	# Write the traceback to the console for debug
	logger.error (str (exc), exc_info = True)
	
	errors = exc.errors ()
	
	if errors:
		
		first_err = errors[0]
		
		# For example: "body -> url: Field required"
		loc = ' -> '.join (str (x) for x in first_err.get ('loc', []))
		
		msg = first_err.get ('msg', 'Invalid value')
		error_message = f'Data validation error: [{loc}] {msg}'
	
	else:
		error_message = 'Invalid input data format'
	
	return JSONResponse (
		status_code = status.HTTP_422_UNPROCESSABLE_CONTENT,
		content = ApiResponse (
			status = 'error',
			code = status.HTTP_422_UNPROCESSABLE_CONTENT,
			message = error_message,
			data = errors
		).model_dump ()
	)
	
async def universal_exception_handler (request: Request, exc: Exception):
	
	"""
	Critical Failure Interceptor (500 Internal Server Error)
	"""
	
	# Write the traceback to the console for debug
	logger.error (str (exc), exc_info = True)
	
	return JSONResponse (
		status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
		content = ApiResponse (
			status = 'error',
			code = status.HTTP_500_INTERNAL_SERVER_ERROR,
			message = str (exc)
		).model_dump ()
	)