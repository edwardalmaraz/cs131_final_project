import os
import pygame
from record import start_recording, stop_recording
from comparsion_pose import parse_pose_sequence_data, parse_frame_data, compare_sequence_to_frames, total_accuracy


# snapshot pose data to a file every 5 seconds
# imported from posenet example code
POSE_OUTPUT_FILE = "player_poses/pose_locations.txt"
os.makedirs(os.path.dirname(POSE_OUTPUT_FILE), exist_ok=True)

# file needed for pose comparison, which is used to calculate the score at the end of the game
POSE_COMPARISON_FILE = "songs/metadata.json"
os.makedirs(os.path.dirname(POSE_COMPARISON_FILE), exist_ok=True)
POSE_SNAPSHOT_INTERVAL_MS = 5000



def _write_pose_snapshot(state, current_song_time_ms):
    poses = state.get("poses", [])
    camera = state.get("pose_camera")
    elapsed = current_song_time_ms / 1000.0

    with open(POSE_OUTPUT_FILE, "a") as f:
        f.write(f"\n=== Timestamp: {elapsed:.1f}s ===\n")
        if not poses:
            f.write("  No poses detected\n")
            return
        for pose in poses:
            neck_kp = None
            for kp in pose.Keypoints:
                if camera.available and camera.net.GetKeypointName(kp.ID) == "neck":
                    neck_kp = kp
                    break
            if neck_kp is not None:
                f.write("    Direction Vectors (relative to neck):\n")
                for kp in pose.Keypoints:
                    name = camera.net.GetKeypointName(kp.ID)
                    if name == "neck":
                        continue
                    vec_x = neck_kp.x - kp.x
                    vec_y = neck_kp.y - kp.y
                    f.write(f"      neck -> {name}: ({vec_x:.1f}, {vec_y:.1f})\n")
            else:
                f.write("    Neck not detected, skipping direction vectors\n")


def handle_events(state):
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            state["run"] = False

        if e.type == pygame.MOUSEBUTTONDOWN:
            if state["current_display"] == "start_screen":
                pass

            elif state["current_display"] == "gameplay":
                if state["button_rect"].collidepoint(e.pos):
                    if state["game_state"] == "not_started":
                        state["song_start_time"] = pygame.time.get_ticks()
                        state["pose_last_snapshot_song_time_ms"] = 0
                        state["game_state"] = "playing"
                        state["button_text"] = state["button_font"].render("PAUSE", True, state["BLACK"])
                        if state["music_loaded"]:
                            pygame.mixer.music.play()
                        start_recording()

                    elif state["game_state"] == "playing":
                        state["pause_start_time"] = pygame.time.get_ticks()
                        state["game_state"] = "paused"
                        state["button_text"] = state["button_font"].render("PLAY", True, state["BLACK"])
                        if state["music_loaded"]:
                            pygame.mixer.music.pause()
                        stop_recording()

                    elif state["game_state"] == "paused":
                        paused_duration = pygame.time.get_ticks() - state.get("pause_start_time", 0)
                        state["song_start_time"] += paused_duration
                        state["game_state"] = "playing"
                        state["button_text"] = state["button_font"].render("PAUSE", True, state["BLACK"])
                        if state["music_loaded"]:
                            pygame.mixer.music.unpause()

            elif state["current_display"] == "leaderboard":
                pass

        if e.type == pygame.KEYDOWN:
            if state["current_display"] == "start_screen":
                if e.key == pygame.K_1:
                    state["current_display"] = "gameplay"
                    with open(POSE_OUTPUT_FILE, "w") as f:
                        f.write("")
                elif e.key == pygame.K_2:
                    print("online library - not built yet")
                elif e.key == pygame.K_3:
                    state["current_display"] = "leaderboard"

            elif state["current_display"] == "gameplay":
                if e.key == pygame.K_ESCAPE:
                    if state["game_state"] == "paused" or state["game_state"] == "not_started":
                        state["game_state"] = "not_started"
                        state["current_lyrics_index"] = 1
                        state["current_pose_index"] = 0
                        state["button_text"] = state["button_font"].render("START", True, state["BLACK"])
                        if state["music_loaded"]:
                            pygame.mixer.music.stop()
                        stop_recording()
                        state["current_display"] = "start_screen"

            elif state["current_display"] == "leaderboard":
                if e.key == pygame.K_ESCAPE or e.key == pygame.K_DELETE:
                    state["current_display"] = "start_screen"

            elif state["current_display"] == "end_screen":
                if e.key == pygame.K_RETURN:
                    state["current_display"] = "start_screen"


def update_state(state):
    # advance lyric/pose indices while playing
    if state.get("game_state") == "playing":
        current_song_time = pygame.time.get_ticks() - state.get("song_start_time", 0)

        if state["current_lyrics_index"] + 1 < len(state["LOADED_SONG"].lyrics):
            if current_song_time >= state["LOADED_SONG"].lyrics[state["current_lyrics_index"] + 1].timestamp_ms:
                state["current_lyrics_index"] += 1

        if state["current_pose_index"] + 1 < len(state["LOADED_SONG"].poses):
            if current_song_time >= state["LOADED_SONG"].poses[state["current_pose_index"] + 1].timestamp_ms:
                state["current_pose_index"] += 1

        last = state.get("pose_last_snapshot_song_time_ms", 0)
        if current_song_time - last >= POSE_SNAPSHOT_INTERVAL_MS:
            _write_pose_snapshot(state, current_song_time)
            state["pose_last_snapshot_song_time_ms"] = current_song_time

    # detect natural song end
    song_finished = False
    if state.get("game_state") == "playing":
        current_song_time = pygame.time.get_ticks() - state.get("song_start_time", 0)
        song_finished = current_song_time >= state.get("song_duration_ms", 0)

    if song_finished:
        state["game_state"] = "not_started"
        state["current_lyrics_index"] = 1
        state["current_pose_index"] = 0
        state["current_display"] = "end_screen"
        state["button_text"] = state["button_font"].render("START", True, state["BLACK"])
        if state["music_loaded"]:
            pygame.mixer.music.stop()
        stop_recording()

        try:
            sequence_order, poses = parse_pose_sequence_data(POSE_COMPARISON_FILE)
            frame_data = parse_frame_data(POSE_OUTPUT_FILE)
            results = compare_sequence_to_frames(sequence_order, poses, frame_data)
            score = int(total_accuracy(results))
        except Exception as e:
            print(f"Score calculation failed: {e}")
            score = 0

        state["final_score"] = score
        state["end_score_text"] = state["end_score_font"].render(f"Score: {score}%", True, state["YELLOW"])

    if state["pose_camera"].available and not state["pose_camera"].is_streaming():
        state["run"] = False
