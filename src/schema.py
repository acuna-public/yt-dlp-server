from typing import Optional, Any, Literal, Annotated

from pydantic import BaseModel, Field, BeforeValidator

class InfoRequest (BaseModel):
	
	type: Literal['video', 'audio'] = 'video'
	proxies: list = Field (default_factory = list)
	cookies: str | None = None
	cookies_browser: str | None = None
	params: dict = Field (default_factory = dict)
	
def fix_php_empty_array (value):
	
	if isinstance (value, list) and len (value) == 0:
		return {}
	
	return value
	
PHPArrayDict = Annotated[dict, BeforeValidator (fix_php_empty_array)]

class EmbedModel (BaseModel):
	
	metadata: PHPArrayDict = None
	
class DownloadRequest (InfoRequest):
	
	download_dir: str | None = None
	name: str | None = None
	chapter_name: str | None = None
	info: dict | None = None
	embed: EmbedModel = EmbedModel ()
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