import pygame
import json
import os

from game.game import Game
from game.multiplayer_game import MultiplayerGame
from game.background import Background
from game.paths import project_path


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


class Menu:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 400
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Deerun - Menu")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 28)
        self.bg = Background(self.WIDTH, self.HEIGHT, 5)

        self.settings_file = project_path("settings.json")
        self.load_settings()
        self.highscores = self.load_highscores()

        try:
            pygame.mixer.music.load(project_path("sounds", "music", "background_music.mp3"))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"[MENU] Nepodarilo sa nacitat hudbu na pozadi: {e}")

        self.menu_state = 'main'
        self.buttons = []

        self.player_name = "Hrac"
        self.ip_input_text = "127.0.0.1"
        self.max_players_choice = 2

        self.active_input = None

        self.error_message = ""
        self.error_time = 0
        self.dragging_slider = None
        self.last_sfx_preview_time = 0
        self.preview_sound = None
        self.load_preview_sound()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.music_volume = data.get("music_volume", 0.5)
                    self.sfx_volume = data.get("sfx_volume", 0.4)
            except (OSError, json.JSONDecodeError) as e:
                print(f"[MENU] Nepodarilo sa nacitat nastavenia: {e}")
                self.music_volume, self.sfx_volume = 0.5, 0.4
        else:
            self.music_volume, self.sfx_volume = 0.5, 0.4

    def save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump({"music_volume": self.music_volume, "sfx_volume": self.sfx_volume}, f)
        except Exception as e:
            print(f"[MENU] Chyba pri ukladaní nastavení: {e}")

    def show_error(self, text):
        self.error_message = text
        self.error_time = pygame.time.get_ticks()

    def load_preview_sound(self):
        try:
            self.preview_sound = pygame.mixer.Sound(project_path("sounds", "effects", "deer_jump.wav"))
            self.preview_sound.set_volume(self.sfx_volume)
        except pygame.error as e:
            print(f"[MENU] Nepodarilo sa nacitat SFX preview: {e}")
            self.preview_sound = None

    def load_highscores(self):
        try:
            with open(project_path("highscores.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[MENU] Nepodarilo sa nacitat top score: {e}")
            return []

        scores = data.get("scores", [])
        return sorted([score for score in scores if isinstance(score, int)], reverse=True)[:10]

    def start_singleplayer(self):
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

        game = Game(self.screen, music_volume=self.music_volume, sfx_volume=self.sfx_volume)
        game.run()
        self.highscores = self.load_highscores()

        try:
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass
        self.menu_state = 'main'

    def start_local_multiplayer(self, player_count=None):
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

        selected_players = player_count or self.max_players_choice
        game = MultiplayerGame(
            self.screen,
            player_count=selected_players,
            music_volume=self.music_volume,
            sfx_volume=self.sfx_volume
        )
        game.run()

        try:
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass
        self.menu_state = 'main'

    def demo_create_server(self):
        self.show_error("Funkcia vytvorenia servera bude dostupná neskôr")

    def demo_connect_to_game(self):
        self.show_error("Funkcia pripojenia k serveru bude dostupná neskôr")

    def draw_main_menu(self):
        title = self.font.render("DEERUN", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 50))
        self.buttons = [
            Button(300, 120, 200, 45, "Štart", lambda: setattr(self, 'menu_state', 'start_choice'), self.small_font),
            Button(300, 175, 200, 45, "High scores", lambda: setattr(self, 'menu_state', 'highscores'), self.small_font),
            Button(300, 230, 200, 45, "Nastavenia", lambda: setattr(self, 'menu_state', 'settings'), self.small_font),
            Button(300, 285, 200, 45, "Ukončiť", lambda: setattr(self, 'running', False), self.small_font)
        ]
    def draw_top_scores(self):
        x = self.WIDTH - 175
        y = 130

        title = self.small_font.render("TOP SCORE", True, (255, 255, 0))
        self.screen.blit(title, (x, y))

        if not self.highscores:
            empty_text = self.small_font.render("Zatial ziadne", True, (255, 255, 255))
            self.screen.blit(empty_text, (x, y + 30))
            return

        for index, score in enumerate(self.highscores, start=1):
            score_text = self.small_font.render(f"{index}. {score}", True, (255, 255, 255))
            self.screen.blit(score_text, (x, y + index * 28))

    def draw_highscores(self):
        self.highscores = self.load_highscores()

        title = self.font.render("HIGH SCORES", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 45))

        if not self.highscores:
            empty_text = self.small_font.render("Zatiaľ žiadne skóre", True, (255, 255, 255))
            self.screen.blit(empty_text, (self.WIDTH // 2 - empty_text.get_width() // 2, 150))
        else:
            for index, score in enumerate(self.highscores, start=1):
                score_text = self.small_font.render(f"{index}. {score}", True, (255, 255, 255))
                self.screen.blit(score_text, (self.WIDTH // 2 - score_text.get_width() // 2, 95 + index * 26))

        self.buttons = [
            Button(300, 310, 200, 45, "Späť", lambda: setattr(self, 'menu_state', 'main'), self.small_font)
        ]

    def draw_start_choice(self):
        title = self.font.render("Výber režimu", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 50))
        self.buttons = [
            Button(300, 140, 200, 45, "Singleplayer", self.start_singleplayer, self.small_font),
            Button(300, 200, 200, 45, "Multiplayer", lambda: setattr(self, 'menu_state', 'multiplayer_choice'),
                   self.small_font),
            Button(300, 280, 200, 45, "Späť", lambda: setattr(self, 'menu_state', 'main'), self.small_font)
        ]

    def draw_multiplayer_choice(self):
        title = self.font.render("Multiplayer", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 50))
        self.buttons = [
            Button(275, 140, 250, 45, "Hrat multiplayer", lambda: setattr(self, 'menu_state', 'create_server'),
                   self.small_font, (0, 110, 80)),
            Button(275, 205, 250, 45, "Pripojiť sa", lambda: setattr(self, 'menu_state', 'join_server'),
                   self.small_font),
            Button(300, 280, 200, 45, "Späť", lambda: setattr(self, 'menu_state', 'start_choice'), self.small_font)
        ]

    def draw_create_server(self):
        title = self.font.render("Lokalny multiplayer", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 30))
        self.screen.blit(self.small_font.render("Počet hráčov (max 4):", True, (255, 255, 255)), (180, 110))
        for i, num in enumerate([2, 3, 4]):
            btn_color = (0, 150, 0) if self.max_players_choice == num else (80, 80, 80)
            self.buttons.append(
                Button(420 + (i * 60), 100, 50, 35, str(num), lambda n=num: setattr(self, 'max_players_choice', n),
                       self.small_font, btn_color))

        self.buttons.extend([
            Button(200, 280, 180, 45, "Start hry", self.start_local_multiplayer, self.small_font, (0, 100, 0)),
            Button(420, 280, 180, 45, "Späť", lambda: setattr(self, 'menu_state', 'multiplayer_choice'),
                   self.small_font)
        ])

    def draw_join_server(self):
        title = self.font.render("Pripojiť sa na server", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 30))

        self.screen.blit(self.small_font.render(f"IP Servera: {self.ip_input_text}", True, (255, 255, 255)), (180, 120))
        self.buttons.append(
            Button(550, 112, 110, 32, "Zmeniť IP", lambda: setattr(self, 'active_input', 'ip_join'), self.small_font))

        self.screen.blit(self.small_font.render(f"Nickname: {self.player_name}", True, (255, 255, 255)), (180, 170))
        self.buttons.append(Button(550, 162, 110, 32, "Zmeniť meno", lambda: setattr(self, 'active_input', 'name_join'),
                                   self.small_font))

        self.buttons.extend([
            Button(200, 270, 180, 45, "Pripojiť", self.demo_connect_to_game, self.small_font, (0, 100, 0)),
            Button(420, 270, 180, 45, "Späť", lambda: setattr(self, 'menu_state', 'multiplayer_choice'),
                   self.small_font)
        ])

    def draw_settings(self):
        title = self.font.render("Nastavenia", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 50))

        self.draw_volume_slider("music", "Hudba", self.music_volume, 150)
        self.draw_volume_slider("sfx", "Efekty", self.sfx_volume, 215)

        self.buttons = [
            Button(300, 300, 200, 45, "Späť", lambda: setattr(self, 'menu_state', 'main'), self.small_font)
        ]

    def draw_volume_slider(self, target, label, value, y):
        label_text = self.small_font.render(f"{label}: {int(value * 100)}%", True, (255, 255, 255))
        self.screen.blit(label_text, (170, y - 12))

        track_rect = pygame.Rect(330, y, 270, 8)
        pygame.draw.rect(self.screen, (70, 70, 70), track_rect)

        fill_rect = pygame.Rect(track_rect.x, track_rect.y, int(track_rect.width * value), track_rect.height)
        pygame.draw.rect(self.screen, (80, 180, 120), fill_rect)

        knob_x = track_rect.x + int(track_rect.width * value)
        pygame.draw.circle(self.screen, (245, 245, 245), (knob_x, track_rect.centery), 12)
        pygame.draw.circle(self.screen, (40, 40, 40), (knob_x, track_rect.centery), 12, 2)

    def slider_value_from_pos(self, pos):
        track_x = 330
        track_width = 270
        return max(0.0, min(1.0, (pos[0] - track_x) / track_width))

    def handle_settings_slider(self, pos, preview_sfx=False):
        slider_zones = {
            "music": pygame.Rect(318, 134, 294, 40),
            "sfx": pygame.Rect(318, 199, 294, 40)
        }

        target = self.dragging_slider
        if target is None:
            for slider_name, zone in slider_zones.items():
                if zone.collidepoint(pos):
                    target = slider_name
                    self.dragging_slider = slider_name
                    break

        if target is None:
            return False

        value = self.slider_value_from_pos(pos)
        if target == "music":
            self.music_volume = value
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except pygame.error:
                pass
        else:
            self.sfx_volume = value
            if self.preview_sound:
                self.preview_sound.set_volume(self.sfx_volume)
                current_time = pygame.time.get_ticks()
                if preview_sfx and current_time - self.last_sfx_preview_time > 150:
                    self.preview_sound.play()
                    self.last_sfx_preview_time = current_time

        self.save_settings()
        return True
    def draw_input_overlay(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(self.WIDTH // 2 - 175, self.HEIGHT // 2 - 30, 350, 60)
        pygame.draw.rect(self.screen, (40, 40, 40), box)
        pygame.draw.rect(self.screen, (255, 255, 255), box, 2)

        prompt_str = "Zadaj svoje meno:" if 'name' in self.active_input else "Zadaj IP adresu servera:"
        curr_val = self.player_name if 'name' in self.active_input else self.ip_input_text

        if pygame.time.get_ticks() % 1000 < 500:
            curr_val += "_"

        lbl = self.small_font.render(prompt_str, True, (255, 255, 0))
        txt = self.small_font.render(curr_val, True, (255, 255, 255))

        self.screen.blit(lbl, (box.x, box.y - 30))
        self.screen.blit(txt, (box.x + 15, box.y + 18))

    def run(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.active_input:
                            self.active_input = None
                        else:
                            if self.menu_state == 'main':
                                self.running = False
                            elif self.menu_state == 'start_choice':
                                self.menu_state = 'main'
                            elif self.menu_state in ['multiplayer_choice', 'settings', 'highscores']:
                                self.menu_state = 'main'
                            elif self.menu_state in ['create_server', 'join_server']:
                                self.menu_state = 'multiplayer_choice'

                    if self.active_input:
                        if event.key == pygame.K_RETURN:
                            self.active_input = None
                        elif event.key == pygame.K_BACKSPACE:
                            if 'name' in self.active_input:
                                self.player_name = self.player_name[:-1]
                            else:
                                self.ip_input_text = self.ip_input_text[:-1]
                        else:
                            if event.unicode.isprintable():
                                if 'name' in self.active_input and len(self.player_name) < 15:
                                    self.player_name += event.unicode
                                elif 'ip' in self.active_input and len(self.ip_input_text) < 20:
                                    self.ip_input_text += event.unicode

                if event.type == pygame.MOUSEBUTTONUP:
                    self.dragging_slider = None

                if event.type == pygame.MOUSEMOTION and self.menu_state == 'settings' and self.dragging_slider:
                    self.handle_settings_slider(event.pos, preview_sfx=True)

                if event.type == pygame.MOUSEBUTTONDOWN and not self.active_input:
                    if self.menu_state == 'settings' and self.handle_settings_slider(event.pos, preview_sfx=True):
                        continue

                    for button in self.buttons:
                        button.handle_click(event.pos)

            self.bg.update()
            self.bg.draw(self.screen)

            self.buttons = []

            if self.menu_state == 'main':
                self.draw_main_menu()
            elif self.menu_state == 'start_choice':
                self.draw_start_choice()
            elif self.menu_state == 'multiplayer_choice':
                self.draw_multiplayer_choice()
            elif self.menu_state == 'create_server':
                self.draw_create_server()
            elif self.menu_state == 'join_server':
                self.draw_join_server()
            elif self.menu_state == 'settings':
                self.draw_settings()
            elif self.menu_state == 'highscores':
                self.draw_highscores()

            if not self.active_input:
                for button in self.buttons:
                    button.draw(self.screen)

            if self.active_input:
                self.draw_input_overlay()

            if self.error_message and pygame.time.get_ticks() - self.error_time < 3000:
                err_surf = self.small_font.render(self.error_message, True, (255, 50, 50))
                self.screen.blit(err_surf, (self.WIDTH // 2 - err_surf.get_width() // 2, self.HEIGHT - 35))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

