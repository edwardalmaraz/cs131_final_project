from dataclasses import dataclass, field
import json

# TODO
#test song file 
#be able to add a new leardboard entry when game starting a new game 
#start game/new game backend button
#


@dataclass
class Pose:
    pose_id : int = 0
    timestamp_ms: int = 0 #in MS
    image_path : str = ""

@dataclass
class Lyric:
    text : str = ""
    timestamp_ms: int = 0 #in MS

@dataclass
class Song:
    song_title : str = "a"
    artist_name : str = "b"
    song_id : int = 0
    poses : list[Pose] = field(default_factory = list)
    #default factory = instead of using a fixed default value, call this function every time a new instance is created, and use whatever it returns as the default.
    lyrics: list[Lyric] = field(default_factory = list)
    audio_path : str = "c"

    @classmethod
    def from_json(cls, path):
        with open(path, "r") as file:
            data = json.load(file)

        lyrics = []

        for lyric_data in data["lyrics"]:
            lyric = Lyric(
                text=lyric_data["text"],
                timestamp_ms=lyric_data["timestamp_ms"]
            )
            lyrics.append(lyric)

        poses = []

        for pose_data in data["pose_images"]:
            pose = Pose(
                pose_id=pose_data["pose_id"],
                timestamp_ms=pose_data["timestamp_ms"],
                image_path=pose_data["image_path"]
            )
            poses.append(pose)

        return cls(
            song_title=data["song_title"],
            artist_name=data["artist_name"],
            song_id=data["song_id"],
            audio_path=data["audio_path"],
            poses=poses,
            lyrics=lyrics
        )

@dataclass
class Score:
    total_score: int = 0

@dataclass
class LeaderboardEntry:
    player_name : str = "player1"
    score : int = 1
    rank : int = 2

@dataclass
class Leaderboard:
    song_id : int = 0
    entries : list[LeaderboardEntry] = field(default_factory=list)
    #field = confige multiple types variables