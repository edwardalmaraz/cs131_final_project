import pygame
from UI.models import Song

pygame.init()
#---------------------------------------------
#                  INIT WINDOW
window = pygame.display.set_mode((1000,700))
pygame.display.set_caption("Kareoke + Dance")

#---------------------------------------------
#                  INIT SONG
SONG_DIR = "songs"
pygame.mixer.music.load(f"{SONG_DIR}/cupid.mp3")


#---------------------------------------------
#                  RUNNING STATE

import pygame
from app_core import setup
from event_handlers import handle_events, update_state
from renderer import render

state = setup()

while state.get("run", False):
    pygame.time.delay(15)

    handle_events(state)
    update_state(state)
    render(state)

pygame.quit()