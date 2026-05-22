"""
TODO
- Add pose figure to top right box
- Display the PoseModel frames from nvidia-inference onto the left hand box
"""


import pygame
import cv2
from UI.models import Song

#camera helper functions
def start_camera():
  """Open the webcam. Returns the camera object."""
  cam = cv2.VideoCapture(0)
  return cam

def stop_camera(cam):
  """Release the webcam. Safe to call with None."""
  if cam is not None:
    cam.release()

The_Feels = Song.from_json("songs/json/the_feels.json")

pygame.init()
#---------------------------------------------
#                  INIT WINDOW
window = pygame.display.set_mode((1000,700))
pygame.display.set_caption("Kareoke + Dance")

#---------------------------------------------
#                  INIT SONG
SONG_DIR = "songs"
pygame.mixer.music.load(f"{SONG_DIR}/TWICE The Feels MV.mp3")


#---------------------------------------------
#                  LAYOUT

# constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
LINE_WIDTH = 2
MARGIN = 20
GAP = 20
LABEL_PADDING = 10
LINE_OFFSET = 80

#camera varable
camera = None  # None means "not currently capturing"

#text fonts
small_font = pygame.font.SysFont("comicsansms", 24)
big_font = pygame.font.SysFont("comicsansms", 36)

#lyrics and pose index
current_lyrics_index = 1
current_pose_index = 0
current_display =  "start_screen"

# window labels
#label_font = pygame.font.SysFont(None, 26)
#left_label = label_font.render("POSE MODEL", True, WHITE)
#right_label = label_font.render("NEXT MOVE", True, WHITE)
#bottom_label = label_font.render("LYRICS", True, WHITE)

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

#gameplay pause/play/start button (toggles between START/PAUSE/PLAY)
button_rect = pygame.Rect(window_width - MARGIN - 100, MARGIN, 100, 40)
button_text = button_font.render("START", True, BLACK)
game_state = "not_started"

#start menu
# ---------- START SCREEN ----------
# title (big text at the top)
title_font = pygame.font.SysFont(None, 64)
title_text = title_font.render("Dance Dance Karaoke", True, WHITE)

# menu options - rendered as text surfaces, no buttons since keyboard-driven
menu_font = pygame.font.SysFont(None, 40)
play_song_text = menu_font.render("1. PLAY SONG", True, WHITE)
online_library_text = menu_font.render("2. ONLINE LIBRARY", True, WHITE)
leaderboard_text = menu_font.render("3. LEADERBOARD", True, WHITE)

# ---------- END SCREEN ----------
# fonts for end screen text
end_title_font = pygame.font.SysFont(None, 64)
end_score_font = pygame.font.SysFont(None, 80)
end_hint_font = pygame.font.SysFont(None, 28)

# hardcoded score for now - will come from cloud later
final_score = 100

# pre-render the static text surfaces
end_song_name_text = end_title_font.render(The_Feels.song_title, True, WHITE)
end_score_text = end_score_font.render(f"Score: {final_score}", True, YELLOW)
end_hint_text = end_hint_font.render("Press ENTER to return to menu", True, WHITE)

# ---------- LEADERBOARD SCREEN ----------
from UI.models import LeaderboardEntry

# fonts for leaderboard
leaderboard_title_font = pygame.font.SysFont(None, 64) 
leaderboard_entry_font = pygame.font.SysFont(None, 36)
leaderboard_hint_font = pygame.font.SysFont(None, 28)

# hardcoded leaderboard entries (already in rank order - highest first)
# replace with cloud data later
leaderboard_entries = [
  LeaderboardEntry(player_name="HANSON", score=980, rank=1),
  LeaderboardEntry(player_name="Z",      score=970, rank=2),
  LeaderboardEntry(player_name="ANDY",   score=960, rank=3),
  LeaderboardEntry(player_name="EDWARD", score=950, rank=4),
  LeaderboardEntry(player_name="BOB",    score=67, rank=5),
]

# pre-render the static text surfaces (don't re-render every frame)
leaderboard_title_text = leaderboard_title_font.render("LEADERBOARD", True, WHITE)
leaderboard_hint_text = leaderboard_hint_font.render("Press ESC to return to menu", True, WHITE)

#---------------------------------------------
#                   RUN

# initialize window
run = True

#load poses to array
pose_images = []

for pose_moves in The_Feels.poses:
    image = pygame.image.load(pose_moves.image_path)
    image = pygame.transform.scale(image, (right_rect.width, right_rect.height))
    pose_images.append(image)

