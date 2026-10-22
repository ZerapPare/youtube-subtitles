import os
import re

from flask import Flask, jsonify, request, send_from_directory
from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

# On Vercel, files in public/ are served by the CDN; Flask only handles /api/*.
# Locally, Flask serves public/ itself.
app = Flask(__name__, static_folder="public", static_url_path="")


def make_client() -> YouTubeTranscriptApi:
    # YouTube blocks most cloud IPs (incl. Vercel), so a proxy is usually
    # required in production. Configure one via environment variables.
    if os.environ.get("WEBSHARE_PROXY_USERNAME"):
        return YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=os.environ["WEBSHARE_PROXY_USERNAME"],
                proxy_password=os.environ["WEBSHARE_PROXY_PASSWORD"],
            )
        )
    if os.environ.get("PROXY_URL"):
        url = os.environ["PROXY_URL"]
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(http_url=url, https_url=url)
        )
    return YouTubeTranscriptApi()


ytt = make_client()

VIDEO_ID_RE = re.compile(
    r"(?:v=|/shorts/|/embed/|/live/|youtu\.be/|/v/)([A-Za-z0-9_-]{11})"
)


def extract_video_id(url: str) -> str | None:
    url = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    m = VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def transcript_error(e: CouldNotRetrieveTranscript):
    if isinstance(e, NoTranscriptFound):
        return error("ไม่พบซับในภาษาที่เลือก", 404)
    if isinstance(e, TranscriptsDisabled):
        return error("คลิปนี้ปิดซับไตเติล หรือไม่มีซับ", 404)
    if isinstance(e, VideoUnavailable):
        return error("ไม่พบวิดีโอ หรือวิดีโอเป็นแบบส่วนตัว", 404)
    if isinstance(e, RequestBlocked):
        return error("YouTube บล็อกการเชื่อมต่อจากเซิร์ฟเวอร์นี้ (ต้องตั้งค่า proxy)", 503)
    return error("ดึงซับไม่ได้ ลองใหม่อีกครั้ง", 502)


def get_video_id_or_error():
    url = request.args.get("url", "")
    video_id = extract_video_id(url)
    if not video_id:
        return None, error("ลิงก์ YouTube ไม่ถูกต้อง")
    return video_id, None


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/languages")
def languages():
    video_id, err = get_video_id_or_error()
    if err:
        return err
    try:
        transcripts = ytt.list(video_id)
    except CouldNotRetrieveTranscript as e:
        return transcript_error(e)

    items = [
        {
            "code": t.language_code,
            "name": t.language,
            "generated": t.is_generated,
        }
        for t in transcripts
    ]
    # Manually-created subtitles first, then auto-generated
    items.sort(key=lambda x: x["generated"])
    return jsonify({"videoId": video_id, "languages": items})


@app.get("/api/transcript")
def transcript():
    video_id, err = get_video_id_or_error()
    if err:
        return err
    lang = request.args.get("lang", "")
    try:
        fetched = ytt.fetch(video_id, languages=[lang] if lang else ["th", "en"])
    except CouldNotRetrieveTranscript as e:
        return transcript_error(e)

    return jsonify(
        {
            "videoId": video_id,
            "language": fetched.language,
            "languageCode": fetched.language_code,
            "generated": fetched.is_generated,
            "segments": [
                {"start": s.start, "duration": s.duration, "text": s.text}
                for s in fetched.snippets
            ],
        }
    )


if __name__ == "__main__":
    # Debug mode must stay off when the site is exposed via a tunnel
    app.run(host="127.0.0.1", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
