# SDL_AUDIODRIVER=alsa AUDIODEV=plughw:1,3 python3 audio_source.py

import pygame

pygame.mixer.quit()
pygame.mixer.init(devicename="EarPods, USB Audio")

pygame.mixer.music.load("../front-end/songs/cupid.mp3")
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    pygame.time.wait(100)