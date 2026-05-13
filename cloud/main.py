from fastapi import FastAPI, UploadFile, File, Form
from database import *
from pydantic import BaseModel
from scoring.text import score_lyrics

app = FastAPI()

#items uses for when the jetson asks to compute the lyrics score 
#when 
class lyric_score_request(BaseModel):
    song_id: str
    player_id: str
    player_transcript: str

class lyric_score_response(BaseModel):
    player_id: str
    lyric_score: float

class pitch_score_response(BaseModel):
    player_id: str
    pitch_score: float


#when first starting the fastAPI server, root starts with an HTML page of hello world
@app.get("/")
def read_root():
    return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str | None = None):
#     return {"item_id": item_id, "q": q}

#When the jetson sends the final transcript at the end of the game, calculate score 
@app.post("/score/lyrics", response_model=lyric_score_response)
async def compute_score(request: lyric_score_request):
    #grab lyrics from song DB
    lyrics = get_song_lyrics(request.song_id)
    #compute score using lyric text function
    result = score_lyrics(request.player_transcript, lyrics)
    #save score to leaderboard DB 
    save_score(request.player_id, result, request.song_id)
    return lyric_score_response(player_id=request.player_id, lyric_score=result)

#extracting song pitch, comparing for additional score


#testing api, grabbing song lyrics 
@app.get("/songs/{song_id}")
async def get_song(song_id: str):
    lyrics = get_song_lyrics(song_id)
    return {"song_id": song_id, "lyrics": lyrics}
