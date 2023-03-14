from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess_eye

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Position(BaseModel):
    fen: str


class Error(BaseModel):
    error: str


@app.post("/api/detect/{to_play}", response_model=Position)
def detect(
    file: UploadFile = File(...),
    to_play: str = "white",
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        return Error(error="Invalid file type. Must be JPG, JPEG, or PNG.")

    if to_play not in ["white", "black"]:
        return Error(error="Invalid to_play parameter. Must be 'white' or 'black'.")

    image_data = file.file.read()
    fen = chess_eye.get_fen(image_data, to_play)
    if len(fen) > 0:
        return Position(fen=fen)
    else:
        return Error(error="Unable to detect position")
