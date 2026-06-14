import pygame
import json
import subprocess
import sys

from game.game import Game
from game.background import Background
from game.paths import project_path
from game.network_config import PORT


class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label, font, callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.font = font
        self.callback = callback
        self.dragging = False

        self.knob_radius = int(h * 0.8)
        self.update_knob_position()

    def update_knob_position(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_x = self.rect.x + ratio * self.rect.width
        self.knob_x = max(self.rect.x, min(self.rect.x + self.rect.width, self.knob_x))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            knob_rect = pygame.Rect(self.knob_x - self.knob_radius * 2, self.rect.y - self.knob_radius,
                                    self.knob_radius * 4, self.rect.height + self.knob_radius * 2)
            if knob_rect.collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = pygame.mouse.get_pos()[0]
            new_x = max(self.rect.x, min(self.rect.x + self.rect.width, mouse_x))
            self.knob_x = new_x

            ratio = (new_x - self.rect.x) / self.rect.width
            old_value = self.value
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            self.value = max(self.min_val, min(self.max_val, self.value))

            if self.callback and abs(self.value - old_value) > 0.001:
                self.callback(self.value)

    def draw(self, screen):
        pygame.draw.rect(screen, (40, 40, 40), self.rect, border_radius=4)

        fill_width = (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(screen, (255, 255, 255), fill_rect, border_radius=4)

        pygame.draw.circle(screen, (200, 200, 200), (int(self.knob_x), self.rect.centery), self.knob_radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.knob_x), self.rect.centery), self.knob_radius - 2)

        label_text = f"{self.label}: {int(self.value * 100)}%"
        label_surf = self.font.render(label_text, True, (255, 255, 255))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 28))


