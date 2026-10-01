from fastapi.exceptions import RequestValidationError

from fastapi import FastAPI

from handlers import validation_exception_handler, video_download_error_handler, universal_exception_handler
from schema import VideoDownloadError

from routers.video import router as video_router
from routers.playlist import router as playlist_router
from routers.cache import router as cache_router
from routers.shutdown import router as shutdown_router

app = FastAPI (title = 'YouTube Downloader Service')

app.add_exception_handler (RequestValidationError, validation_exception_handler)
app.add_exception_handler (VideoDownloadError, video_download_error_handler)
app.add_exception_handler (Exception, universal_exception_handler)

app.include_router (video_router)
app.include_router (playlist_router)
app.include_router (cache_router)
app.include_router (shutdown_router)