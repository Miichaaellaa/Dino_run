import pygame
import json
import os
from game.game import Game
from game.background import Background

class Button:
    def __init__(self, x, y, w, h, text, action, font, color=(100, 100, 100), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.font = font
        self.color = color
        self.text_color = text_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial, label, font, on_change=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.min = min_val
        self.max = max_val
        self.value = initial
        self.label = label
        self.font = font
        self.on_change = on_change
        self.dragging = False
        self.prev_value = initial

    def update(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx, _ = event.pos
                new_value = (mx - self.rect.x) / self.rect.w * (self.max - self.min) + self.min
                self.value = max(self.min, min(self.max, new_value))
                if self.on_change and abs(self.value - self.prev_value) > 0.01:  # Threshold to reduce spam
                    self.on_change(self.value)
                    self.prev_value = self.value
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

    def draw(self, screen):
        pygame.draw.rect(screen, (50, 50, 50), self.rect)
        pos_x = self.rect.x + (self.value - self.min) / (self.max - self.min) * self.rect.w
        pygame.draw.rect(screen, (0, 0, 255), (self.rect.x, self.rect.y, pos_x - self.rect.x, self.rect.h))
        label_surf = self.font.render(f"{self.label}: {self.value:.2f}", True, (255, 255, 255))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 30))

class Menu:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 400
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Dino Run Menu")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 28)
        self.bg = Background(self.WIDTH, self.HEIGHT, 5)

        self.settings_file = "settings.json"
        self.highscores_file = "highscores.json"

        self.music_volume = 0.5
        self.sfx_volume = 0.4
        self.load_settings()

        # ─── Vytvoríme slidery raz tu ────────────────────────────────
        self.music_slider = Slider(
            250, 150, 300, 20, 0.0, 1.0, self.music_volume,
            "Music Volume", self.small_font, self.music_change
        )
        self.sfx_slider = Slider(
            250, 200, 300, 20, 0.0, 1.0, self.sfx_volume,
            "SFX Volume", self.small_font, self.sfx_change
        )
        # ─────────────────────────────────────────────────────────────

        self.jump_sound = pygame.mixer.Sound("sounds/effects/deer_jump.wav")
        self.jump_sound.set_volume(self.sfx_volume)

        pygame.mixer.music.load("sounds/music/background_music.mp3")
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1)

        self.current_screen = 'main'
        self.buttons = []
        self.highscores = self.load_highscores()


    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
                self.music_volume = data.get('music_volume', 0.5)
                self.sfx_volume = data.get('sfx_volume', 0.4)

    def save_settings(self):
        data = {
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume
        }
        with open(self.settings_file, 'w') as f:
            json.dump(data, f)

    def load_highscores(self):
        if os.path.exists(self.highscores_file):
            with open(self.highscores_file, 'r') as f:
                data = json.load(f)
                return data.get('scores', [])
        return []

    def save_highscore(self, new_score):
        self.highscores.append(new_score)
        self.highscores.sort(reverse=True)
        self.highscores = self.highscores[:15]
        with open(self.highscores_file, 'w') as f:
            json.dump({'scores': self.highscores}, f)

    def play_action(self):
        pygame.mixer.music.stop()
        game = Game(self.screen, self.music_volume, self.sfx_volume)
        result = game.run()
        if result == 'menu':
            self.save_highscore(game.score)
            self.highscores = self.load_highscores()  # reload
        pygame.mixer.music.play(-1)
        self.current_screen = 'main'

    def highscores_action(self):
        self.current_screen = 'highscores'

    def settings_action(self):
        self.current_screen = 'settings'

    def quit_action(self):
        self.running = False

    def back_action(self):
        if self.current_screen == 'settings':
            self.save_settings()
        self.current_screen = 'main'

    def music_change(self, value):
        self.music_volume = value
        pygame.mixer.music.set_volume(value)

    def sfx_change(self, value):
        self.sfx_volume = value
        self.jump_sound.set_volume(value)
        self.jump_sound.play()

    def run(self):
        self.running = True
        while self.running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.current_screen == 'main':
                            self.running = False
                        else:
                            self.back_action()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    for button in self.buttons:
                        button.handle_click(pos)

                if self.current_screen == 'settings':
                    self.music_slider.update(event)
                    self.sfx_slider.update(event)

            self.bg.update()
            self.bg.draw(self.screen)

            self.buttons = []

            if self.current_screen == 'main':
                title_text = self.font.render("Dino Run", True, (255, 255, 255))
                self.screen.blit(title_text, (self.WIDTH // 2 - title_text.get_width() // 2, 50))

                play_button = Button(300, 150, 200, 50, "Play", self.play_action, self.small_font)
                highscores_button = Button(300, 210, 200, 50, "High Scores", self.highscores_action, self.small_font)
                settings_button = Button(300, 270, 200, 50, "Settings", self.settings_action, self.small_font)
                quit_button = Button(300, 330, 200, 50, "Quit", self.quit_action, self.small_font)

                self.buttons = [play_button, highscores_button, settings_button, quit_button]

            elif self.current_screen == 'highscores':
                hs_text = self.font.render("Top 15 Scores", True, (255, 255, 255))
                self.screen.blit(hs_text, (self.WIDTH // 2 - hs_text.get_width() // 2, 50))

                for i, score in enumerate(self.highscores):
                    score_text = self.small_font.render(f"{i+1}. {score}", True, (255, 255, 255))
                    self.screen.blit(score_text, (300, 100 + i * 20))

                back_button = Button(300, 350, 200, 50, "Back", self.back_action, self.small_font)
                self.buttons = [back_button]

            elif self.current_screen == 'settings':
                settings_text = self.font.render("Settings", True, (255, 255, 255))
                self.screen.blit(settings_text, (self.WIDTH // 2 - settings_text.get_width() // 2, 50))

                self.music_slider.draw(self.screen)
                self.sfx_slider.draw(self.screen)

                back_button = Button(300, 350, 200, 50, "Back", self.back_action, self.small_font)
                self.buttons = [back_button]

            for button in self.buttons:
                button.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

        self.save_settings()
        pygame.quit()

if __name__ == "__main__":
    menu = Menu()
    menu.run()