class Button:
    def __init__(self, x, y, w, h, text, action, font, color=(50, 50, 50), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.font = font
        self.color = color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        draw_color = tuple(min(c + 30, 255) for c in self.color) if self.is_hovered else self.color

        pygame.draw.rect(screen, draw_color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, width=1, border_radius=6)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

class ScoreTable:
    def __init__(self, x, y, width, height, font):

        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.scores = []

        self.score_file = "highscores.json"

        self.gold_color = (242, 193, 46)
        self.silver_color = (186, 194, 204)
        self.bronze_color = (214, 131, 87)
        self.default_color = (220, 220, 220)

        self.load_scores()

    def load_scores(self):
        try:
            with open(self.score_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.scores = data.get('scores', [])
                self.scores = [(item['name'], item['score']) for item in self.scores]
        except FileNotFoundError:
            self.scores = []
        except Exception as e:
            print(f"Chyba pri načítaní skóre: {e}")
            self.scores = []

    def save_scores(self):
        try:
            data = {
                'scores': [{'name': name, 'score': score} for name, score in self.scores]
            }
            with open(self.score_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Chyba pri ukladaní skóre: {e}")

    def add_score(self, name, score):
        self.scores.append((name, score))
        self.scores.sort(key=lambda x: x[1], reverse=True)
        self.scores = self.scores[:10]
        self.save_scores()

    def get_rank_color(self, rank):
        if rank == 0:
            return self.gold_color
        elif rank == 1:
            return self.silver_color
        elif rank == 2:
            return self.bronze_color
        return self.default_color

    def draw(self, screen):
        bg_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_surface.fill((30, 30, 30))
        screen.blit(bg_surface, (self.rect.x, self.rect.y))

        pygame.draw.rect(screen, (255, 255, 255), self.rect, width=2, border_radius=8)

        header_y = self.rect.y + 20

        rank_header = self.font.render("#", True, (255, 215, 0))
        name_header = self.font.render("Meno", True, (255, 215, 0))
        score_header = self.font.render("Skóre", True, (255, 215, 0))

        screen.blit(rank_header, (self.rect.x + 25, header_y))
        screen.blit(name_header, (self.rect.x + 70, header_y))
        screen.blit(score_header, (self.rect.x + self.rect.width - score_header.get_width() - 25, header_y))

        pygame.draw.line(screen, (255, 255, 255), (self.rect.x + 15, header_y + 30),
                         (self.rect.x + self.rect.width - 15, header_y + 30), 1)

        y_offset = header_y + 45
        row_height = 18

        max_rows = (self.rect.height - (y_offset - self.rect.y) - 15) // row_height

        for i, (name, score) in enumerate(self.scores[:int(max_rows)]):
            rank = i + 1
            rank_color = self.get_rank_color(i)

            if i % 2 == 0:
                row_surface = pygame.Surface((self.rect.width - 20, row_height - 4), pygame.SRCALPHA)
                row_surface.fill((255, 255, 255, 10))
                screen.blit(row_surface, (self.rect.x + 10, y_offset - 2))

            rank_text = self.font.render(f"{rank}.", True, rank_color)
            screen.blit(rank_text, (self.rect.x + 25, y_offset))

            name_text = self.font.render(name, True, (255, 255, 255))
            screen.blit(name_text, (self.rect.x + 70, y_offset))

            score_str = f"{score:,}".replace(",", " ")
            score_text = self.font.render(score_str, True, rank_color if rank <= 3 else (255, 255, 255))
            score_x = self.rect.x + self.rect.width - score_text.get_width() - 25
            screen.blit(score_text, (score_x, y_offset))

            y_offset += row_height

        if not self.scores:
            empty_text = self.font.render("Zatiaľ žiadne skóre", True, (100, 115, 130))
            empty_x = self.rect.x + (self.rect.width // 2) - (empty_text.get_width() // 2)
            empty_y = self.rect.y + (self.rect.height // 2)
            screen.blit(empty_text, (empty_x, empty_y))

class Menu:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 400
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Deerun - Menu")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 52, bold=True)
        self.small_font = pygame.font.SysFont(None, 28)
        self.score_font = pygame.font.SysFont(None, 24)
        self.bg = Background(self.WIDTH, self.HEIGHT, 5)

        self.music_volume = 0.5
        self.sfx_volume = 0.4
        self.settings_file = "settings.json"
        self.load_settings()

        try:
            pygame.mixer.music.load("sounds/music/background_music.mp3")
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except:
            print("Nepodarilo sa načítať hudbu na pozadí.")

        self.menu_state = 'main'
        self.buttons = []

        self.music_slider = None
        self.sfx_slider = None

        self.player_name = "Hrac"
        self.ip_input_text = "127.0.0.1"
        self.max_players_choice = 2
        self.active_input = None

        self.error_message = ""
        self.error_time = 0

        self.score_table = ScoreTable(self.WIDTH // 2 - 300, 80, 600, 230, self.score_font)

        self.available_characters = ["deer", "hamster", "horse", "nugget"]
        self.selected_character = "deer"
        self.character_images = self.load_character_images()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.music_volume = data.get('music_volume', 0.5)
                self.sfx_volume = data.get('sfx_volume', 0.4)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Chyba pri načítaní nastavení: {e}")

    def save_settings(self):
        try:
            data = {
                'music_volume': self.music_volume,
                'sfx_volume': self.sfx_volume,
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Chyba pri ukladaní nastavení: {e}")

    def load_character_images(self):
        characters = {}
        for char in self.available_characters:
            path = f"assets/characters/{char}/idle.png"
            try:
                img = pygame.image.load(path)
                characters[char] = pygame.transform.scale(img, (60, 60))
            except pygame.error:
                fallback = pygame.Surface((60, 60))
                fallback.fill((200, 0, 0))
                characters[char] = fallback

        return characters

    def music_change(self, value):
        self.music_volume = value
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except:
            pass
        self.save_settings()

    def sfx_change(self, value):
        self.sfx_volume = value
        self.save_settings()

    def show_error(self, text):
        self.error_message = text
        self.error_time = pygame.time.get_ticks()

    def start_singleplayer(self):
        if not self.player_name.strip():
            self.show_error("Zadaj platné meno hráča!")
            return

        try:
            pygame.mixer.music.stop()
        except:
            pass

        game = Game(self.screen, music_volume=self.music_volume, sfx_volume=self.sfx_volume,
                    character=self.selected_character)
        final_score = game.run()

        if final_score and final_score > 0:
            self.score_table.add_score(self.player_name, final_score)

        try:
            pygame.mixer.music.play(-1)
        except:
            pass
        self.menu_state = 'main'

    def start_multiplayer(self, ip):
        try:
            pygame.mixer.music.stop()
        except:
            pass
        from client import Network
        n = Network(ip)
        if n.player_id is None:
            n.close()
            self.show_error("Nepodarilo sa pripojiť k serveru!")
            return
        lobby_running = True
        lobby_clock = pygame.time.Clock()
        while lobby_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    n.close()
                    lobby_running = False
                    self.menu_state = 'main'
                    return
            response = n.send({"type": "lobby_join", "name": self.player_name, "character": self.selected_character})
            if not response:
                n.close()
                self.show_error("Spojenie so serverom prerušené!")
                return
            self.screen.fill((30, 30, 30))
            title_text = self.font.render("Lobby Čakáreň", True, (255, 255, 255))
            self.screen.blit(title_text, (self.WIDTH // 2 - title_text.get_width() // 2, 40))
            count_text = self.small_font.render(f"Hráči: {response['total_connected']} / {response['max_players']}", True, (200, 200, 200))
            self.screen.blit(count_text, (self.WIDTH // 2 - count_text.get_width() // 2, 100))
            y_pos = 150
            for p_id, p_info in response["players"].items():
                p_str = f"Hráč {p_id}: {p_info['name']} ({p_info['character'].upper()})"
                p_color = (100, 255, 100) if p_id == n.player_id else (255, 255, 255)
                p_surf = self.small_font.render(p_str, True, p_color)
                self.screen.blit(p_surf, (self.WIDTH // 2 - p_surf.get_width() // 2, y_pos))
                y_pos += 30
            if response["game_started"]:
                lobby_running = False
                break
            if response.get("countdown", 10) <= 10 and response["total_connected"] == response["max_players"]:
                cd_str = f"Hra začína o: {response['countdown']}s"
                cd_surf = self.font.render(cd_str, True, (255, 215, 0))
                self.screen.blit(cd_surf, (self.WIDTH // 2 - cd_surf.get_width() // 2, 300))
            else:
                wait_surf = self.small_font.render("Čaká sa na naplnenie serveru...", True, (150, 150, 150))
                self.screen.blit(wait_surf, (self.WIDTH // 2 - wait_surf.get_width() // 2, 300))
            pygame.display.flip()
            lobby_clock.tick(30)
        try:
            from game.multiplayer_game import MultiplayerGame
            game = MultiplayerGame(
                self.screen,
                response["max_players"],
                music_volume=self.music_volume,
                sfx_volume=self.sfx_volume,
                player_name=self.player_name,
                character=self.selected_character,
                local_player_id=n.player_id,
                initial_players=response.get("players"),
            )
            game.network = n
            game.run()
        except ImportError:
            game = Game(self.screen, music_volume=self.music_volume, sfx_volume=self.sfx_volume, character=self.selected_character)
            if hasattr(game, "run_multiplayer"):
                game.run_multiplayer(n, self.player_name)
            else:
                game.run()
        n.close()
        try:
            pygame.mixer.music.play(-1)
        except:
            pass
        self.menu_state = 'main'

    def demo_create_server(self):
        try:
            subprocess.Popen(
                [sys.executable, str(project_path("server.py")), str(self.max_players_choice)],
                cwd=str(project_path()),
            )
            self.start_multiplayer("127.0.0.1")
        except Exception as e:
            self.show_error("Nepodarilo sa spustiť server")


    def get_local_ip(self):
        """Získa lokálnu IP adresu"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"


    def demo_connect_to_game(self):
        if not self.ip_input_text:
            self.show_error("Zadaj IP adresu")
            return
        self.start_multiplayer(self.ip_input_text)

    def show_scores(self):
        self.menu_state = 'scores'

    def change_name(self):
        self.active_input = 'name_settings'

    def change_character(self, direction):
        current_index = self.available_characters.index(self.selected_character)
        new_index = (current_index + direction) % len(self.available_characters)
        self.selected_character = self.available_characters[new_index]

    def draw_main_menu(self):
        title = self.font.render("DEERUN", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 40))
        self.buttons = [
            Button(300, 120, 200, 42, "Štart", lambda: setattr(self, 'menu_state', 'start_choice'), self.small_font),
            Button(300, 175, 200, 42, "Skóre", self.show_scores, self.small_font),
            Button(300, 230, 200, 42, "Nastavenia", lambda: setattr(self, 'menu_state', 'settings'), self.small_font),
            Button(300, 285, 200, 42, "Ukončiť", lambda: setattr(self, 'running', False), self.small_font)
        ]

    def draw_scores(self):
        title = self.font.render("Tabuľka skóre", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 20))
        self.score_table.draw(self.screen)
        self.buttons = [
            Button(300, 340, 200, 42, "Späť", lambda: setattr(self, 'menu_state', 'main'), self.small_font)
        ]

    def draw_start_choice(self):
        title = self.font.render("Výber režimu", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 50))
        self.buttons = [
            Button(300, 140, 200, 42, "Singleplayer", self.start_singleplayer, self.small_font),
            Button(300, 195, 200, 42, "Multiplayer", lambda: setattr(self, 'menu_state', 'multiplayer_choice'),
                   self.small_font),
            Button(300, 270, 200, 42, "Späť", lambda: setattr(self, 'menu_state', 'main'), self.small_font)
        ]
        info_text = self.small_font.render(f"Hráč: {self.player_name}", True, (230, 230, 230))
        self.screen.blit(info_text, (20, self.HEIGHT - 35))

    def draw_multiplayer_choice(self):
        title = self.font.render("Multiplayer", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 50))
        self.buttons = [
            Button(300, 140, 200, 42, "Pripojiť sa", lambda: setattr(self, 'menu_state', 'join_server'),
                   self.small_font),
            Button(300, 195, 200, 42, "Vytvoriť server", lambda: setattr(self, 'menu_state', 'create_server'),
                   self.small_font),
            Button(300, 270, 200, 42, "Späť", lambda: setattr(self, 'menu_state', 'start_choice'), self.small_font)
        ]

    def draw_create_server(self):
        title = self.font.render("Vytvoriť server", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 30))

        local_ip = self.get_local_ip()
        ip_text = self.small_font.render(f"Vaša IP adresa: {local_ip}", True, (100, 255, 100))
        self.screen.blit(ip_text, (self.WIDTH // 2 - ip_text.get_width() // 2, 80))
        port_text = self.small_font.render(f"Port: {PORT}", True, (200, 200, 200))
        self.screen.blit(port_text, (self.WIDTH // 2 - port_text.get_width() // 2, 108))

        self.screen.blit(self.small_font.render("Počet hráčov (max 4):", True, (255, 255, 255)), (180, 150))
        for i, num in enumerate([2, 3, 4]):
            btn_color = (0, 120, 0) if self.max_players_choice == num else (50, 50, 50)
            self.buttons.append(
                Button(420 + (i * 65), 142, 55, 35, str(num), lambda n=num: setattr(self, 'max_players_choice', n),
                       self.small_font, btn_color))

        self.buttons.extend([
            Button(190, 270, 200, 42, "Vytvoriť server", self.demo_create_server, self.small_font, (0, 100, 0)),
            Button(410, 270, 200, 42, "Späť", lambda: setattr(self, 'menu_state', 'multiplayer_choice'),
                   self.small_font)
        ])

    def draw_join_server(self):
        title = self.font.render("Pripojiť sa na server", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 30))

        self.screen.blit(self.small_font.render(f"IP Servera: {self.ip_input_text}", True, (255, 255, 255)), (180, 120))
        self.buttons.append(
            Button(550, 112, 110, 32, "Zmeniť IP", lambda: setattr(self, 'active_input', 'ip_join'), self.small_font))

        self.buttons.extend([
            Button(190, 270, 200, 42, "Pripojiť", self.demo_connect_to_game, self.small_font, (0, 100, 0)),
            Button(410, 270, 200, 42, "Späť", lambda: setattr(self, 'menu_state', 'multiplayer_choice'),
                   self.small_font)
        ])

    def draw_settings(self):
        title = self.font.render("Nastavenia", True, (255, 255, 255))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 25))

        if self.music_slider is None:
            self.music_slider = Slider(250, 90, 300, 16, 0.0, 1.0, self.music_volume, "Hlasitosť hudby",
                                       self.small_font, self.music_change)
            self.sfx_slider = Slider(250, 160, 300, 16, 0.0, 1.0, self.sfx_volume, "Hlasitosť efektov", self.small_font,
                                     self.sfx_change)

        self.music_slider.draw(self.screen)
        self.sfx_slider.draw(self.screen)

        text_bg_rect = pygame.Rect(180, 210, 330, 36)
        pygame.draw.rect(self.screen, (30, 30, 30, 150), text_bg_rect, border_radius=6)
        pygame.draw.rect(self.screen, (100, 100, 100), text_bg_rect, width=1, border_radius=6)

        name_text = self.small_font.render(f"Meno hráča: {self.player_name}", True, (255, 255, 255))
        self.screen.blit(name_text, (195, 218))

        self.buttons.append(
            Button(525, 210, 100, 36, "Zmeniť", self.change_name, self.small_font)
        )

        char_bg_rect = pygame.Rect(180, 260, 440, 70)
        pygame.draw.rect(self.screen, (30, 30, 30, 150), char_bg_rect, border_radius=6)
        pygame.draw.rect(self.screen, (100, 100, 100), char_bg_rect, width=1, border_radius=6)

        char_label = self.small_font.render("Výber postavy:", True, (255, 255, 255))
        self.screen.blit(char_label, (195, 270))

        char_name_text = self.small_font.render(self.selected_character.upper(), True, (255, 215, 0))
        self.screen.blit(char_name_text, (195, 295))

        if self.selected_character in self.character_images:
            char_img = self.character_images[self.selected_character]
            if char_img:
                self.screen.blit(char_img, (400, 265))

        self.buttons.append(
            Button(480, 275, 50, 36, "<", lambda: self.change_character(-1), self.small_font)
        )
        self.buttons.append(
            Button(540, 275, 50, 36, ">", lambda: self.change_character(1), self.small_font)
        )

        self.buttons.append(
            Button(300, 345, 200, 42, "Späť", lambda: setattr(self, 'menu_state', 'main'), self.small_font)
        )

    def draw_input_overlay(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(self.WIDTH // 2 - 175, self.HEIGHT // 2 - 30, 350, 60)
        pygame.draw.rect(self.screen, (30, 30, 30), box, border_radius=6)
        pygame.draw.rect(self.screen, (73, 162, 227), box, 2, border_radius=6)

        if self.active_input == 'name_settings':
            prompt_str = "Zadaj svoje meno:"
            curr_val = self.player_name
            max_len = 15
        else:
            prompt_str = "Zadaj IP adresu servera:"
            curr_val = self.ip_input_text
            max_len = 15

        if pygame.time.get_ticks() % 1000 < 500:
            curr_val += "_"

        lbl = self.small_font.render(prompt_str, True, (255, 215, 0))
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
                            elif self.menu_state in ['scores', 'start_choice', 'multiplayer_choice', 'settings']:
                                self.menu_state = 'main'
                            elif self.menu_state in ['create_server', 'join_server']:
                                self.menu_state = 'multiplayer_choice'

                    if self.active_input:
                        if event.key == pygame.K_RETURN:
                            if self.active_input == 'name_settings' and not self.player_name.strip():
                                self.player_name = "Hrac"
                            self.active_input = None
                        elif event.key == pygame.K_BACKSPACE:
                            if self.active_input == 'name_settings':
                                self.player_name = self.player_name[:-1]
                            else:
                                self.ip_input_text = self.ip_input_text[:-1]
                        else:
                            if event.unicode.isprintable():
                                if self.active_input == 'name_settings' and len(self.player_name) < 15:
                                    new_name = self.player_name + event.unicode
                                    if new_name.strip():
                                        self.player_name = new_name
                                    else:
                                        pass
                                elif self.active_input == 'ip_join' and len(self.ip_input_text) < 15:
                                    if event.unicode.isdigit() or event.unicode == '.':
                                        self.ip_input_text += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN and not self.active_input:
                    for button in self.buttons:
                        button.handle_click(event.pos)

                if self.menu_state == 'settings' and self.music_slider and self.sfx_slider:
                    self.music_slider.handle_event(event)
                    self.sfx_slider.handle_event(event)

            self.bg.update()
            self.bg.draw(self.screen)

            self.buttons = []

            if self.menu_state == 'main':
                self.draw_main_menu()
            elif self.menu_state == 'scores':
                self.draw_scores()
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
