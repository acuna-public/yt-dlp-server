import uvicorn

from app import app
from utils import args

if __name__ == '__main__':
  uvicorn.run (app, host = '127.0.0.1', port = args.get ('port'))