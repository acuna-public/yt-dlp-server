# REST API server for yt-dlp

A convenient and powerful production-ready REST API server for [yt-dlp](https://github.com/yt-dlp/yt-dlp) built with **FastAPI**.
Provides a fully automated background service that allows you to download videos and
whole playlists, smart proxy rotation and cookies support. Working as REST HTTP service so you can
use it as backend for you multi-language applications which supports network layer HTTP queries.

## Features

- **Background Daemon:** Runs continuously as an HTTP server waiting for requests.
- **Cookies support:** Supports Netscape format and RAW strings cookies.
- **Whole playlists downloading:** Just set playlist id to parse and download it.
- **Smart Hybrid Proxying:** Proxies list supports, proxies changes randomly every query
automatically.
- **Advanced Deduplication (`X-Exists-Action`):** Supports `rename` (auto-indexing),
`smaller` (overwriting broken chunks), or `error` policies.
- **JSON Standardization:** Production-grade error handling. Standard `yt-dlp` API exceptions
handled as JSON responses for best HTTP experience.
- **yt-dlp community reliance:** Working as wrapper for `yt-dlp` so just execute the
`pip install -U yt-dlp` command in console if YouTube algorithms changed and `yt-dlp` handle
it to keep the fun going.
- **Industrial standards following:** Fully REST-architecture, well commented, clean and robust
codebase.

## Installation

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/acuna-public/yt-dlp-server
   cd YOUR_REPO_NAME
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Required:** Ensure you have `ffmpeg` installed on your system or place `ffmpeg.exe` right next to `server.py` so the service can merge separate audio and video streams together.

## Usage

Start the service with `run.bat`.

The server will boot up on `http://127.0.0.1:8000` waiting for service the queries.

### API Endpoints

**`GET /video/{video_id}`**

Getting the video info by its identifier.

#### Query Parameters:
- `video_id` (Required): YouTube video identifier.

#### Body Parameters:
- `proxies` (Optional): A JSON-encoded string array containing proxy endpoints.
Supports IPv4, IPv6, and SOCKS5.



**`GET /playlist/{playlist_id}`**

Getting the playlist info by its identifier.

#### Query Parameters:
- `playlist_id` (Required): YouTube playlist identifier.

#### Body Parameters:
- `proxies` (Optional): A JSON-encoded string array containing proxy endpoints.
Supports IPv4, IPv6, and SOCKS5.

**`PUT /video/{video_id}`**

Downloads video

#### Query Parameters:
- `video_id` (Required): YouTube video identifier.

#### Body Parameters:
- `name` (Optional): Preferred filename without extension (will be an `yt-dlp` default if not set).
- `download_dir` (Required): Folder where video will be downloaded.
- `type` (Optional): Type of the downloaded video (audio or video).
If you set `audio` - only audio stream will be downloaded.
- `embed` (Optional): Data type to embed in video file. Set it to dictionary `{'metadata': {}}`
to add metadata to the video file. For another types use `params` to add custom `YoutubeDL`
parameters like `writethumbnail`, `writesubtitles`, `writeautomaticsub` etc.
- `params` (Optional): custom `YoutubeDL` parameters (`sleep_interval`, `max_sleep_interval`,
`ratelimit` etc.). Follow `yt-dlp` API manual to get its list.
- `proxies` (Optional): A JSON-encoded string array containing proxy endpoints.
Supports IPv4, IPv6, and SOCKS5.

#### Headers:
- `X-Exists-Action` (Optional): Strategy for existing files.
Options: `skip` (default), `rename`, `smaller`, `error`.

**`PUT /playlist/{playlist_id}`**

Downloads whole playlist videos

#### Query Parameters:
- `playlist_id` (Required): YouTube playlist identifier.

#### Body Parameters:
- `name` (Optional): Preferred filename without extension (will be an `yt-dlp` default if not set).
- `download_dir` (Required): Folder where all videos will be downloaded.
- `type` (Optional): Type of the downloaded video (audio or video).
If you set `audio` - only audio stream will be downloaded.
- `embed` (Optional): Data type to embed in video file. Set it to dictionary `{'metadata': {}}`
to add metadata to the video file. For another types use `params` to add custom `YoutubeDL`
parameters like `writethumbnail`, `writesubtitles`, `writeautomaticsub` etc.
- `params` (Optional): custom `YoutubeDL` parameters (`sleep_interval`, `max_sleep_interval`,
`ratelimit` etc.). Follow `yt-dlp` API manual to get its list.
- `proxies` (Optional): A JSON-encoded string array containing proxy endpoints .
Supports IPv4, IPv6 and SOCKS5.

#### Headers:
- `X-Exists-Action` (Optional): Strategy for existing files.
Options: `skip` (default), `rename`, `smaller`, `error`.

## Examples

[Official Postman collection](https://orbital-module-cosmologist-52990594-s-team.postman.co/workspace/Personal-Workspace~634a97fe-e97b-4ec5-8ed9-2c411b96e1bf/collection/32397565-86cbaf19-ceeb-473b-b205-1c3c8631956d?action=share&creator=32397565)
is a good starting point for your experiments.

## License
Apache 2.0
