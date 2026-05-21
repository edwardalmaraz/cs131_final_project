import pygame
import cv2
import sys

# open camera
camera = cv2.VideoCapture(0)

# init pygame, make window
pygame.init()
window = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Camera Feed")

running = True

# main loop
while running:
    # handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # get frame from camera
    success, frame = camera.read()

    if not success:
        continue

    # convert OpenCV BGR to RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # rotate/flip for pygame
    frame = frame.swapaxes(0, 1)

    # convert frame to pygame surface
    surface = pygame.surfarray.make_surface(frame)

    # blit surface
    window.blit(surface, (0, 0))

    # flip display
    pygame.display.flip()

# release camera, quit pygame
camera.release()
pygame.quit()
sys.exit()