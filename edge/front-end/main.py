# ui interface


import sys
from UI.models import Song, LeaderboardEntry
from event_handlers import handle_events, update_state
from renderer import render


import pygame
pygame.init()


## Set SDL_AUDIODRIVER to "alsa" to use ALSA audio driver
import os
os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
#########################################################




class PoseNetCamera:
   def __init__(self, input_uri="/dev/video0", network="resnet18-body", threshold=0.15, overlay="links,keypoints"):
       self.available = False
       self.error = None
       self.overlay = overlay
       self.cuda_to_numpy = None


       try:
           import numpy as np
           from jetson_inference import poseNet
           from jetson_utils import videoSource, cudaToNumpy, cudaDeviceSynchronize
       except ImportError as e:
           self.error = f"PoseNet unavailable: {e}"
           return


       self.np = np


       try:
           self.net = poseNet(network, sys.argv, threshold)
           self.input = videoSource(input_uri, argv=sys.argv)
           self.cuda_to_numpy = cudaToNumpy
           self.cuda_device_synchronize = cudaDeviceSynchronize
           self.available = True
       except Exception as e:
           self.error = f"PoseNet init failed: {e}"


   def get_surface(self):
       if not self.available:
           return None, []


       img = self.input.Capture()
       if img is None:
           return None, []


       poses = self.net.Process(img, overlay=self.overlay)
       self.cuda_device_synchronize()
       frame = self.cuda_to_numpy(img)


       if frame.dtype != self.np.uint8:
           frame = self.np.clip(frame, 0, 255).astype(self.np.uint8)


       if frame.ndim == 2:
           frame = self.np.repeat(frame[:, :, None], 3, axis=2)
       elif frame.shape[2] == 4:
           frame = frame[:, :, :3]
       elif frame.shape[2] == 1:
           frame = self.np.repeat(frame, 3, axis=2)
       else:
           frame = frame[:, :, :3]


       frame = self.np.array(frame, dtype=self.np.uint8)  # force Python-owned copy away from CUDA memory
       surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
       return surface, poses


   def is_streaming(self):
       return self.available and self.input.IsStreaming()




def blit_fit(surface, target_surface, target_rect):
   source_rect = surface.get_rect()
   scale = min(target_rect.width / source_rect.width, target_rect.height / source_rect.height)
   scaled_size = (
       max(1, int(source_rect.width * scale)),
       max(1, int(source_rect.height * scale)),
   )
   scaled = pygame.transform.smoothscale(surface, scaled_size)
   scaled_rect = scaled.get_rect(center=target_rect.center)
   target_surface.blit(scaled, scaled_rect)




def draw_centered_text(surface, text, rect, font, color):
   rendered = font.render(text, True, color)
   text_rect = rendered.get_rect(center=rect.center)
   surface.blit(rendered, text_rect)




#---------------------------------------------
#                  INIT WINDOW
window = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Kareoke + Dance :3")




#---------------------------------------------
#                  INIT POSE MODEL
pose_camera = PoseNetCamera()




#---------------------------------------------
#                  INIT SONG
SONG_DIR = "songs"
music_loaded = True
try:
   pygame.mixer.quit()  # undo auto-init from pygame.init() before re-initializing with custom device
   pygame.mixer.init(devicename="EarPods, USB Audio")
   pygame.mixer.music.load(f"{SONG_DIR}/audio.mp3")
except pygame.error as e:
   music_loaded = False
   print(f"Music unavailable: {e}")




#---------------------------------------------
#                  LAYOUT


# constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LINE_WIDTH = 2
MARGIN = 20
GAP = 20
LABEL_PADDING = 10


# window labels
label_font = pygame.font.SysFont(None, 26)
status_font = pygame.font.SysFont(None, 22)
left_label = label_font.render("POSE MODEL", True, WHITE)
right_label = label_font.render("NEXT MOVE", True, WHITE)
bottom_label = label_font.render("LYRICS", True, WHITE)


# window heights
window_width, window_height = window.get_size()


top_height = (window_height - (2 * MARGIN) - GAP) // 2
top_width = (window_width - (2 * MARGIN) - GAP) // 2


# create window stamps
left_rect = pygame.Rect(MARGIN, MARGIN, top_width, top_height)
right_rect = pygame.Rect(MARGIN + top_width + GAP, MARGIN, top_width, top_height)
bottom_rect = pygame.Rect(
   MARGIN,
   MARGIN + top_height + GAP,
   window_width - (2 * MARGIN),
   window_height - (2 * MARGIN) - top_height - GAP,
)


# create camera stamp
left_camera_rect = pygame.Rect(
   left_rect.x + LABEL_PADDING,
   left_rect.y + LABEL_PADDING + left_label.get_height() + LABEL_PADDING,
   left_rect.width - (2 * LABEL_PADDING),
   left_rect.height - (3 * LABEL_PADDING) - left_label.get_height(),
)


# create play/pause button (top right window -> top right corner)
button_font = pygame.font.SysFont(None, 24)
button_rect = pygame.Rect(window_width - MARGIN - 100, MARGIN, 100, 40)
button_text = button_font.render("PAUSE", True, BLACK)
is_paused = False




#---------------------------------------------
#                   RUN


# additional vars for full app (layout section already has the rest)
YELLOW = (255, 255, 0)
small_font = pygame.font.SysFont("comicsansms", 24)
big_font = pygame.font.SysFont("comicsansms", 36)


# song data
LOADED_SONG = Song.from_json("songs/metadata.json")


