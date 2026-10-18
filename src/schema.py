from typing import Optional, Any, Literal, Annotated

from pydantic import BaseModel

class InfoRequest (BaseModel):
  
  type: Literal['video', 'audio'] = 'video'
  proxies: list = []
  cookies: str | None = None
  cookies_browser: str | None = None
  embed: list = []
  params: dict = {}
  
class DownloadRequest (InfoRequest):
	
  info: dict | None = None
  download_dir: str | None = None
  outtmpl: dict = {}
  makedir: bool = True
  
class ApiResponse (BaseModel):
  
  status: str
  code: int
  message: str | None = None
  data: Optional[Any] = []
  
class VideoDownloadError (Exception):
  
  def __init__ (self, status: str, code: int, message: str, data):
    
    self.status = status
    self.code = code
    self.message = message
    self.data = data
    
class RemuxRequest (BaseModel):
	
  input_file: str | None = None
  format: str | None = None
  
class SilentLogger:
  
  def debug (self, msg): pass
  def warning (self, msg): pass
  def error (self, msg): pass