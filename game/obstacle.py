import pygame

from .paths import project_path

class Obstacle:
    def __init__(self, x, obstacle_type, speed):
        self.x = x
        self.type = obstacle_type
        self.passed = False

        self.set_properties(obstacle_type, speed)

        self.load_image()

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def set_properties(self, obstacle_type, speed):
        props = {
            "auto_cervene": {"w": 100, "h": 60, "y": 310, "speed": speed * 0.8, "image": "auto_cervene.png"},
            "auto_oranzove": {"w": 100, "h": 60, "y": 310, "speed": speed * 0.8, "image": "auto_oranzove.png"},
            "auto_zelene": {"w": 110, "h": 60, "y": 310, "speed": speed * 0.9, "image": "auto_zelene.png"},
            "auto_modre": {"w": 110, "h": 60, "y": 310, "speed": speed * 0.9, "image": "auto_modre.png"},
            "dodavka": {"w": 140, "h": 80, "y": 290, "speed": speed * 1.0, "image": "dodavka.png"},
            "taxi": {"w": 100, "h": 50, "y": 320, "speed": speed * 1.0, "image": "taxi.png"}
        }

        prop = props.get(obstacle_type, props["auto_cervene"])
        self.width = prop["w"]
        self.height = prop["h"]
        self.y = prop["y"]
        self.speed = prop["speed"]
        self.image_name = prop["image"]

    def load_image(self):
        self.image = pygame.image.load(project_path("assets", "images", self.image_name)).convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def update(self):
        self.x -= self.speed
        self.rect.x = self.x

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
