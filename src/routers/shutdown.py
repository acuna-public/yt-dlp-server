import os
import signal

from fastapi import APIRouter, BackgroundTasks
from starlette import status

from schema import ApiResponse
from utils import make_response

router = APIRouter (
  prefix = '/shutdown',
  tags = ['Shutdown']
)

def shutdown_server ():
	os.kill (os.getpid (), signal.SIGINT)

@router.get ('/')
def shutdown (
	background_tasks: BackgroundTasks
) -> ApiResponse:
	
	"""
	Shutdown the server by query, use it if you want to shut down downloading from browser,
	but you need to start the server manually after it.
	"""
	
	background_tasks.add_task (shutdown_server)
	
	return make_response (
		'success',
		status.HTTP_200_OK,
		'Server shutting down...'
	)