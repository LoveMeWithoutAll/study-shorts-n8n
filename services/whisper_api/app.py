import os
import tempfile
from datetime import timedelta
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, Request
from pydantic import BaseModel
from faster_whisper import WhisperModel

app = FastAPI()

MODEL_NAME = os.getenv("WHISPER_MODEL", "medium")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ko")
BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
VAD_FILTER = os.getenv("WHISPER_VAD_FILTER", "true").lower() == "true"

model = WhisperModel(MODEL_NAME, device="cpu", compute_type=COMPUTE_TYPE)


def format_srt_time(seconds: float) -> str:
    millis = int(seconds * 1000)
    hours = millis // 3600000
    minutes = (millis % 3600000) // 60000
    secs = (millis % 60000) // 1000
    ms = millis % 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def segments_to_srt(segments: List[dict]) -> str:
    lines = []
    for idx, seg in enumerate(segments, start=1):
        start = format_srt_time(seg["start"])
        end = format_srt_time(seg["end"])
        text = seg["text"].strip()
        lines.append(str(idx))
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


@app.get("/healthz")
def healthz():
    return {"status": "ok", "model": MODEL_NAME, "compute_type": COMPUTE_TYPE}


@app.post("/transcribe")
async def transcribe(
    request: Request,
    file: UploadFile | None = File(default=None),
    language: str = Form(default=LANGUAGE),
):
    if file is None:
        form = await request.form()
        for value in form.values():
            if isinstance(value, UploadFile):
                file = value
                break
    raw_bytes = None
    if file is None:
        raw_bytes = await request.body()
        if not raw_bytes:
            return {"error": "no file uploaded"}

    if file is not None:
        suffix = os.path.splitext(file.filename or "audio")[1]
    else:
        ctype = (request.headers.get("content-type") or "").lower()
        if "mp4" in ctype:
            suffix = ".mp4"
        elif "mpeg" in ctype:
            suffix = ".mp3"
        elif "wav" in ctype:
            suffix = ".wav"
        else:
            suffix = ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        if file is not None:
            tmp.write(await file.read())
        else:
            tmp.write(raw_bytes)
        tmp_path = tmp.name

    segments, info = model.transcribe(
        tmp_path,
        language=language,
        beam_size=BEAM_SIZE,
        vad_filter=VAD_FILTER,
    )

    seg_list = []
    transcript = []
    for seg in segments:
        seg_list.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text.strip(),
        })
        transcript.append(seg.text.strip())

    srt = segments_to_srt(seg_list)

    os.unlink(tmp_path)

    return {
        "language": language,
        "duration": float(getattr(info, "duration", 0.0)),
        "transcript": " ".join(transcript).strip(),
        "segments": seg_list,
        "srt": srt,
    }


class TranscribePathRequest(BaseModel):
    input_path: str
    language: str = LANGUAGE


@app.post("/transcribe_path")
def transcribe_path(req: TranscribePathRequest):
    segments, info = model.transcribe(
        req.input_path,
        language=req.language,
        beam_size=BEAM_SIZE,
        vad_filter=VAD_FILTER,
    )

    seg_list = []
    transcript = []
    for seg in segments:
        seg_list.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text.strip(),
        })
        transcript.append(seg.text.strip())

    srt = segments_to_srt(seg_list)

    return {
        "language": req.language,
        "duration": float(getattr(info, "duration", 0.0)),
        "transcript": " ".join(transcript).strip(),
        "segments": seg_list,
        "srt": srt,
    }
