import random
import pygame
import pygame.mixer
from .background import Background
from .dino import Dino
from .obstacle import Obstacle
from .paths import project_path

class MultiplayerGame:
    def __init__(self, screen, player_count=4, music_volume=0.5, sfx_volume=0.4):
        self.screen = screen
        self.WIDTH, self.HEIGHT = 800, 400
        self.WORLD_WIDTH, self.WORLD_HEIGHT = 800, 400
        self.player_count = max(2, min(4, player_count))
        pygame.display.set_caption("Deerun - Multiplayer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 26)
        self.tiny_font = pygame.font.SysFont(None, 22)
        self.world_aspect = self.WORLD_WIDTH / self.WORLD_HEIGHT
        available_players = [
            {"name": "P1", "key": pygame.K_SPACE, "key_label": "SPACE", "dino": Dino(100, 300), "alive": True},
            {"name": "P2", "key": pygame.K_w, "key_label": "W", "dino": Dino(100, 300), "alive": True},
            {"name": "P3", "key": pygame.K_UP, "key_label": "UP", "dino": Dino(100, 300), "alive": True},
            {"name": "P4", "key": pygame.K_RETURN, "key_label": "ENTER", "dino": Dino(100, 300), "alive": True},
        ]
        self.players = available_players[:self.player_count]
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
        except pygame.error as e:
            print(f"Chyba pri nacitani multiplayer zvukov: {e}")
            self.jump_sound = None
            self.crash_sound = None

    def play_music(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(project_path("sounds", "music", "background_music.mp3"))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Chyba pri nacitani multiplayer hudby: {e}")

    def play_sfx(self, sound):
        if not sound or self.sfx_volume <= 0:
            return
        try:
            channel = pygame.mixer.find_channel(True)
            if channel:
                channel.play(sound)
            else:
                sound.play()
        except pygame.error as e:
            print(f"Chyba pri prehravani SFX: {e}")

    def handle_events(self):
        local_id = self.network.player_id if hasattr(self, "network") else 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_over:
                        self.return_to_menu = True
                    else:
                        self.running = False
                    return
                if event.key == pygame.K_r and self.game_over:
                    self.restart_game()
                    return
                if self.game_over:
                    continue
                if event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w, pygame.K_RETURN]:
                    player = self.players[local_id]
                    if player["alive"] and not player["dino"].jumping:
                        player["dino"].jump()
                        self.play_sfx(self.jump_sound)

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

    def update(self):
        if self.game_over:
            return
        local_id = self.network.player_id if hasattr(self, "network") else 0
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
        if self.players[local_id]["alive"]:
            for obstacle in self.obstacles:
                if self.players[local_id]["dino"].rect.colliderect(obstacle.rect):
                    self.players[local_id]["alive"] = False
                    self.play_sfx(self.crash_sound)
                    break
        if hasattr(self, "network") and self.network:
            local_dino = self.players[local_id]["dino"]
            local_data = {
                "y": local_dino.rect.y,
                "is_jumping": local_dino.jumping,
                "alive": self.players[local_id]["alive"]
            }
            if local_id == 0:
                local_data["score"] = self.score
                local_data["level"] = self.level
                local_data["game_speed"] = self.game_speed
                local_data["obstacles"] = [{"x": obs.x, "type": obs.type} for obs in self.obstacles]
            response = self.network.send({"type": "update", "data": local_data})
            if response and "players" in response:
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
                for p_id_key, p_info in response["players"].items():
                    p_id = int(p_id_key)
                    if p_id != local_id and p_id < len(self.players):
                        remote_dino = self.players[p_id]["dino"]
                        remote_dino.rect.y = p_info.get("y", 300)
                        if hasattr(remote_dino, "y"):
                            remote_dino.y = p_info.get("y", 300)
                        remote_dino.jumping = p_info.get("is_jumping", False)
                        self.players[p_id]["alive"] = p_info.get("alive", True)
        alive_players = [index for index, player in enumerate(self.players) if player["alive"]]
        if len(alive_players) <= 1:
            self.game_over = True
            self.winner_index = alive_players[0] if alive_players else None
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass

    def draw_world_for_player(self, player):
        self.bg.draw(self.world_surface)
        player["dino"].draw(self.world_surface)
        for obstacle in self.obstacles:
            obstacle.draw(self.world_surface)

    def draw_player_overlay(self, target_rect, player_index):
        player = self.players[player_index]
        label = self.tiny_font.render(
            f"{player['name']}  skok: {player['key_label']}", True, (255, 255, 255)
        )
        self.screen.blit(label, (target_rect.x + 10, target_rect.y + 8))
        score_text = self.tiny_font.render(f"Score: {self.score // 10}", True, (255, 255, 255))
        level_text = self.tiny_font.render(f"Level: {self.level}", True, (255, 255, 255))
        score_x = target_rect.right - score_text.get_width() - 10
        level_x = target_rect.right - level_text.get_width() - 10
        self.screen.blit(score_text, (score_x, target_rect.y + 8))
        self.screen.blit(level_text, (level_x, target_rect.y + 30))
        if not player["alive"]:
            overlay = pygame.Surface((target_rect.width, target_rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 155))
            self.screen.blit(overlay, target_rect.topleft)
            eliminated = self.small_font.render("Vypadol", True, (255, 70, 70))
            self.screen.blit(
                eliminated,
                (
                    target_rect.centerx - eliminated.get_width() // 2,
                    target_rect.centery - eliminated.get_height() // 2,
                ),
            )

    def draw_game_over(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))
        if self.winner_index is None:
            title = "REMIZA"
        else:
            title = f"VYHRAL {self.players[self.winner_index]['name']}"
        title_text = self.font.render(title, True, (255, 230, 80))
        restart_text = self.small_font.render("R - restart    ESC - menu", True, (230, 230, 230))
        self.screen.blit(title_text, (self.WIDTH // 2 - title_text.get_width() // 2, self.HEIGHT // 2 - 40))
        self.screen.blit(restart_text, (self.WIDTH // 2 - restart_text.get_width() // 2, self.HEIGHT // 2 + 10))

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
        view_positions = [
            pygame.Rect(0, 0, self.WIDTH // 2, self.HEIGHT // 2),
            pygame.Rect(self.WIDTH // 2, 0, self.WIDTH // 2, self.HEIGHT // 2),
            pygame.Rect(0, self.HEIGHT // 2, self.WIDTH // 2, self.HEIGHT // 2),
            pygame.Rect(self.WIDTH // 2, self.HEIGHT // 2, self.WIDTH // 2, self.HEIGHT // 2),
        ]
        return view_positions

    def draw_split_lines(self):
        if self.player_count == 2:
            pygame.draw.line(self.screen, (245, 245, 245), (self.WIDTH // 2, 0), (self.WIDTH // 2, self.HEIGHT), 2)
        elif self.player_count == 3:
            pygame.draw.line(self.screen, (245, 245, 245), (self.WIDTH // 2, 0), (self.WIDTH // 2, self.HEIGHT), 2)
            pygame.draw.line(self.screen, (245, 245, 245), (0, self.HEIGHT // 2), (self.WIDTH, self.HEIGHT // 2), 2)
        else:
            pygame.draw.line(self.screen, (245, 245, 245), (self.WIDTH // 2, 0), (self.WIDTH // 2, self.HEIGHT), 2)
            pygame.draw.line(self.screen, (245, 245, 245), (0, self.HEIGHT // 2), (self.WIDTH, self.HEIGHT // 2), 2)

    def restart_game(self):
        for player in self.players:
            player["dino"] = Dino(100, 300)
            player["alive"] = True
        self.obstacles = []
        self.bg = Background(self.WORLD_WIDTH, self.WORLD_HEIGHT, 5)
        self.game_over = False
        self.winner_index = None
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