# start screen
title_font = pygame.font.SysFont(None, 64)
title_text = title_font.render("Dance Dance Karaoke", True, WHITE)
menu_font = pygame.font.SysFont(None, 40)
play_song_text = menu_font.render("1. PLAY SONG", True, WHITE)
online_library_text = menu_font.render("2. ONLINE LIBRARY", True, WHITE)
leaderboard_menu_text = menu_font.render("3. LEADERBOARD", True, WHITE)


# end screen
end_title_font = pygame.font.SysFont(None, 64)
end_score_font = pygame.font.SysFont(None, 80)
end_hint_font = pygame.font.SysFont(None, 28)
final_score = 100
end_song_name_text = end_title_font.render(LOADED_SONG.song_title, True, WHITE)
end_score_text = end_score_font.render(f"Score: {final_score}", True, YELLOW)
end_hint_text = end_hint_font.render("Press ENTER to return to menu", True, WHITE)


# name entry
name_entry_title_font = pygame.font.SysFont(None, 64)
name_entry_input_font = pygame.font.SysFont(None, 56)
name_entry_hint_font = pygame.font.SysFont(None, 28)

# song library
library_title_font = pygame.font.SysFont(None, 64)
library_entry_font = pygame.font.SysFont(None, 36)
library_hint_font = pygame.font.SysFont(None, 28)

# leaderboard
leaderboard_title_font = pygame.font.SysFont(None, 64)
leaderboard_entry_font = pygame.font.SysFont(None, 36)
leaderboard_hint_font = pygame.font.SysFont(None, 28)
leaderboard_entries = [
   LeaderboardEntry(player_name="HANSON", score=980, rank=1),
   LeaderboardEntry(player_name="Z", score=970, rank=2),
   LeaderboardEntry(player_name="ANDY", score=960, rank=3),
   LeaderboardEntry(player_name="EDWARD", score=950, rank=4),
   LeaderboardEntry(player_name="BOB", score=67, rank=5),
]
leaderboard_title_text = leaderboard_title_font.render("LEADERBOARD", True, WHITE)
leaderboard_hint_text = leaderboard_hint_font.render("Press ESC to return to menu", True, WHITE)


# pose reference images
pose_images = []


#moved code below to event_handlers.py so that the images are loaded after they are drawn and saved to the poses folder
# there is a data classs for Pose in models.py, but we don't need to use it here since we just need the images
# start here tmrw and assume this is where Z will inject the new pose drawing functions
# for pose_move in LOADED_SONG.poses:
#     image = pygame.image.load(pose_move.image_path)
#     image = pygame.transform.scale(image, (right_rect.width, right_rect.height))
#     pose_images.append(image)


song_duration_ms = max(
   LOADED_SONG.lyrics[-1].timestamp_ms if LOADED_SONG.lyrics else 0,
   LOADED_SONG.poses[-1].timestamp_ms if LOADED_SONG.poses else 0,
)


state = {
   "window": window,
   "LOADED_SONG": LOADED_SONG,
   "WHITE": WHITE,
   "BLACK": BLACK,
   "YELLOW": YELLOW,
   "LINE_WIDTH": LINE_WIDTH,
   "MARGIN": MARGIN,
   "GAP": GAP,
   "LABEL_PADDING": LABEL_PADDING,
   "small_font": small_font,
   "big_font": big_font,
   "label_font": label_font,
   "status_font": status_font,
   "left_label": left_label,
   "right_label": right_label,
   "bottom_label": bottom_label,
   "window_width": window_width,
   "window_height": window_height,
   "left_rect": left_rect,
   "right_rect": right_rect,
   "bottom_rect": bottom_rect,
   "left_camera_rect": left_camera_rect,
   "button_font": button_font,
   "button_rect": button_rect,
   "button_text": button_font.render("START", True, BLACK),
   "game_state": "not_started",
   "title_text": title_text,
   "play_song_text": play_song_text,
   "online_library_text": online_library_text,
   "leaderboard_text": leaderboard_menu_text,
   "end_song_name_text": end_song_name_text,
   "end_score_font": end_score_font,
   "end_score_text": end_score_text,
   "end_hint_text": end_hint_text,
   "leaderboard_entries": leaderboard_entries,
   "leaderboard_title_text": leaderboard_title_text,
   "leaderboard_entry_font": leaderboard_entry_font,
   "leaderboard_hint_text": leaderboard_hint_text,
   "player_id": "player1",
   "player_name_input": "",
   "name_entry_title_font": name_entry_title_font,
   "name_entry_input_font": name_entry_input_font,
   "name_entry_hint_font": name_entry_hint_font,
   "library_songs": [],
   "library_selected_index": 0,
   "library_title_font": library_title_font,
   "library_entry_font": library_entry_font,
   "library_hint_font": library_hint_font,
   "pose_images": pose_images,
   "pose_camera": pose_camera,
   "current_lyrics_index": 1,
   "current_pose_index": 0,
   "current_display": "start_screen",
   "final_score": final_score,
   "song_duration_ms": song_duration_ms,
   "music_loaded": music_loaded,
   "pose_surface": None,
   "poses": [],
   "run": True,
}


while state["run"]:
   pygame.time.delay(15)


   # always capture every frame to keep the gstreamer pipeline running
   state["pose_surface"], state["poses"] = pose_camera.get_surface()


   handle_events(state)
   update_state(state)
   render(state)




# exit pygame — release CUDA-backed surface and stop audio before teardown
state["pose_surface"] = None
if music_loaded:
   pygame.mixer.music.stop()
   pygame.mixer.quit()
pygame.quit()



