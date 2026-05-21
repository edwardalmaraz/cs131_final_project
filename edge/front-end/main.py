"""
TODO
- Add pose figure to top right box
- Display the PoseModel frames from nvidia-inference onto the left hand box
- Lyrics (should be some sort of yellow color kind of like kareoke on yt)
- add leaderboard menu
-

- END-OF-SONG: detect when audio finishes, show "Good job!" in lyrics box
- END-OF-SONG: handle gap between last timestamp and audio finishing
"""


import pygame
from UI.models import Song

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

#text fonts
small_font = pygame.font.SysFont("comicsansms", 24)
big_font = pygame.font.SysFont("comicsansms", 36)

#lyrics and pose index
current_lyrics_index = 1
current_pose_index = 0
current_display = "start screen"

# window labels
label_font = pygame.font.SysFont(None, 26)
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
button_text = button_font.render("START", True, BLACK)
game_state = "not_started"

#leaderboard button


#---------------------------------------------
#                   RUN

# initialize window
run = True

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

    """ USER SCREEN INPUT """
    if e.type == pygame.MOUSEBUTTONDOWN: # if user pressed in pause button area (called button_rect)
        if button_rect.collidepoint(e.pos):

            if game_state == "not_started":
                pygame.mixer.music.play()
                song_start_time = pygame.time.get_ticks()
                game_state = "playing"
                button_text = button_font.render("PAUSE", True, BLACK)

            elif game_state == "playing":
                pygame.mixer.music.pause()
                pause_start_time = pygame.time.get_ticks()
                game_state = "paused"
                button_text = button_font.render("PLAY", True, BLACK)

            elif game_state == "paused":
                pygame.mixer.music.unpause()
                paused_duration = pygame.time.get_ticks() - pause_start_time
                song_start_time += paused_duration
                game_state = "playing"
                button_text = button_font.render("PAUSE", True, BLACK)


  if game_state == "playing":
      current_song_time = pygame.time.get_ticks() - song_start_time

      if current_lyrics_index + 1 < len(The_Feels.lyrics):
          if current_song_time >= The_Feels.lyrics[current_lyrics_index + 1].timestamp_ms:
            current_lyrics_index += 1

      if current_pose_index + 1 < len(The_Feels.poses):
          if current_song_time >= The_Feels.poses[current_pose_index + 1].timestamp_ms:
            current_pose_index += 1
          

  # advance lyric index based on song time

  # start new frame
  window.fill(BLACK)

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

  window.blit(pose_images[current_pose_index], left_rect) 

  if current_pose_index + 1 < len(pose_images):
    window.blit(pose_images[current_pose_index + 1], right_rect)

  # draw play/pause button
  pygame.draw.rect(window, BLACK, button_rect, LINE_WIDTH)
  window.blit(button_text, (button_rect.x + 15, button_rect.y + 15))
  #pygame.draw.rect(surface, color, rect, width)

  # update to new frame
  pygame.display.flip()

# exit pygame