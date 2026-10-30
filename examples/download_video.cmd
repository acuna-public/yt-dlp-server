curl --location --request GET 'http://127.0.0.1:8000/video?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3Dvideo_id' \
--header 'X-Exists-Action: rewrite' \
--header 'Content-Type: application/json' \
--data '{
    "writesubtitles": true,
    "writeautomaticsub": true,
    "windowsfilenames": true
}'