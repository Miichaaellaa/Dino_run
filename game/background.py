import pygame

from .paths import project_path

class Background:
    def __init__(self, width, height, speed):
        self.width = width
        self.height = height

        self.speed = speed

        self.image = pygame.image.load(project_path("assets", "images", "background.png")).convert()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

        self.x1 = 0.0
        self.x2 = float(self.width)

    def update(self):
        real_movement = self.speed * 0.5

        self.x1 -= real_movement
        self.x2 -= real_movement

        if self.x1 <= -self.width:
            self.x1 = self.x2 + self.width

        if self.x2 <= -self.width:
            self.x2 = self.x1 + self.width

    def draw(self, screen):
        screen.blit(self.image, (int(self.x1), 0))
        screen.blit(self.image, (int(self.x2), 0))
