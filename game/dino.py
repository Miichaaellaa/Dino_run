import pygame


class Dino:
    def __init__(self, x, y, character="deer", fast_animation=True):
        self.x = x
        self.y = 270
        self.width = 60
        self.height = 90

        self.character = character
        self.fast_animation = fast_animation

        self.jumping = False
        self.jump_velocity = 0
        self.gravity = 1
        self.jump_strength = -22

        self.run_frames = []
        self.load_character_frames()

        self.jump_image = self.load_character_image()
        if self.jump_image is None:
                self.jump_image = pygame.Surface((self.width, self.height))
                self.jump_image.fill((150, 50, 50))

        self.current_frame = 0

        if self.fast_animation:
            self.animation_speed = 0.2
        else:
            self.animation_speed = 0.08

        self.frame_counter = 0

        if self.run_frames:
            self.image = self.run_frames[0]
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((100, 100, 100))

        self.rect = pygame.Rect(self.x + 15, self.y + 30, self.width - 30, self.height - 45)

    def load_character_frames(self):
        for i in range(20):
            try:
                img_path = f"assets/characters/{self.character}/run/frame{i}.png"
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (self.width, self.height))
                self.run_frames.append(img)
            except:
                continue

        if not self.run_frames:
            idle_path = f"assets/characters/{self.character}/idle.png"
            idle_img = pygame.image.load(idle_path).convert_alpha()
            idle_img = pygame.transform.scale(idle_img, (self.width, self.height))
            self.run_frames.append(idle_img)



    def load_character_image(self):
        img_path = f"assets/characters/{self.character}/jump.png"
        img = pygame.image.load(img_path).convert_alpha()
        return pygame.transform.scale(img, (self.width, self.height))

    def update(self):
        if self.jumping:
            self.y += self.jump_velocity
            self.jump_velocity += self.gravity
            if self.y >= 270:
                self.y = 270
                self.jumping = False

        if not self.jumping:
            self.frame_counter += self.animation_speed

        if not self.jumping:

            if self.run_frames:
                if self.frame_counter >= len(self.run_frames):
                    self.frame_counter = 0

                self.current_frame = int(self.frame_counter)
                if self.current_frame < len(self.run_frames):
                    self.image = self.run_frames[self.current_frame]
            else:
                if hasattr(self, 'image') and self.image:
                    pass
                else:
                    self.image = self.jump_image

        else:
            self.image = self.jump_image

        self.rect = pygame.Rect(self.x + 15, self.y + 30, self.width - 30, self.height - 45)

    def jump(self):
        if not self.jumping:
            self.jumping = True
            self.jump_velocity = self.jump_strength

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))