while run:
  pygame.time.delay(15)

  # look to see if window exited
  for e in pygame.event.get():

    """ USER EXIT CALL """
    if e.type == pygame.QUIT:
      run = False

    """ USER SCREEN INPUT - MOUSE """
    if e.type == pygame.MOUSEBUTTONDOWN:

      # ----- START SCREEN -----
      if current_display == "start_screen":
        # keyboard-only, no mouse handling
        pass

      # ----- GAMEPLAY SCREEN -----
      elif current_display == "gameplay":
        # only respond if the click landed on the pause/play button
        if button_rect.collidepoint(e.pos):
          if game_state == "not_started":
            # first click starts the song
            pygame.mixer.music.play()
            song_start_time = pygame.time.get_ticks()
            game_state = "playing"
            button_text = button_font.render("PAUSE", True, BLACK)

          elif game_state == "playing":
            # button shows PAUSE - clicking pauses the song
            pygame.mixer.music.pause()
            pause_start_time = pygame.time.get_ticks()
            game_state = "paused"
            button_text = button_font.render("PLAY", True, BLACK)

          elif game_state == "paused":
            # button shows PLAY - clicking resumes the song
            pygame.mixer.music.unpause()
            paused_duration = pygame.time.get_ticks() - pause_start_time
            song_start_time += paused_duration
            game_state = "playing"
            button_text = button_font.render("PAUSE", True, BLACK)

      # ----- LEADERBOARD SCREEN -----
      elif current_display == "leaderboard":
        # no buttons here yet - placeholder
        pass

    """ USER SCREEN INPUT - KEYBOARD """
    if e.type == pygame.KEYDOWN:

      # ----- START SCREEN keyboard shortcuts -----
      if current_display == "start_screen":
        if e.key == pygame.K_1:
          # press "1" to play song
          camera = start_camera()
          current_display = "gameplay"
        elif e.key == pygame.K_2:
          # press "2" for online library (not built yet)
          print("online library - not built yet")
        elif e.key == pygame.K_3:
          # press "3" to view leaderboard
          current_display = "leaderboard"

      # ----- GAMEPLAY SCREEN keyboard shortcuts -----
      elif current_display == "gameplay":
        # ESC returns to start screen, but ONLY when song
        # is paused or hasn't started. Prevents accidental quit mid-song.
        if e.key == pygame.K_ESCAPE:
          if game_state == "paused" or game_state == "not_started":
            # stop music completely (in case it was paused)
            pygame.mixer.music.stop()
            # reset all state for a clean return
            game_state = "not_started"
            current_lyrics_index = 1
            current_pose_index = 0
            button_text = button_font.render("START", True, BLACK)
            current_display = "start_screen"
            stop_camera(camera)
            camera = None               

      # ----- LEADERBOARD SCREEN keyboard shortcuts -----
      elif current_display == "leaderboard":
        # ESC or DELETE goes back to start screen
        if e.key == pygame.K_ESCAPE or e.key == pygame.K_DELETE:
          current_display = "start_screen"

      # ----- END SCREEN keyboard shortcuts -----
      elif current_display == "end_screen":
        if e.key == pygame.K_RETURN:
          # press ENTER to go back to start screen
          current_display = "start_screen"

  #fixes indexing error for arrays
  if game_state == "playing":
      current_song_time = pygame.time.get_ticks() - song_start_time

      if current_lyrics_index + 1 < len(The_Feels.lyrics):
          if current_song_time >= The_Feels.lyrics[current_lyrics_index + 1].timestamp_ms:
            current_lyrics_index += 1

      if current_pose_index + 1 < len(The_Feels.poses):
          if current_song_time >= The_Feels.poses[current_pose_index + 1].timestamp_ms:
            current_pose_index += 1

    # ---------- DETECT END OF SONG ----------
  # get_busy() returns False when song finishes OR when paused. so we also check game_state to know it's a real finish, not a pause
  if game_state == "playing" and not pygame.mixer.music.get_busy():
    # song just finished naturally
    game_state = "not_started"           # reset so player could replay
    current_lyrics_index = 1             # reset lyric position
    current_pose_index = 0               # reset pose position
    current_display = "end_screen"       # switch to end screen
    button_text = button_font.render("START", True, BLACK)  # reset button label
    stop_camera(camera)        
    camera = None               
          

  # advance lyric index based on song time

  # start new frame
  window.fill(BLACK)
  if current_display == "start_screen":
    # draw title centered horizontally near the top
    title_rect = title_text.get_rect(center=(window_width // 2, 120))
    window.blit(title_text, title_rect)

    # draw the three menu options centered, stacked vertically below the title
    play_rect = play_song_text.get_rect(center=(window_width // 2, 300))
    library_rect = online_library_text.get_rect(center=(window_width // 2, 370))
    leaderboard_rect = leaderboard_text.get_rect(center=(window_width // 2, 440))

    window.blit(play_song_text, play_rect)
    window.blit(online_library_text, library_rect)
    window.blit(leaderboard_text, leaderboard_rect)
  
  elif current_display == "gameplay":
    # draw windows
    pygame.draw.rect(window, WHITE, left_rect, LINE_WIDTH)
    pygame.draw.rect(window, WHITE, right_rect, LINE_WIDTH)
    pygame.draw.rect(window, WHITE, bottom_rect, LINE_WIDTH)

    # draw text
    text_surface1 = small_font.render(The_Feels.lyrics[current_lyrics_index - 1].text, True, WHITE)
    text_surface2 = big_font.render(The_Feels.lyrics[current_lyrics_index].text, True, YELLOW)

    text_rect1 = text_surface1.get_rect(center=(bottom_rect.centerx, bottom_rect.top + 80))
    text_rect2 = text_surface2.get_rect(center=bottom_rect.center)

    window.blit(text_surface1, text_rect1)
    window.blit(text_surface2, text_rect2)

    if current_lyrics_index + 1 < len(The_Feels.lyrics):
      text_surface3 = small_font.render(The_Feels.lyrics[current_lyrics_index + 1].text, True, WHITE)
      text_rect3 = text_surface3.get_rect(center=(bottom_rect.centerx, bottom_rect.bottom - 80))
      window.blit(text_surface3, text_rect3)

    # ---------- CAMERA FEED IN LEFT BOX ----------
    if camera is not None:
      success, frame = camera.read()
      if success:
        # mirror horizontally so player sees themselves like in a mirror
        frame = cv2.flip(frame, 1)
        # OpenCV uses BGR, pygame uses RGB - swap channels
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # OpenCV stores frames as [rows, cols], pygame wants [cols, rows] - swap axes
        frame = frame.swapaxes(0, 1)
        # convert numpy array to a pygame surface we can blit
        camera_surface = pygame.surfarray.make_surface(frame)
        # scale the camera frame to fit inside left_rect
        camera_surface = pygame.transform.scale(camera_surface, (left_rect.width, left_rect.height))
        # draw it
        window.blit(camera_surface, left_rect)

    window.blit(pose_images[current_pose_index], right_rect)

    # draw play/pause button
    pygame.draw.rect(window, BLACK, button_rect, LINE_WIDTH)
    window.blit(button_text, (button_rect.x + 15, button_rect.y + 15))

    # update to new frame
  elif current_display == "leaderboard":
    # draw title at the top, centered
    title_rect = leaderboard_title_text.get_rect(center=(window_width // 2, 100))
    window.blit(leaderboard_title_text, title_rect)

    # draw each entry stacked vertically below the title
    entry_start_y = 200    # vertical position of first entry
    entry_spacing = 60     # pixels between entries

    for index, entry in enumerate(leaderboard_entries):
      # build the display string from the entry's data
      #format: rank number, player name (left-padded), score (right-aligned)
      entry_string = f"{entry.rank}.  {entry.player_name:<10}  {entry.score}"

      # render the text and center it horizontally
      entry_surface = leaderboard_entry_font.render(entry_string, True, WHITE)
      entry_rect = entry_surface.get_rect(center=(window_width // 2, entry_start_y + index * entry_spacing))
      window.blit(entry_surface, entry_rect)

    # draw hint at the bottom
    hint_rect = leaderboard_hint_text.get_rect(center=(window_width // 2, window_height - 60))
    window.blit(leaderboard_hint_text, hint_rect)
    
  elif current_display == "end_screen":
    # draw song name at the top, centered
    song_name_rect = end_song_name_text.get_rect(center=(window_width // 2, 150))
    window.blit(end_song_name_text, song_name_rect)

    # draw score in the middle, centered
    score_rect = end_score_text.get_rect(center=(window_width // 2, window_height // 2))
    window.blit(end_score_text, score_rect)

    # draw hint text near the bottom
    hint_rect = end_hint_text.get_rect(center=(window_width // 2, window_height - 80))
    window.blit(end_hint_text, hint_rect)

  pygame.display.flip()

stop_camera(camera)
pygame.quit()

# exit pygame