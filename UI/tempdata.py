from models import Song, Pose, Lyric

The_Feels = Song(song_title = "The Feels", 
                 artist_name = "Twice", 
                 song_id = 1, 
                 poses = [
                    Pose(pose_id = 1, timestamp_ms = 100, image_path = "1.png"),
                    Pose(pose_id = 2, timestamp_ms = 100, image_path = "2.png"),
                    Pose(pose_id = 3, timestamp_ms = 100, image_path = "1.png"),
                    Pose(pose_id = 4, timestamp_ms = 100, image_path = "1.png"),
                    Pose(pose_id = 5, timestamp_ms = 100, image_path = "1.png"),
                    Pose(pose_id = 6, timestamp_ms = 100, image_path = "1.png"),
                    Pose(pose_id = 7, timestamp_ms = 100, image_path = "1.png"),
                    Pose(pose_id = 8, timestamp_ms = 100, image_path = "1.png"),
                    Pose(pose_id = 9, timestamp_ms = 100, image_path = "1.png"),
                 ],

                 lyrics = [
                    Lyric(text = "Boy, I, boy, I, boy, I know", timestamp_ms = 100),
                    Lyric(text = "I know you got the feels", timestamp_ms = 100),
                    Lyric(text = "Boy, I, boy, I, boy, I know", timestamp_ms = 100),
                    Lyric(text = "Uh, I'm so curious", timestamp_ms = 100),
                    Lyric(text = "Bout you, boy, wanna keep it cool", timestamp_ms = 100),
                    Lyric(text = "But I know every time you move, got me frozen", timestamp_ms = 100),
                    Lyric(text = "I get so shy, it's obvious (get ya)", timestamp_ms = 100),
                    Lyric(text = "Catching feels like butterflies", timestamp_ms = 100),
                    Lyric(text = "If I say what's on my mind", timestamp_ms = 100),
                 ]                                   
)
