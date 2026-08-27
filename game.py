import math
import pygame
import os
import json
import random
from typing import Any, cast
from settings import *
from level_manager import LevelManager
from sprites import Paddle, Ball, PowerUp, Block, Particle, SecureBorder, SafetyNet, LaserProjectile
from menu import LevelSelectionMenu, MainMenu
from editor import LevelEditor

def get_level_name(lvl_nr: int) -> str:
    if lvl_nr <= 9:
        return f"Level00{lvl_nr}.txt"
    elif lvl_nr > 9 and lvl_nr <= 99:
        return f"Level0{lvl_nr}.txt"
    else:
        return f"Level{lvl_nr}.txt"

class Game:
    def __init__(self):
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode((DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MENU
        
        # Level-Verwaltung
        self.level_manager = LevelManager()
        self.current_level_num = 1
        self.unlocked_level = 1
        self.difficulty = DIFFICULTY_NORMAL
        self.highscores: dict[str, list[dict[str, Any]]] = {}
        
        # Unified Save & Load
        self.load_game_data()
        self.highscore_view_level = 1
        
        # Highscore-Rechtecke für Klicks definieren
        self.update_highscore_rects()
        
        # Scoring-Metriken
        self.level_start_ticks = 0
        self.elapsed_seconds_at_win = 0.0
        self.paddle_hits_count = 0
        self.powerups_collected_count = 0
        self.score_multiplier = 1.0
        self.final_score = 0
        self.qualifies_for_highscores = False
        self.is_score_saved = False
        self.player_name = ""
        
        # Menü & Editor
        self.menu = MainMenu()
        self.menu.set_difficulty_label(self.difficulty)
        self.level_selection_menu = LevelSelectionMenu(self.screen)
        self.editor = LevelEditor(self.screen)
        
        # Sprite-Gruppen
        self.all_sprites: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.blocks: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.powerups: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.balls: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.lasers: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.particles: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.secure_borders: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.safety_net: SafetyNet | None = None
        
        self.paddle: Paddle = Paddle()
        self.time_factor: float = 1.0 
        self.active_effects: dict[str, int] = {}
        
        # Visual Background Stars & Fireworks
        sw, sh = self.screen.get_width(), self.screen.get_height()
        self.bg_stars = [
            [random.randint(0, sw), random.randint(0, sh), random.uniform(0.2, 1.2)]
            for _ in range(50)
        ]
        self.fireworks_timer = 0

    def load_game_data(self):
        """Lädt alle Spieldaten aus game_data.json mit Abwärtskompatibilität."""
        if os.path.exists("game_data.json"):
            try:
                with open("game_data.json", "r") as file:
                    data = json.load(file)
                    self.unlocked_level = data.get("unlocked_level", 1)
                    self.difficulty = data.get("difficulty", DIFFICULTY_NORMAL)
                    self.highscores = data.get("highscores", {})
                print(f"[Load] game_data.json geladen. Fortschritt: Level {self.unlocked_level}")
                return
            except Exception as e:
                print(f"[Load-Fehler] game_data.json beschädigt: {e}")

        # Fallback & Migration von alten JSON-Dateien
        if os.path.exists("save_progress.json"):
            try:
                with open("save_progress.json", "r") as file:
                    save_data = json.load(file)
                    self.unlocked_level = save_data.get("unlocked_level", 1)
            except Exception as e:
                print(f"[Load] Fehler in save_progress.json: {e}")

        if os.path.exists("highscores.json"):
            try:
                with open("highscores.json", "r") as file:
                    self.highscores = json.load(file)
            except Exception as e:
                print(f"[Load] Fehler in highscores.json: {e}")

        self.save_game_data()

    def save_game_data(self):
        """Speichert Fortschritt, Highscores und Einstellungen in game_data.json."""
        data = {
            "unlocked_level": self.unlocked_level,
            "difficulty": self.difficulty,
            "highscores": self.highscores
        }
        try:
            with open("game_data.json", "w") as file:
                json.dump(data, file, indent=4)
            print(f"[Save] game_data.json erfolgreich gespeichert.")
        except Exception as e:
            print(f"[Save-Fehler] Konnte game_data.json nicht schreiben: {e}")

    def spawn_particles(self, x: float, y: float, color: tuple[int, ...], count: int = 12):
        for _ in range(count):
            p = Particle(x, y, color)
            self.particles.add(p)
            self.all_sprites.add(p)

    def start_game(self):
        self.all_sprites.empty()
        self.blocks.empty()
        self.powerups.empty()
        self.balls.empty()
        self.lasers.empty()
        self.particles.empty()
        self.secure_borders.empty()
        if self.safety_net:
            self.safety_net.kill()
            self.safety_net = None

        self.active_effects.clear()
        self.time_factor = 1.0
        self.score_multiplier = 1.0
        
        self.level_start_ticks = pygame.time.get_ticks()
        self.elapsed_seconds_at_win = 0.0
        self.paddle_hits_count = 0
        self.powerups_collected_count = 0
        self.is_score_saved = False
        self.player_name = ""
        
        pygame.display.set_caption(f"{TITLE} - Level {self.current_level_num} ({DIFFICULTY_SETTINGS[self.difficulty]['label']})")
        
        level_file = get_level_name(self.current_level_num)
        sw, sh = self.screen.get_width(), self.screen.get_height()
        self.blocks = self.level_manager.load_level(level_file, sw, sh)
        
        if len(self.blocks) == 0:
            self.state = STATE_MENU
            return

        self.reset_paddle()
        self.paddle_sticky = False
        
        diff_settings = DIFFICULTY_SETTINGS[self.difficulty]
        base_ball_speed = BALL_SPEED * diff_settings["ball_speed_mult"]
        
        start_ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - 8, speed_x=0, speed_y=-base_ball_speed)
        start_ball.attached = True
        self.balls.add(start_ball)
        
        self.all_sprites.add(self.paddle, self.balls, self.blocks)
        self.state = STATE_PLAYING

    def reset_paddle(self):
        sw, sh = self.screen.get_width(), self.screen.get_height()
        pos = self.paddle.rect.center if hasattr(self.paddle, 'rect') else (sw // 2, sh - 30)
        self.paddle.image = pygame.Surface((100, 15))
        self.paddle.image.fill(WHITE)
        self.paddle.rect = self.paddle.image.get_rect(centerx=pos[0], bottom=sh - 30)
        self.paddle.inverted_controls = False

    POSITIVE_EFFECTS = ["sticky_paddle", "expand_paddle", "slow_time",
                        "bigger_ball", "multiball", "piercing_shot",
                        "laser_paddle", "safety_net", "secure_border",
                        "magnet", "score_boost", "fireball"]
    NEGATIVE_EFFECTS = ["shrink_paddle", "speed_time", "smaller_ball",
                        "score_drain", "inverted_controls"]

    def spawn_powerup(self, x: int, y: int, guaranteed_type: str | None = None):
        diff_cfg = DIFFICULTY_SETTINGS[self.difficulty]
        spawn_chance: float = 1.0 if guaranteed_type else diff_cfg["powerup_chance"]
        if random.random() < spawn_chance:
            if guaranteed_type == 'P':
                chosen = random.choice(self.POSITIVE_EFFECTS)
            elif guaranteed_type == 'D':
                chosen = random.choice(self.NEGATIVE_EFFECTS)
            elif guaranteed_type:
                chosen = guaranteed_type
            else:
                chosen = random.choice(self.POSITIVE_EFFECTS + self.NEGATIVE_EFFECTS)
            p_up = PowerUp(x, y, chosen)
            self.powerups.add(p_up)
            self.all_sprites.add(p_up)

    def apply_powerup(self, powerup: PowerUp):
        self.powerups_collected_count += 1
        now = pygame.time.get_ticks()
        diff_cfg = DIFFICULTY_SETTINGS[self.difficulty]
        duration = int(8000 * diff_cfg["timer_mult"])
        etype = powerup.effect_type
        
        if etype == "sticky_paddle":
            self.paddle_sticky = True
            current_width = self.paddle.rect.width
            self.paddle.image = pygame.Surface((current_width, 15))
            self.paddle.image.fill(YELLOW)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            self.active_effects["sticky_paddle"] = now + duration
            
        elif etype == "expand_paddle":
            self.paddle.image = pygame.Surface((150, 15))
            color = YELLOW if self.paddle_sticky else GREEN
            self.paddle.image.fill(color)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            self.active_effects["paddle_size"] = now + duration
            
        elif etype == "shrink_paddle":
            self.paddle.image = pygame.Surface((60, 15))
            color = YELLOW if self.paddle_sticky else RED
            self.paddle.image.fill(color)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            self.active_effects["paddle_size"] = now + duration
            
        elif etype == "slow_time":
            self.time_factor = 0.6
            self.active_effects["time_distortion"] = now + duration
            
        elif etype == "speed_time":
            self.time_factor = 1.4
            self.active_effects["time_distortion"] = now + duration
            
        elif etype == "bigger_ball":
            for ball in self.balls: ball.set_size(14)
            self.active_effects["ball_size"] = now + duration
            
        elif etype == "smaller_ball":
            for ball in self.balls: ball.set_size(5)
            self.active_effects["ball_size"] = now + duration
            
        elif etype == "piercing_shot":
            for ball in self.balls: ball.set_piercing(True)
            self.active_effects["piercing"] = now + duration
            
        elif etype == "multiball":
            current_balls = list(self.balls)
            for b in current_balls:
                new_ball = Ball(b.rect.centerx, b.rect.centery, b.speed_x * -1, b.speed_y)
                if "ball_size" in self.active_effects: new_ball.set_size(b.radius)
                if "piercing" in self.active_effects: new_ball.set_piercing(True)
                if getattr(b, "is_fireball", False): new_ball.set_fireball(True)
                self.balls.add(new_ball)
                self.all_sprites.add(new_ball)
                
        elif etype == "laser_paddle":
            self.active_effects["laser_paddle"] = now + duration
            
        elif etype == "safety_net":
            if self.safety_net:
                self.safety_net.kill()
            sw, sh = self.screen.get_width(), self.screen.get_height()
            self.safety_net = SafetyNet(sw, sh)
            self.all_sprites.add(self.safety_net)
            self.active_effects["safety_net"] = now + duration

        elif etype == "secure_border":
            if len(self.secure_borders) == 0:
                sw, sh = self.screen.get_width(), self.screen.get_height()
                sb = SecureBorder(sw, sh)
                self.secure_borders.add(sb)
                self.all_sprites.add(sb)
            self.active_effects["secure_border"] = now + duration + 4000

        elif etype == "fireball":
            for ball in self.balls:
                ball.set_fireball(True)
            self.active_effects["fireball"] = now + duration
            
        elif etype == "magnet":
            self.active_effects["magnet"] = now + duration
            
        elif etype == "score_boost":
            self.score_multiplier = 1.5
            self.active_effects["score_modifier"] = now + duration
            
        elif etype == "score_drain":
            self.score_multiplier = 0.7
            self.active_effects["score_modifier"] = now + duration
            
        elif etype == "inverted_controls":
            self.paddle.inverted_controls = True
            self.active_effects["inverted_controls"] = now + duration

    def check_timers(self):
        now = pygame.time.get_ticks()
        
        if "paddle_size" in self.active_effects and now > self.active_effects["paddle_size"]:
            self.reset_paddle()
            if self.paddle_sticky:
                current_width = self.paddle.rect.width
                self.paddle.image = pygame.Surface((current_width, 15))
                self.paddle.image.fill(YELLOW)
                self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            del self.active_effects["paddle_size"]
            
        if "sticky_paddle" in self.active_effects and now > self.active_effects["sticky_paddle"]:
            self.paddle_sticky = False
            current_width = self.paddle.rect.width
            self.paddle.image = pygame.Surface((current_width, 15))
            if "paddle_size" in self.active_effects:
                if current_width > 100:
                    self.paddle.image.fill(GREEN)
                elif current_width < 100:
                    self.paddle.image.fill(RED)
                else:
                    self.paddle.image.fill(WHITE)
            else:
                self.paddle.image.fill(WHITE)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            del self.active_effects["sticky_paddle"]

        if "time_distortion" in self.active_effects and now > self.active_effects["time_distortion"]:
            self.time_factor = 1.0
            del self.active_effects["time_distortion"]
            
        if "ball_size" in self.active_effects and now > self.active_effects["ball_size"]:
            for ball in self.balls: ball.set_size(8)
            del self.active_effects["ball_size"]
            
        if "piercing" in self.active_effects and now > self.active_effects["piercing"]:
            for ball in self.balls: ball.set_piercing(False)
            del self.active_effects["piercing"]

        if "fireball" in self.active_effects and now > self.active_effects["fireball"]:
            for ball in self.balls: ball.set_fireball(False)
            del self.active_effects["fireball"]
            
        if "secure_border" in self.active_effects and now > self.active_effects["secure_border"]:
            for sb in self.secure_borders: sb.kill()
            del self.active_effects["secure_border"]
            
        if "magnet" in self.active_effects and now > self.active_effects["magnet"]:
            del self.active_effects["magnet"]
            
        if "score_modifier" in self.active_effects and now > self.active_effects["score_modifier"]:
            self.score_multiplier = 1.0
            del self.active_effects["score_modifier"]
            
        if "inverted_controls" in self.active_effects and now > self.active_effects["inverted_controls"]:
            self.paddle.inverted_controls = False
            del self.active_effects["inverted_controls"]

    def trigger_explosion(self, origin_block: Block):
        origin_block.kill()
        center_x = origin_block.rect.centerx
        center_y = origin_block.rect.centery
        self.spawn_particles(center_x, center_y, ORANGE, count=25)
        self.spawn_particles(center_x, center_y, RED, count=15)
        
        radius_x = BLOCK_WIDTH * 1.6
        radius_y = BLOCK_HEIGHT * 1.6

        surrounding = [
            b for b in list(self.blocks)
            if b != origin_block and abs(b.rect.centerx - center_x) <= radius_x and abs(b.rect.centery - center_y) <= radius_y
        ]
        
        for b in surrounding:
            if not b.alive():
                continue
            destroyed = b.hit(force_destroy=True)
            if destroyed:
                b.kill()
                self.spawn_particles(b.rect.centerx, b.rect.centery, YELLOW, count=10)
                if getattr(b, 'is_explosive', False) or b.block_type == 'B':
                    self.trigger_explosion(b)
                elif getattr(b, 'is_powerdown', False) or b.block_type == 'D':
                    self.spawn_powerup(b.rect.x, b.rect.y, guaranteed_type='D')
                else:
                    self.spawn_powerup(b.rect.x, b.rect.y, guaranteed_type='P' if (b.is_powerup or b.block_type == 'P') else None)

    def handle_portal_teleport(self, ball: Ball, portal_block: Block):
        now = pygame.time.get_ticks()
        if now - getattr(ball, 'last_teleport_ticks', 0) < 600:
            return
        
        portals = [b for b in self.blocks if b.block_type == 'T' and b != portal_block]
        if portals:
            dest_portal = random.choice(portals)
            ball.rect.centerx = dest_portal.rect.centerx
            ball.rect.centery = dest_portal.rect.centery + (35 if ball.speed_y > 0 else -35)
            ball.x = float(ball.rect.x)
            ball.y = float(ball.rect.y)
            ball.last_teleport_ticks = now

    def calculate_score(self, elapsed_seconds: float) -> int:
        base_score = 10000
        time_penalty = int(elapsed_seconds * 10 * (1.0 / self.time_factor))
        hit_penalty = self.paddle_hits_count * 20
        powerup_penalty = self.powerups_collected_count * 100
        
        score = (base_score - time_penalty - hit_penalty - powerup_penalty) * self.score_multiplier
        return max(0, int(score))

    def calculate_current_score(self) -> int:
        elapsed_seconds = (pygame.time.get_ticks() - self.level_start_ticks) / 1000.0
        return self.calculate_score(elapsed_seconds)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
        else:
            self.screen = pygame.display.set_mode((DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT), pygame.RESIZABLE)
        self.on_resize()

    def on_resize(self):
        sw, sh = self.screen.get_width(), self.screen.get_height()
        self.editor.screen = self.screen
        self.level_selection_menu.screen = self.screen
        self.update_highscore_rects()
        if self.state == STATE_PLAYING:
            if self.safety_net and self.safety_net.alive():
                self.safety_net.image = pygame.Surface((sw, 8))
                self.safety_net.image.fill((0, 220, 255))
                pygame.draw.rect(self.safety_net.image, WHITE, (0, 0, sw, 8), 1)
                self.safety_net.rect = self.safety_net.image.get_rect(topleft=(0, sh - 12))

    def update_highscore_rects(self):
        sw, sh = self.screen.get_width(), self.screen.get_height()
        self.hs_prev_rect = pygame.Rect(sw // 2 - 140, 110, 40, 35)
        self.hs_next_rect = pygame.Rect(sw // 2 + 100, 110, 40, 35)
        self.hs_delete_rect = pygame.Rect(sw // 2 - 210, sh - 80, 200, 45)
        self.hs_back_rect = pygame.Rect(sw // 2 + 10, sh - 80, 200, 45)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.VIDEORESIZE:
                if not self.is_fullscreen:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.on_resize()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)):
                    self.toggle_fullscreen()
                    continue

            if self.state == STATE_MENU:
                action = self.menu.handle_event(event)
                
                if action == "PLAY":
                    self.current_level_num = self.unlocked_level
                    self.start_game()
                    
                elif action == "LEVEL_SELECT":
                    self.state = STATE_LEVEL_SELECT
                    
                elif action == "DIFFICULTY":
                    if self.difficulty == DIFFICULTY_EASY:
                        self.difficulty = DIFFICULTY_NORMAL
                    elif self.difficulty == DIFFICULTY_NORMAL:
                        self.difficulty = DIFFICULTY_HARD
                    else:
                        self.difficulty = DIFFICULTY_EASY
                    self.menu.set_difficulty_label(self.difficulty)
                    self.save_game_data()
                    
                elif action == "EDITOR":
                    self.state = STATE_EDITOR
                    
                elif action == "FULLSCREEN":
                    self.toggle_fullscreen()

                elif action == "RESET":
                    self.unlocked_level = 1
                    self.current_level_num = 1
                    self.save_game_data()
                    print("[Spielstand] Fortschritt zurückgesetzt!")
                    
                elif action == "QUIT":
                    self.running = False
                
                elif action == "HIGHSCORE":
                    self.state = STATE_HIGHSCORE

            elif self.state == STATE_LEVEL_SELECT:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    chosen_level = self.level_selection_menu.handle_click(pygame.mouse.get_pos())
                    
                    if chosen_level == "BACK":
                        self.state = STATE_MENU
                        
                    elif chosen_level is not None:
                        self.current_level_num = chosen_level
                        self.start_game()
                
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU

            elif self.state == STATE_HIGHSCORE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.hs_back_rect.collidepoint(mouse_pos):
                        self.state = STATE_MENU
                    elif self.hs_delete_rect.collidepoint(mouse_pos):
                        level_key = get_level_name(self.highscore_view_level)
                        if level_key in self.highscores:
                            del self.highscores[level_key]
                            self.save_game_data()
                    elif self.hs_prev_rect.collidepoint(mouse_pos):
                        if self.highscore_view_level > 1:
                            self.highscore_view_level -= 1
                    elif self.hs_next_rect.collidepoint(mouse_pos):
                        if self.highscore_view_level < 50:
                            self.highscore_view_level += 1

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU

            elif self.state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        for ball in self.balls:
                            if ball.attached:
                                ball.attached = False
                                hit_pos = getattr(ball, "sticky_offset_x", 0)
                                relative_hit = max(-1.0, min(1.0, hit_pos / (self.paddle.rect.width / 2)))
                                
                                speed_mult = DIFFICULTY_SETTINGS[self.difficulty]["ball_speed_mult"]
                                BALL_TEMPO = BALL_SPEED * speed_mult
                                if abs(relative_hit) < 0.1:
                                    relative_hit = random.choice([-0.15, 0.15])
                                
                                ball.speed_x = relative_hit * (BALL_TEMPO * 0.8)
                                ball.speed_y = -math.sqrt(max(1.0, BALL_TEMPO**2 - ball.speed_x**2))

                        if "laser_paddle" in self.active_effects:
                            l1 = LaserProjectile(self.paddle.rect.left + 8, self.paddle.rect.top - 6)
                            l2 = LaserProjectile(self.paddle.rect.right - 8, self.paddle.rect.top - 6)
                            self.lasers.add(l1, l2)
                            self.all_sprites.add(l1, l2)
                    
                    elif event.key == pygame.K_p:
                        self.state = STATE_PAUSED

            elif self.state == STATE_PAUSED:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.state = STATE_PLAYING

            elif self.state in (STATE_LEVEL_CLEARED, STATE_ALL_CLEARED):
                if self.qualifies_for_highscores and not self.is_score_saved:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.player_name.strip():
                                level_key = get_level_name(self.current_level_num)
                                if level_key not in self.highscores:
                                    self.highscores[level_key] = []
                                self.highscores[level_key].append({
                                    "name": self.player_name.strip(),
                                    "score": self.final_score
                                })
                                self.highscores[level_key].sort(key=lambda x: x["score"], reverse=True)
                                self.highscores[level_key] = self.highscores[level_key][:5]
                                self.save_game_data()
                                self.is_score_saved = True
                        elif event.key == pygame.K_BACKSPACE:
                            self.player_name = self.player_name[:-1]
                        else:
                            if len(self.player_name) < 15 and event.unicode.isprintable() and event.unicode.strip():
                                self.player_name += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.menu_btn_rect.collidepoint(mouse_pos):
                        self.state = STATE_MENU
                        pygame.display.set_caption(TITLE)
                    elif hasattr(self, 'next_btn_rect') and self.next_btn_rect and self.next_btn_rect.collidepoint(mouse_pos):
                        next_level = self.current_level_num + 1
                        if os.path.exists(os.path.join("levels", get_level_name(next_level))):
                            self.current_level_num = next_level
                            self.start_game()
                        else:
                            self.state = STATE_ALL_CLEARED
                    
            elif self.state == STATE_EDITOR:
                self.editor.handle_event(event) 
                
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
                    pygame.display.set_caption(TITLE)

    def update(self):
        if self.state == STATE_PLAYING:
            self.check_timers()
            self.particles.update()
            
            # Magnet effect
            if "magnet" in self.active_effects:
                for ball in self.balls:
                    if not ball.attached:
                        if ball.rect.centerx < self.paddle.rect.centerx:
                            ball.speed_x += 0.1
                        elif ball.rect.centerx > self.paddle.rect.centerx:
                            ball.speed_x -= 0.1
                for p_up in self.powerups:
                    if p_up.rect.centerx < self.paddle.rect.centerx:
                        p_up.rect.x += 1
                    elif p_up.rect.centerx > self.paddle.rect.centerx:
                        p_up.rect.x -= 1
            
            for ball in self.balls:
                if ball.attached:
                    offset = getattr(ball, "sticky_offset_x", 0)
                    ball.rect.centerx = self.paddle.rect.centerx + offset
                    ball.rect.bottom = self.paddle.rect.top
                    ball.x = float(ball.rect.x)
                    ball.y = float(ball.rect.y)

            self.paddle.update()
            self.powerups.update()
            self.blocks.update()
            self.lasers.update()
            self.balls.update(self.time_factor)

            # --- LASER-KOLLISIONEN ---
            for laser in list(self.lasers):
                hit_blocks = pygame.sprite.spritecollide(laser, self.blocks, False)
                if hit_blocks:
                    laser.kill()
                    for block in hit_blocks:
                        destroyed = block.hit(force_destroy=True)
                        if destroyed:
                            block.kill()
                            if getattr(block, 'is_explosive', False) or block.block_type == 'B':
                                self.trigger_explosion(block)
                            else:
                                self.spawn_powerup(block.rect.x, block.rect.y, guaranteed_type='P' if (block.is_powerup or block.block_type == 'P') else None)
            
            for ball in list(self.balls):
                # --- PADDLE-KOLLISION ---
                if pygame.sprite.collide_rect(ball, self.paddle) and ball.speed_y > 0:
                    self.paddle_hits_count += 1
                    if self.paddle_sticky:
                        ball.attached = True
                        ball.sticky_offset_x = ball.rect.centerx - self.paddle.rect.centerx
                        ball.rect.bottom = self.paddle.rect.top
                        ball.x = float(ball.rect.x)
                        ball.y = float(ball.rect.y)
                    else:
                        hit_pos = ball.rect.centerx - self.paddle.rect.centerx
                        relative_hit = max(-1.0, min(1.0, hit_pos / (self.paddle.rect.width / 2)))
                        
                        if abs(relative_hit) < 0.1:
                            relative_hit = random.choice([-0.15, 0.15])
                        
                        speed_mult = DIFFICULTY_SETTINGS[self.difficulty]["ball_speed_mult"]
                        BALL_TEMPO = BALL_SPEED * speed_mult
                        ball.speed_x = relative_hit * (BALL_TEMPO * 0.8)
                        ball.speed_y = -math.sqrt(max(1.0, BALL_TEMPO**2 - ball.speed_x**2))

                # --- SECURE BORDER KOLLISION ---
                if pygame.sprite.spritecollide(ball, self.secure_borders, False) and ball.speed_y > 0:
                    ball.speed_y *= -1
                    self.spawn_particles(ball.rect.centerx, ball.rect.bottom, CYAN, count=8)

                # --- BLOCK-KOLLISION ---
                hit_blocks = pygame.sprite.spritecollide(ball, self.blocks, False)
                if hit_blocks:
                    for block in hit_blocks:
                        if block.block_type == 'T':
                            self.handle_portal_teleport(ball, block)
                            if not getattr(ball, 'is_fireball', False) and not getattr(ball, 'is_piercing', False):
                                ball.speed_y *= -1
                        else:
                            force = getattr(ball, 'is_fireball', False) or getattr(ball, 'is_piercing', False)
                            if not getattr(ball, 'is_piercing', False) and not getattr(ball, 'is_fireball', False) and not block.is_unbreakable:
                                ball.speed_y *= -1
                            elif block.is_unbreakable and not force:
                                ball.speed_y *= -1

                            self.spawn_particles(block.rect.centerx, block.rect.centery, YELLOW if block.health==1 else ORANGE, count=8)
                            destroyed = block.hit(force_destroy=force)
                            if destroyed:
                                block.kill()
                                if getattr(block, 'is_explosive', False) or block.block_type == 'B':
                                    self.trigger_explosion(block)
                                elif getattr(block, 'is_powerdown', False) or block.block_type == 'D':
                                    self.spawn_powerup(block.rect.x, block.rect.y, guaranteed_type='D')
                                else:
                                    self.spawn_powerup(block.rect.x, block.rect.y, guaranteed_type='P' if (block.is_powerup or block.block_type == 'P') else None)

                # Aus-dem-Spiel- & Schutznetz-Prüfung
                sw, sh = self.screen.get_width(), self.screen.get_height()
                if ball.rect.bottom >= sh - 15:
                    if self.safety_net and self.safety_net.alive():
                        ball.rect.bottom = self.safety_net.rect.top
                        ball.y = float(ball.rect.y)
                        ball.speed_y = -abs(ball.speed_y)
                        self.safety_net.kill()
                        self.safety_net = None
                        if "safety_net" in self.active_effects:
                            del self.active_effects["safety_net"]
                    elif ball.rect.top > sh:
                        ball.kill()

            collected_powerups = pygame.sprite.spritecollide(cast(Any, self.paddle), self.powerups, True)
            for p_up in collected_powerups:
                self.apply_powerup(p_up)

            if len(self.balls) == 0:
                self.state = STATE_MENU
                pygame.display.set_caption(TITLE)

            # --- WIN CONDITION: Mandatory Bricks Cleared ---
            mandatory_remaining = [b for b in self.blocks if not b.is_unbreakable and not getattr(b, 'is_powerdown', False)]
            if len(mandatory_remaining) == 0:
                elapsed_ms = pygame.time.get_ticks() - self.level_start_ticks
                self.elapsed_seconds_at_win = elapsed_ms / 1000.0
                self.final_score = self.calculate_score(self.elapsed_seconds_at_win)
                
                next_level = self.current_level_num + 1
                if next_level > self.unlocked_level:
                    self.unlocked_level = next_level
                    self.save_game_data()
                
                level_key = get_level_name(self.current_level_num)
                level_scores = self.highscores.get(level_key, [])
                if len(level_scores) < 5 or self.final_score > level_scores[-1]["score"]:
                    self.qualifies_for_highscores = True
                else:
                    self.qualifies_for_highscores = False
                
                if os.path.exists(os.path.join("levels", get_level_name(next_level))):
                    self.state = STATE_LEVEL_CLEARED
                else:
                    self.state = STATE_ALL_CLEARED
                
        elif self.state in (STATE_LEVEL_CLEARED, STATE_ALL_CLEARED):
            self.particles.update()
            now = pygame.time.get_ticks()
            if now - self.fireworks_timer > 300:
                self.fireworks_timer = now
                sw, sh = self.screen.get_width(), self.screen.get_height()
                fx = random.randint(100, sw - 100)
                fy = random.randint(80, min(300, sh // 2))
                fcolor = random.choice([YELLOW, CYAN, RED, GREEN, MAGENTA])
                self.spawn_particles(fx, fy, fcolor, count=30)
                
        elif self.state == STATE_EDITOR:
            self.editor.update()

    def draw_background(self):
        self.screen.fill(BLACK)
        sw, sh = self.screen.get_width(), self.screen.get_height()
        for star in self.bg_stars:
            star[1] += star[2]
            if star[1] > sh:
                star[1] = 0
                star[0] = random.randint(0, sw)
            pygame.draw.circle(self.screen, (100, 120, 150), (int(star[0]), int(star[1])), max(1, int(star[2])))

    def draw(self):
        self.draw_background()
        sw, sh = self.screen.get_width(), self.screen.get_height()
        
        if self.state in (STATE_PLAYING, STATE_PAUSED):
            self.all_sprites.draw(self.screen)
            
            if "laser_paddle" in self.active_effects:
                pygame.draw.rect(self.screen, RED, (self.paddle.rect.left + 4, self.paddle.rect.top - 6, 6, 8))
                pygame.draw.rect(self.screen, RED, (self.paddle.rect.right - 10, self.paddle.rect.top - 6, 6, 8))
            
            font_hud = pygame.font.SysFont(None, 24)
            live_score = self.calculate_current_score()
            score_txt = font_hud.render(f"Score: {live_score}", True, YELLOW)
            diff_txt = font_hud.render(f"Diff: {DIFFICULTY_SETTINGS[self.difficulty]['label']}", True, CYAN)
            self.screen.blit(score_txt, (sw - 140, 15))
            self.screen.blit(diff_txt, (20, 15))
            
            now = pygame.time.get_ticks()
            active_labels = []
            for etype, expire in list(self.active_effects.items()):
                rem = expire - now
                if rem <= 2000 and (now // 200) % 2 == 0:
                    continue
                active_labels.append(etype.replace("_", " ").title())
            
            if active_labels:
                eff_surf = font_hud.render(f"Effekte: {', '.join(active_labels)}", True, GREEN)
                self.screen.blit(eff_surf, (20, sh - 25))
        
        if self.state == STATE_PAUSED:
            font = pygame.font.SysFont(None, 60, bold=True)
            text_surf = font.render("SPIEL PAUSIERT", True, WHITE)
            text_rect = text_surf.get_rect(center=(sw // 2, sh // 2))
            
            sub_font = pygame.font.SysFont(None, 24)
            sub_surf = sub_font.render("Drücke 'P' oder 'ESC' zum Weiterspielen", True, (200, 200, 200))
            sub_rect = sub_surf.get_rect(center=(sw // 2, (sh // 2) + 50))
            
            self.screen.blit(text_surf, text_rect)
            self.screen.blit(sub_surf, sub_rect)
            
        elif self.state in (STATE_LEVEL_CLEARED, STATE_ALL_CLEARED):
            self.particles.draw(self.screen)
            
            title_font = pygame.font.SysFont(None, 46, bold=True)
            if self.state == STATE_ALL_CLEARED:
                title_surf = title_font.render("GLÜCKWUNSCH! ALLE LEVEL MEISTERHAFT CLEARED!", True, YELLOW)
            else:
                title_surf = title_font.render(f"LEVEL {self.current_level_num} GESCHAFFT!", True, GREEN)
            self.screen.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, 40))
            
            stat_font = pygame.font.SysFont(None, 24)
            elapsed_time = int(self.elapsed_seconds_at_win)
            
            stats = [
                f"Benötigte Zeit: {elapsed_time} Sekunden",
                f"Paddle-Kontakte: {self.paddle_hits_count}",
                f"Gesammelte Power-Ups: {self.powerups_collected_count}",
                f"FINALER SCORE: {self.final_score}"
            ]
            
            for idx, text in enumerate(stats):
                color = YELLOW if idx == 3 else WHITE
                surf = stat_font.render(text, True, color)
                self.screen.blit(surf, (sw // 2 - 150, 110 + idx * 28))
                
            hs_font = pygame.font.SysFont(None, 26, bold=True)
            hs_title = hs_font.render(f"--- Top 5 Highscores (Level {self.current_level_num}) ---", True, ORANGE)
            self.screen.blit(hs_title, (sw // 2 - hs_title.get_width() // 2, 230))
            
            level_key = get_level_name(self.current_level_num)
            level_scores = self.highscores.get(level_key, [])
            
            row_font = pygame.font.SysFont(None, 22)
            if not level_scores:
                no_hs = row_font.render("Noch keine Highscores vorhanden.", True, (180, 180, 180))
                self.screen.blit(no_hs, (sw // 2 - no_hs.get_width() // 2, 265))
            else:
                for idx, entry in enumerate(level_scores):
                    row_txt = row_font.render(f"{idx + 1}. {entry['name']} - {entry['score']} Punkte", True, WHITE)
                    self.screen.blit(row_txt, (sw // 2 - 120, 265 + idx * 25))

            offset_y = 400
            if self.qualifies_for_highscores and not self.is_score_saved:
                prompt_surf = row_font.render("Neuer Highscore! Gib deinen Namen ein und drücke ENTER:", True, YELLOW)
                self.screen.blit(prompt_surf, (sw // 2 - prompt_surf.get_width() // 2, offset_y))
                
                input_rect = pygame.Rect(sw // 2 - 150, offset_y + 30, 300, 35)
                pygame.draw.rect(self.screen, (60, 60, 60), input_rect, border_radius=6)
                pygame.draw.rect(self.screen, WHITE, input_rect, width=2, border_radius=6)
                
                name_surf = row_font.render(self.player_name + "_", True, WHITE)
                self.screen.blit(name_surf, (input_rect.x + 10, input_rect.centery - name_surf.get_height() // 2))
                offset_y += 80
            elif self.qualifies_for_highscores and self.is_score_saved:
                saved_surf = row_font.render("Highscore erfolgreich gespeichert!", True, GREEN)
                self.screen.blit(saved_surf, (sw // 2 - saved_surf.get_width() // 2, offset_y))
                offset_y += 80

            self.menu_btn_rect = pygame.Rect(sw // 2 - 210, sh - 70, 190, 45)
            pygame.draw.rect(self.screen, (70, 70, 70), self.menu_btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, WHITE, self.menu_btn_rect, width=2, border_radius=8)
            menu_txt = row_font.render("Hauptmenü", True, WHITE)
            self.screen.blit(menu_txt, (self.menu_btn_rect.centerx - menu_txt.get_width() // 2, self.menu_btn_rect.centery - menu_txt.get_height() // 2))
            
            next_level = self.current_level_num + 1
            if os.path.exists(os.path.join("levels", get_level_name(next_level))):
                self.next_btn_rect = pygame.Rect(sw // 2 + 20, sh - 70, 190, 45)
                pygame.draw.rect(self.screen, (50, 150, 50), self.next_btn_rect, border_radius=8)
                pygame.draw.rect(self.screen, WHITE, self.next_btn_rect, width=2, border_radius=8)
                next_txt = row_font.render("Nächstes Level", True, WHITE)
                self.screen.blit(next_txt, (self.next_btn_rect.centerx - next_txt.get_width() // 2, self.next_btn_rect.centery - next_txt.get_height() // 2))
            else:
                self.next_btn_rect = None

        elif self.state == STATE_MENU:
            self.menu.draw(self.screen, self.unlocked_level, self.is_fullscreen)

        elif self.state == STATE_HIGHSCORE:
            title_font = pygame.font.SysFont(None, 45, bold=True)
            title_surf = title_font.render("HIGHSCORE-BESTENLISTE", True, YELLOW)
            self.screen.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, 40))

            ctrl_font = pygame.font.SysFont(None, 24, bold=True)
            
            pygame.draw.rect(self.screen, (70, 70, 70), self.hs_prev_rect, border_radius=5)
            pygame.draw.rect(self.screen, (70, 70, 70), self.hs_next_rect, border_radius=5)
            
            prev_txt = ctrl_font.render("<", True, WHITE)
            next_txt = ctrl_font.render(">", True, WHITE)
            self.screen.blit(prev_txt, (self.hs_prev_rect.centerx - prev_txt.get_width() // 2, self.hs_prev_rect.centery - prev_txt.get_height() // 2))
            self.screen.blit(next_txt, (self.hs_next_rect.centerx - next_txt.get_width() // 2, self.hs_next_rect.centery - next_txt.get_height() // 2))

            lvl_label = ctrl_font.render(f"Level {self.highscore_view_level}", True, WHITE)
            self.screen.blit(lvl_label, (sw // 2 - lvl_label.get_width() // 2, 118))

            level_key = get_level_name(self.highscore_view_level)
            level_scores = self.highscores.get(level_key, [])
            
            row_font = pygame.font.SysFont(None, 24)
            if not level_scores:
                no_scores_surf = row_font.render("Noch keine Einträge für dieses Level.", True, (180, 180, 180))
                self.screen.blit(no_scores_surf, (sw // 2 - no_scores_surf.get_width() // 2, 220))
            else:
                for idx, entry in enumerate(level_scores):
                    row_txt = row_font.render(f"{idx + 1}. {entry['name']} - {entry['score']} Punkte", True, WHITE)
                    self.screen.blit(row_txt, (sw // 2 - 130, 180 + idx * 35))

            pygame.draw.rect(self.screen, (150, 40, 40), self.hs_delete_rect, border_radius=8)
            pygame.draw.rect(self.screen, WHITE, self.hs_delete_rect, width=2, border_radius=8)
            del_txt = row_font.render("Highscores löschen", True, WHITE)
            self.screen.blit(del_txt, (self.hs_delete_rect.centerx - del_txt.get_width() // 2, self.hs_delete_rect.centery - del_txt.get_height() // 2))

            pygame.draw.rect(self.screen, (70, 70, 70), self.hs_back_rect, border_radius=8)
            pygame.draw.rect(self.screen, WHITE, self.hs_back_rect, width=2, border_radius=8)
            back_txt = row_font.render("Zurück", True, WHITE)
            self.screen.blit(back_txt, (self.hs_back_rect.centerx - back_txt.get_width() // 2, self.hs_back_rect.centery - back_txt.get_height() // 2))

        elif self.state == STATE_LEVEL_SELECT:
            self.level_selection_menu.draw(self.unlocked_level)
        elif self.state == STATE_EDITOR:
            self.editor.draw()
            
        pygame.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)