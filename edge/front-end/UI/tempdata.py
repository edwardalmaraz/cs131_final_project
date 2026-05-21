from .models import Song, Pose, Lyric

The_Feels = Song(song_title = "The Feels", 
                 artist_name = "Twice", 
                 song_id = 1, 
                 poses = [
                    Pose(pose_id = 1, timestamp_ms = 5000, image_path = "poses/pose1.png"),
                    Pose(pose_id = 2, timestamp_ms = 10000, image_path = "poses/pose2.png"),
                    Pose(pose_id = 3, timestamp_ms = 15000, image_path = "poses/pose1.png"),
                    Pose(pose_id = 4, timestamp_ms = 20000, image_path = "poses/pose2.png"),
                    Pose(pose_id = 5, timestamp_ms = 25000, image_path = "poses/pose1.png"),
                    Pose(pose_id = 6, timestamp_ms = 30000, image_path = "poses/pose2.png"),
                    Pose(pose_id = 7, timestamp_ms = 35000, image_path = "poses/pose1.png"),
                    Pose(pose_id = 8, timestamp_ms = 40000, image_path = "poses/pose2.png"),
                 ],

                 lyrics = [
                    Lyric(text = " ", timestamp_ms = 0),
                    Lyric(text = "Uh, I'm so curious", timestamp_ms = 5000),
                    Lyric(text = "Bout you, boy, wanna keep it cool", timestamp_ms = 10000),
                    Lyric(text = "But I know every time you move, got me frozen", timestamp_ms = 15000),
                    Lyric(text = "I get so shy, it's obvious (get ya)", timestamp_ms = 20000),
                    Lyric(text = "Catching feels like butterflies", timestamp_ms = 25000),
                    Lyric(text = "If I say what's on my mind", timestamp_ms = 30000),
                    Lyric(text = "If I say what's on my mind", timestamp_ms = 35000),
                    Lyric(text = "", timestamp_ms = 40000)
                 ]                                   
)
