import pygame

class Dino:
    def __init__(self, x, y):
        self.x = x
        self.y = 270
        self.width = 60
        self.height = 90

        self.jumping = False
        self.jump_velocity = 0
        self.gravity = 1
        self.jump_strength = -22

        self.run_frames = []
        self.load_run_frames()

        self.jump_image = pygame.image.load("assets/images/jump.png").convert_alpha()
        self.jump_image = pygame.transform.scale(self.jump_image, (self.width, self.height))

        self.current_frame = 0
        self.animation_speed = 0.2
        self.frame_counter = 0

        self.image = self.run_frames[0]

        self.rect = pygame.Rect(self.x + 15, self.y + 30, self.width - 30, self.height - 45)

    def load_run_frames(self):
        for i in range(8):
            img = pygame.image.load(f"assets/images/dino_run/frame{i}.png").convert_alpha()
            img = pygame.transform.scale(img, (self.width, self.height))
            self.run_frames.append(img)

    def update(self):
        if self.jumping:
            self.y += self.jump_velocity
            self.jump_velocity += self.gravity
            if self.y >= 270 :
                self.y = 270
                self.jumping = False

        if not self.jumping:
            self.frame_counter += self.animation_speed
            if self.frame_counter >= len(self.run_frames):
                self.frame_counter = 0

            self.current_frame = int(self.frame_counter)
            self.image = self.run_frames[self.current_frame]
        else:
            self.image = self.jump_image

        self.rect = pygame.Rect(self.x + 15, self.y + 30, self.width - 30, self.height - 45)

    def jump(self):
        if not self.jumping:
            self.jumping = True
            self.jump_velocity = self.jump_strength

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))