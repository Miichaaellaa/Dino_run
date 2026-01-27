import pygame
import random
import pygame.mixer

from .dino import Dino
from .obstacle import Obstacle

class Game:
    def __init__(self):
        pygame.init()

        self.WIDTH, self.HEIGHT = 800, 400
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Dino Game")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)

        self.dino = Dino(100, 300)
        self.obstacles = []

        self.game_over = False
        self.game_speed = 5

        self.background = pygame.image.load("assets/images/bg.jpg").convert()
        self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))

        self.car_types = ["auto_cervene", "auto_oranzove", "auto_zelene",
                          "auto_modre", "dodavka", "taxi"]

        self.last_cars = []

        self.obstacle_frequency = 1500
        self.last_obstacle_time = pygame.time.get_ticks()

        self.load_sounds()

        pygame.mixer.music.load("sounds/music/background_music.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

    def load_sounds(self):
        try:
            self.jump_sound = pygame.mixer.Sound("sounds/effects/deer_jump.wav")
            self.jump_sound.set_volume(0.4)

            self.crash_sound = pygame.mixer.Sound("sounds/effects/crash.wav")
            self.crash_sound.set_volume(1.0)
        except pygame.error as e:
            print(f"Chyba pri načítaní zvukov: {e}")
            self.jump_sound = None
            self.crash_sound = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.game_over:
                    if not self.dino.jumping:
                        self.dino.jump()
                        if self.jump_sound:
                            self.jump_sound.play()

                if event.key == pygame.K_r and self.game_over:
                    self.restart_game()
                    return

                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    pygame.quit()
                    return

    def get_random_car_type(self):
        if len(self.last_cars) >= 3:
            if self.last_cars[-1] == self.last_cars[-2] == self.last_cars[-3]:
                available = [car for car in self.car_types if car != self.last_cars[-1]]
                if available:
                    car_type = random.choice(available)
                else:
                    car_type = random.choice(self.car_types)
            else:
                car_type = random.choice(self.car_types)
        else:
            car_type = random.choice(self.car_types)

        self.last_cars.append(car_type)
        if len(self.last_cars) > 5:
            self.last_cars.pop(0)

        return car_type

    def update(self):
        if not self.game_over:
            self.dino.update()

            for obstacle in self.obstacles[:]:
                obstacle.update()

                if obstacle.x < -200:
                    self.obstacles.remove(obstacle)

            current_time = pygame.time.get_ticks()
            if current_time - self.last_obstacle_time > self.obstacle_frequency:
                car_type = self.get_random_car_type()
                self.obstacles.append(Obstacle(self.WIDTH, car_type, self.game_speed))
                self.last_obstacle_time = current_time

            for obstacle in self.obstacles:
                if self.dino.rect.colliderect(obstacle.rect):
                    self.game_over = True
                    if self.crash_sound:
                        pygame.mixer.music.stop()
                        self.crash_sound.play()
                    break

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.dino.draw(self.screen)

        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def draw_game_over(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.font.render("GAME OVER", True, (255, 50, 50))
        restart_text = pygame.font.SysFont(None, 32).render("Press R to restart", True, (200, 200, 200))

        self.screen.blit(game_over_text, (self.WIDTH // 2 - game_over_text.get_width() // 2, self.HEIGHT // 2 - 30))
        self.screen.blit(restart_text, (self.WIDTH // 2 - restart_text.get_width() // 2, self.HEIGHT // 2 + 30))

    def restart_game(self):
        self.__init__()

    def run(self):
        self.running = True

        while self.running:
            self.handle_events()

            if not hasattr(self, 'running') or not self.running:
                break

            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()