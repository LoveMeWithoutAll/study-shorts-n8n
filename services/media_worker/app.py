import os
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

MEDIA_FONT = os.getenv("MEDIA_FONT", "Noto Sans CJK KR")

class RenderShortRequest(BaseModel):
    input_path: str
    srt_path: str
    output_path: str
    start_sec: float
    end_sec: float

class ThumbnailRequest(BaseModel):
    input_path: str
    output_path: str
    time_sec: float
    text: str = Field(default="")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "font": MEDIA_FONT}

@app.post("/render_short")
def render_short(req: RenderShortRequest):
    vf = (
        "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
        "scale=1080:1920,"
        f"subtitles={req.srt_path}:force_style='FontName={MEDIA_FONT},FontSize=54,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=3,Outline=2,Shadow=1'"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(req.start_sec),
        "-to",
        str(req.end_sec),
        "-i",
        req.input_path,
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "22",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        req.output_path,
    ]
    subprocess.check_call(cmd)
    return {"output_path": req.output_path}

@app.post("/thumbnail")
def thumbnail(req: ThumbnailRequest):
    draw = (
        f"drawtext=font='{MEDIA_FONT}':"
        f"text='{req.text}':x=(w-text_w)/2:y=h*0.12:fontsize=64:"
        "fontcolor=white:borderw=4:bordercolor=black"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(req.time_sec),
        "-i",
        req.input_path,
        "-vframes",
        "1",
        "-vf",
        draw,
        req.output_path,
    ]
    subprocess.check_call(cmd)
    return {"output_path": req.output_path}
