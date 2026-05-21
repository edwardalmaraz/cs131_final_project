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

        for pose_data in data["poses"]:
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
    
#testing

# #test Song
# test_song = Song(song_title = "Hello", artist_name = "Adele", song_id = 1)
# print("Song Title:", test_song.song_title,  "Artist Name:", test_song.artist_name, "Song ID:", test_song.song_id)
# print()

# #test Score (adjust fields based on what you decide to include)
# Test_score = Score(total_score=87)
# print("Score Test:", Test_score.total_score)
# print()

# #test LeaderboardEntry
# test_entry = LeaderboardEntry(player_name = "Hanson", score = 95, rank = 1)
# print("LeaderboardEntry Entry Name:", test_entry.player_name, "LeaderboardEntry Score:", test_entry.score, "Rank:", test_entry.rank)
# print()

# #test Leaderboard with a list of entries
# test_leaderboard = Leaderboard(
#     song_id=1,
#     entries=[
#         LeaderboardEntry(player_name="Z", score = 95, rank = 1),
#         LeaderboardEntry(player_name="Edward", score = 88, rank = 2),
#         LeaderboardEntry(player_name="Hanson", score = 85, rank = 3),
#         LeaderboardEntry(player_name="Andy", score = 83, rank = 4),
#     ]
# )

# print("Leaderboard works:", test_leaderboard)

# #test default empty list
# # empty_leaderboard = Leaderboard(song_id = 2 )
# # print("Empty leaderboard works:", empty_leaderboard)
# # print()

# #test poses
# #test_pose = Pose(pose_id = 0, timestamp_ms = 100, image_path = "1.png")

# #testing song & song
# test_song = Song(song_title = "twice", 
#                  artist_name = "twice", 
#                  song_id = 1, 
#                  poses = [
#                     Pose(pose_id = 0, timestamp_ms = 100, image_path = "1.png"),
#                     Pose(pose_id = 2, timestamp_ms = 500, image_path = "2.png")
#                  ], 
#                  lyrics = [
#                     Lyric(text = "Uh, I'm so curious", timestamp_ms = 200),
#                     Lyric(text = "'Bout you, boy, wanna keep it cool", timestamp_ms = 400)
#                  ]
# )

# print("Song Title:", test_song.song_title)
# print("Artist Name:", test_song.artist_name)
# print("Song ID:", test_song.song_id)
# print("Poses:")
# for pose in test_song.poses:
#     print(" ", pose)
# print()

# #testing lyrics
# for lyric in test_song.lyrics:
#     print(" ", lyric)
# print()
