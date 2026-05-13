import pygame
pygame.init()
#---------------------------------------------
#                  INIT WINDOW
window = pygame.display.set_mode((1000,700))
pygame.display.set_caption("Kareoke + Dance")

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

#---------------------------------------------
#                   RUN

# initialize window
run = True

while run:
  pygame.time.delay(15)

  # look to see if window exited
  for e in pygame.event.get():
    if e.type == pygame.QUIT:
      run = False

  # start new frame
  window.fill(BLACK)

  # draw windows
  pygame.draw.rect(window, WHITE, left_rect, LINE_WIDTH)
  pygame.draw.rect(window, WHITE, right_rect, LINE_WIDTH)
  pygame.draw.rect(window, WHITE, bottom_rect, LINE_WIDTH)

  # draw text
  window.blit(left_label, (left_rect.x + LABEL_PADDING, left_rect.y + LABEL_PADDING))
  window.blit(right_label, (right_rect.x + LABEL_PADDING, right_rect.y + LABEL_PADDING))
  window.blit(bottom_label, (bottom_rect.x + LABEL_PADDING, bottom_rect.y + LABEL_PADDING))

  # update to new frame
  pygame.display.flip()

# exit pygame
pygame.quit()