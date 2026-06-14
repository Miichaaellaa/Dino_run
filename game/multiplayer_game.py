import random
import pygame
import pygame.mixer
from .background import Background
from .dino import Dino
from .obstacle import Obstacle
from .paths import project_path

DINO_START_Y = 270


class MultiplayerGame:
    def __init__(
            self,
            screen,
            player_count=4,
            music_volume=0.5,
            sfx_volume=0.4,
            player_name="Hrac",
            character="deer",
            fast_animation=True,
            local_player_id=0,
            initial_players=None
    ):
        self.screen = screen
        self.WIDTH, self.HEIGHT = 800, 400
        self.WORLD_WIDTH, self.WORLD_HEIGHT = 800, 400
        self.player_count = max(2, min(4, player_count))
        try:
            local_player_id = int(local_player_id)
        except (TypeError, ValueError):
            local_player_id = 0
        self.local_player_id = max(0, min(self.player_count - 1, local_player_id))
        self.local_player_name = str(
            player_name or f"P{self.local_player_id + 1}").strip() or f"P{self.local_player_id + 1}"
        self.local_character = str(character or "deer").strip() or "deer"
        self.fast_animation = fast_animation
        pygame.display.set_caption("Deerun - Multiplayer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 26)
        self.tiny_font = pygame.font.SysFont(None, 22)
        self.world_aspect = self.WORLD_WIDTH / self.WORLD_HEIGHT

        self.players = []
        for i in range(self.player_count):
            name = self.local_player_name if i == self.local_player_id else f"P{i + 1}"
            char = self.local_character if i == self.local_player_id else "deer"
            self.players.append({
                "name": name,
                "character": char,
                "dino": Dino(100, DINO_START_Y, character=char, fast_animation=self.fast_animation),
                "alive": True,
                "display_score": 0,
                "frozen_surface": None,
            })

        self.obstacles = []
        self.bg = Background(self.WORLD_WIDTH, self.WORLD_HEIGHT, 5)
        self.world_surface = pygame.Surface((self.WORLD_WIDTH, self.WORLD_HEIGHT))
        self.game_over = False
        self.return_to_menu = False
        self.winner_index = None
        self.game_speed = 5
        self.level = 1
        self.score = 0
        self.car_types = ["auto_cervene", "auto_oranzove", "auto_zelene", "auto_modre", "dodavka", "taxi"]
        self.last_cars = []
        self.obstacle_frequency = 1500
        self.last_obstacle_time = pygame.time.get_ticks()
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self.jump_sound = None
        self.crash_sound = None
        self.waiting_for_restart = False
        self.server_countdown = 10
        self.round_id = 0
        self.last_alive_player = None
        if initial_players:
            self.apply_server_players(initial_players)
        self.load_sounds()
        self.play_music()

    def load_sounds(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(12)
            self.jump_sound = pygame.mixer.Sound(project_path("sounds", "effects", "deer_jump.wav"))
            self.jump_sound.set_volume(self.sfx_volume)
            self.crash_sound = pygame.mixer.Sound(project_path("sounds", "effects", "crash.wav"))
            self.crash_sound.set_volume(self.sfx_volume)
        except pygame.error:
            self.jump_sound = None
            self.crash_sound = None

    def play_music(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(project_path("sounds", "music", "background_music.mp3"))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def play_sfx(self, sound):
        if not sound or self.sfx_volume <= 0:
            return
        try:
            channel = pygame.mixer.find_channel(True)
            if channel:
                channel.play(sound)
            else:
                sound.play()
        except pygame.error:
            pass

    def get_local_id(self):
        network = getattr(self, "network", None)
        player_id = getattr(network, "player_id", self.local_player_id)
        try:
            player_id = int(player_id)
        except (TypeError, ValueError):
            player_id = self.local_player_id
        return max(0, min(len(self.players) - 1, player_id))

    def rebuild_player_dino(self, player, character):
        old_dino = player["dino"]
        new_dino = Dino(100, DINO_START_Y, character=character, fast_animation=self.fast_animation)
        new_dino.y = getattr(old_dino, "y", DINO_START_Y)
        new_dino.jumping = getattr(old_dino, "jumping", False)
        new_dino.jump_velocity = getattr(old_dino, "jump_velocity", 0)
        new_dino.frame_counter = getattr(old_dino, "frame_counter", 0)
        new_dino.rect = pygame.Rect(
            new_dino.x + 15,
            new_dino.y + 30,
            new_dino.width - 30,
            new_dino.height - 45,
        )
        player["dino"] = new_dino

    def sync_player_identity(self, player_id, player_info):
        if player_id < 0 or player_id >= len(self.players):
            return

        player = self.players[player_id]
        name = str(player_info.get("name") or player.get("name") or f"P{player_id + 1}").strip()
        character = str(player_info.get("character") or player.get("character") or "deer").strip() or "deer"
        player["name"] = name or f"P{player_id + 1}"

        if player.get("character") != character:
            player["character"] = character
            self.rebuild_player_dino(player, character)

    def apply_server_players(self, server_players):
        local_id = self.get_local_id()
        for player_id_key, player_info in server_players.items():
            try:
                player_id = int(player_id_key)
            except (TypeError, ValueError):
                continue
            if player_id < 0 or player_id >= len(self.players) or not isinstance(player_info, dict):
                continue

            self.sync_player_identity(player_id, player_info)
            player = self.players[player_id]
            was_alive = player.get("alive", True)
            new_alive = player_info.get("alive", True)
            player["display_score"] = player_info.get("display_score", player.get("display_score", 0))

            if player_id != local_id:
                remote_dino = player["dino"]
                remote_dino.y = player_info.get("y", DINO_START_Y)
                remote_dino.jumping = player_info.get("is_jumping", False)
                remote_dino.rect = pygame.Rect(
                    remote_dino.x + 15,
                    remote_dino.y + 30,
                    remote_dino.width - 30,
                    remote_dino.height - 45,
                )

            if was_alive and not new_alive:
                self.capture_frozen_view(player)
            elif new_alive:
                player["frozen_surface"] = None
            player["alive"] = new_alive

    def fit_text(self, text, max_width, font=None):
        font = font or self.tiny_font
        text = str(text or "").strip()
        if font.size(text)[0] <= max_width:
            return text

        for length in range(len(text) - 1, 2, -1):
            shortened = f"{text[:length]}."
            if font.size(shortened)[0] <= max_width:
                return shortened
        return text[:1]

    def render_world_to_surface(self, surface, player):
        self.bg.draw(surface)
        player["dino"].draw(surface)
        for obstacle in self.obstacles:
            obstacle.draw(surface)

    def capture_frozen_view(self, player):
        if player.get("frozen_surface") is not None:
            return
        frozen_surface = pygame.Surface((self.WORLD_WIDTH, self.WORLD_HEIGHT))
        self.render_world_to_surface(frozen_surface, player)
        player["frozen_surface"] = frozen_surface

    def choose_obstacle_type(self):
        if self.level < 2:
            available_types = ["auto_cervene", "auto_oranzove"]
        elif self.level < 4:
            available_types = ["auto_cervene", "auto_oranzove", "auto_zelene", "auto_modre"]
        elif self.level < 6:
            available_types = ["auto_modre", "auto_zelene", "taxi"]
        else:
            available_types = ["taxi", "auto_modre", "dodavka", "auto_zelene"]

        if len(self.last_cars) >= 3 and self.last_cars[-1] == self.last_cars[-2] == self.last_cars[-3]:
            available_types = [car for car in available_types if car != self.last_cars[-1]]

        obstacle_type = random.choice(available_types or self.car_types)
        self.last_cars.append(obstacle_type)
        if len(self.last_cars) > 5:
            self.last_cars.pop(0)
        return obstacle_type

    def handle_events(self):
        local_id = self.get_local_id()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.return_to_menu = True
                    return

                if event.key == pygame.K_r and self.game_over:
                    if hasattr(self, "network") and self.network:
                        self.network.send({"type": "restart"})
                    return

                if self.game_over:
                    continue
                if event.key == pygame.K_SPACE:
                    player = self.players[local_id]
                    if player["alive"] and not player["dino"].jumping:
                        player["dino"].jump()
                        self.play_sfx(self.jump_sound)

    def update(self):
        local_id = self.get_local_id()
        if hasattr(self, "network") and self.network:
            local_dino = self.players[local_id]["dino"]
            if self.players[local_id]["alive"]:
                self.players[local_id]["display_score"] = self.score // 10
            local_data = {
                "name": self.players[local_id]["name"],
                "character": self.players[local_id]["character"],
                "y": local_dino.y,
                "is_jumping": local_dino.jumping,
                "alive": self.players[local_id]["alive"],
                "display_score": self.players[local_id]["display_score"],
            }
            if local_id == 0 and not self.game_over:
                local_data["score"] = self.score
                local_data["level"] = self.level
                local_data["game_speed"] = self.game_speed
                local_data["obstacles"] = [{"x": obs.x, "type": obs.type} for obs in self.obstacles]

            response = self.network.send({"type": "update", "round_id": self.round_id, "data": local_data})
            if response:
                if response.get("abort_game"):
                    self.return_to_menu = True
                    return
                server_game_started = response.get("game_started", True)
                self.server_countdown = response.get("countdown", 10)

                old_round_id = self.round_id
                self.round_id = response.get("round_id", self.round_id)
                round_changed = old_round_id != self.round_id

                was_game_over = self.game_over
                server_game_over = response.get("global_game_over", False)

                if round_changed or (was_game_over and not server_game_over):
                    self.restart_game()

                self.game_over = server_game_over
                self.winner_index = response.get("global_winner")

                if not was_game_over and self.game_over:
                    try:
                        pygame.mixer.music.stop()
                    except pygame.error:
                        pass

                if "players" in response:
                    self.apply_server_players(response["players"])

                if "players" in response and server_game_started and not self.game_over:
                    p0_info = response["players"].get(0) or response["players"].get("0")
                    if local_id != 0 and p0_info:
                        self.score = p0_info.get("score", self.score)
                        self.level = p0_info.get("level", self.level)
                        self.game_speed = p0_info.get("game_speed", self.game_speed)
                        remote_obstacles = p0_info.get("obstacles", [])
                        if len(self.obstacles) != len(remote_obstacles):
                            self.obstacles = []
                            for obs in remote_obstacles:
                                self.obstacles.append(Obstacle(obs["x"], obs["type"], self.game_speed))
                        else:
                            for i, obs in enumerate(remote_obstacles):
                                self.obstacles[i].x = obs["x"]
                                if hasattr(self.obstacles[i], "rect"):
                                    self.obstacles[i].rect.x = obs["x"]
        if self.game_over:
            return

        if local_id == 0:
            self.score += 1
            self.level = self.score // 600 + 1
            self.game_speed = 5 + (self.level * 0.3)
            self.obstacle_frequency = max(800, 1500 - (self.level * 100))
            self.bg.speed = self.game_speed
            self.bg.update()
            current_time = pygame.time.get_ticks()
            if current_time - self.last_obstacle_time > self.obstacle_frequency:
                self.obstacles.append(Obstacle(self.WORLD_WIDTH, self.choose_obstacle_type(), self.game_speed))
                self.last_obstacle_time = current_time
            for obstacle in self.obstacles[:]:
                obstacle.update()
                if obstacle.x < -200:
                    self.obstacles.remove(obstacle)
        else:
            self.bg.speed = self.game_speed
            self.bg.update()

        if self.players[local_id]["alive"]:
            self.players[local_id]["dino"].update()
            for obstacle in self.obstacles:
                if self.players[local_id]["dino"].rect.colliderect(obstacle.rect):
                    self.players[local_id]["display_score"] = self.score // 10
                    self.capture_frozen_view(self.players[local_id])
                    self.players[local_id]["alive"] = False
                    self.play_sfx(self.crash_sound)
                    break

        if not (hasattr(self, "network") and self.network):
            alive_players = [index for index, player in enumerate(self.players) if player["alive"]]
            if len(alive_players) == 1:
                self.last_alive_player = alive_players[0]
            if len(alive_players) == 0:
                self.game_over = True
                self.winner_index = self.last_alive_player
                try:
                    pygame.mixer.music.stop()
                except pygame.error:
                    pass

    def draw_world_for_player(self, player):
        frozen_surface = player.get("frozen_surface")
        if not player["alive"] and frozen_surface:
            self.world_surface.blit(frozen_surface, (0, 0))
            return

        self.render_world_to_surface(self.world_surface, player)

    def draw_player_overlay(self, target_rect, player_index):
        player = self.players[player_index]

        info_str = f"{self.fit_text(player['name'], 120)} : {player.get('display_score', 0)}"
        score_text = self.tiny_font.render(info_str, True, (255, 255, 255))
        level_text = self.tiny_font.render(f"Level: {self.level}", True, (255, 255, 255))

        score_x = target_rect.x + 10
        level_x = target_rect.right - level_text.get_width() - 10

        # Obe hodnoty su na rovnakej y suradnici (+8) co ich zarovna uplne hore
        self.screen.blit(score_text, (score_x, target_rect.y + 8))
        self.screen.blit(level_text, (level_x, target_rect.y + 8))

        if not player["alive"]:
            overlay = pygame.Surface((target_rect.width, target_rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 155))
            self.screen.blit(overlay, target_rect.topleft)
            eliminated = self.small_font.render("Vypadol", True, (255, 70, 70))
            self.screen.blit(eliminated, (target_rect.centerx - eliminated.get_width() // 2,
                                          target_rect.centery - eliminated.get_height() // 2))

    def draw_game_over(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        if self.winner_index is None:
            title = "REMIZA"
        else:
            title = f"VYHRAL {self.players[self.winner_index]['name']}!"

        title_text = self.font.render(title, True, (255, 230, 80))

        # --- TABULKA HRÁČOV ---
        sorted_players = sorted(self.players, key=lambda p: p.get("display_score", 0), reverse=True)

        row_spacing = 40
        table_width = 340
        table_height = len(sorted_players) * row_spacing + 20

        # Matematika na vycentrovanie tabulky a nadpisu na stred celej obrazovky
        total_block_height = title_text.get_height() + 20 + table_height
        start_block_y = (self.HEIGHT - total_block_height) // 2

        title_y = start_block_y
        table_rect_y = title_y + title_text.get_height() + 20
        start_y = table_rect_y + 10

        self.screen.blit(title_text, (self.WIDTH // 2 - title_text.get_width() // 2, title_y))

        table_rect = pygame.Rect(self.WIDTH // 2 - table_width // 2, table_rect_y, table_width, table_height)
        pygame.draw.rect(self.screen, (40, 40, 40), table_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 230, 80), table_rect, 2, border_radius=12)

        for i, p in enumerate(sorted_players):
            color = (255, 230, 80) if i == 0 else (220, 220, 220)

            rank_text = self.small_font.render(f"{i + 1}.", True, color)
            name_text = self.small_font.render(self.fit_text(p["name"], 160, self.small_font), True, color)
            score_text = self.small_font.render(f"{p.get('display_score', 0)} b", True, color)

            y_pos = start_y + i * row_spacing
            self.screen.blit(rank_text, (table_rect.x + 20, y_pos))
            self.screen.blit(name_text, (table_rect.x + 60, y_pos))
            self.screen.blit(score_text, (table_rect.right - score_text.get_width() - 20, y_pos))

        restart_text = self.small_font.render("R - Okamzity restart hry pre vsetkych    ESC - menu", True,
                                              (200, 200, 200))
        self.screen.blit(restart_text, (self.WIDTH // 2 - restart_text.get_width() // 2, self.HEIGHT - 40))

    def draw(self):
        view_positions = self.get_view_positions()
        self.screen.fill((0, 0, 0))
        for index, cell_rect in enumerate(view_positions):
            self.draw_world_for_player(self.players[index])
            target_rect = self.fit_world_rect(cell_rect)
            scaled_view = pygame.transform.smoothscale(self.world_surface, target_rect.size)
            self.screen.blit(scaled_view, target_rect.topleft)
            self.draw_player_overlay(target_rect, index)
        self.draw_split_lines()
        if self.game_over:
            self.draw_game_over()
        pygame.display.flip()

    def fit_world_rect(self, cell_rect):
        width = cell_rect.width
        height = int(width / self.world_aspect)
        if height > cell_rect.height:
            height = cell_rect.height
            width = int(height * self.world_aspect)
        x = cell_rect.x + (cell_rect.width - width) // 2
        y = cell_rect.y + (cell_rect.height - height) // 2
        return pygame.Rect(x, y, width, height)

    def get_view_positions(self):
        if self.player_count == 2:
            return [
                pygame.Rect(0, 0, self.WIDTH // 2, self.HEIGHT),
                pygame.Rect(self.WIDTH // 2, 0, self.WIDTH // 2, self.HEIGHT),
            ]
        if self.player_count == 3:
            return [
                pygame.Rect(0, 0, self.WIDTH // 2, self.HEIGHT // 2),
                pygame.Rect(self.WIDTH // 2, 0, self.WIDTH // 2, self.HEIGHT // 2),
                pygame.Rect(0, self.HEIGHT // 2, self.WIDTH // 2, self.HEIGHT // 2),
            ]
        return [
            pygame.Rect(0, 0, self.WIDTH // 2, self.HEIGHT // 2),
            pygame.Rect(self.WIDTH // 2, 0, self.WIDTH // 2, self.HEIGHT // 2),
            pygame.Rect(0, self.HEIGHT // 2, self.WIDTH // 2, self.HEIGHT // 2),
            pygame.Rect(self.WIDTH // 2, self.HEIGHT // 2, self.WIDTH // 2, self.HEIGHT // 2),
        ]

    def draw_split_lines(self):
        if self.player_count == 2:
            pygame.draw.line(self.screen, (245, 245, 245), (self.WIDTH // 2, 0), (self.WIDTH // 2, self.HEIGHT), 2)
        elif self.player_count >= 3:
            pygame.draw.line(self.screen, (245, 245, 245), (self.WIDTH // 2, 0), (self.WIDTH // 2, self.HEIGHT), 2)
            pygame.draw.line(self.screen, (245, 245, 245), (0, self.HEIGHT // 2), (self.WIDTH, self.HEIGHT // 2), 2)

    def restart_game(self):
        for player in self.players:
            character = player.get("character", "deer")
            player["dino"] = Dino(100, DINO_START_Y, character=character, fast_animation=self.fast_animation)
            player["alive"] = True
        self.obstacles = []
        self.bg = Background(self.WORLD_WIDTH, self.WORLD_HEIGHT, 5)
        self.game_over = False
        self.winner_index = None
        self.last_alive_player = None
        self.game_speed = 5
        self.level = 1
        self.score = 0
        self.last_cars = []
        self.last_obstacle_time = pygame.time.get_ticks()
        self.play_music()

    def run(self):
        self.running = True
        while self.running:
            self.handle_events()
            if self.return_to_menu:
                return "menu"
            if not self.running:
                break
            self.update()
            self.draw()
            self.clock.tick(60)
        return "quit"