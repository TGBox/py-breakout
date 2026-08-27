import math
import pygame
import os
import json
import random
from typing import Any, cast
from settings import *
from level_manager import LevelManager
from sprites import Paddle, Ball, PowerUp, Block, Particle, SecureBorder, SafetyNet, LaserProjectile, HomingMissile, ShieldOrb, Boss, BossProjectile, FloatingText
from menu import LevelSelectionMenu, MainMenu, SettingsMenu
from editor import LevelEditor
from sound_manager import SoundManager

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
        self.previous_state = STATE_MENU
        
        # UI Auswahl-Indizes für Controller
        self.pause_selected_idx = 0
        self.win_selected_idx = 0
        self.hs_selected_idx = 0
        self.last_ctrl_move_ticks = 0

        # Controller / Gamepad Unterstützung
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        self.joysticks: list[Any] = []
        self.init_joysticks()

        # Audio Manager
        self.sound_manager = SoundManager()
        
        # Level-Verwaltung
        self.level_manager = LevelManager()
        self.current_level_num = 1
        self.unlocked_level = 1
        self.difficulty = DIFFICULTY_NORMAL
        self.highscores: dict[str, list[dict[str, Any]]] = {}
        
        # Unified Save & Load
        self.load_game_data()
        self.highscore_view_level = 1
        
        # Highscore-Rechtecke & Pause-Buttons für Klicks definieren
        self.update_highscore_rects()
        
        # Scoring-Metriken & Zeitmessung & Combo-System
        self.level_start_ticks = 0
        self.effective_elapsed_seconds = 0.0
        self.last_frame_ticks = 0
        self.elapsed_seconds_at_win = 0.0
        self.paddle_hits_count = 0
        self.powerups_collected_count = 0
        self.score_multiplier = 1.0
        self.final_score = 0
        self.qualifies_for_highscores = False
        self.is_score_saved = False
        self.player_name = ""
        
        self.combo_counter = 0
        self.last_hit_ticks = 0
        
        # Screen-Shake State
        self.shake_amount: float = 0.0
        self.shake_until_ticks: int = 0
        
        # Menü, Settings & Editor
        self.menu = MainMenu()
        self.menu.set_difficulty_label(self.difficulty)
        self.level_selection_menu = LevelSelectionMenu(self.screen)
        self.settings_menu = SettingsMenu(self.screen)
        self.editor = LevelEditor(self.screen)
        
        # Sprite-Gruppen
        self.all_sprites: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.blocks: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.powerups: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.balls: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.lasers: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.missiles: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.shield_orbs: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.particles: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.secure_borders: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.bosses: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.boss_projectiles: pygame.sprite.Group[Any] = pygame.sprite.Group()
        self.floating_texts: pygame.sprite.Group[Any] = pygame.sprite.Group()
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

    def init_joysticks(self):
        """Erkennt und initialisiert angeschlossene Gamepads / Controller."""
        self.joysticks.clear()
        if pygame.joystick.get_init():
            for i in range(pygame.joystick.get_count()):
                try:
                    js = pygame.joystick.Joystick(i)
                    js.init()
                    self.joysticks.append(js)
                    print(f"[Controller] Gamepad erkannt: {js.get_name()}")
                except Exception as e:
                    print(f"[Controller] Fehler beim Initialisieren: {e}")

    def add_screen_shake(self, intensity: float, duration_ms: int = 250):
        self.shake_amount = max(self.shake_amount, intensity)
        self.shake_until_ticks = pygame.time.get_ticks() + duration_ms

    def spawn_floating_text(self, x: float, y: float, text: str, color: tuple[int, int, int] = WHITE, font_size: int = 22):
        ft = FloatingText(x, y, text, color=color, font_size=font_size)
        self.floating_texts.add(ft)

    def register_hit_combo(self, x: float, y: float, base_pts: int = 100) -> int:
        now = pygame.time.get_ticks()
        if now - self.last_hit_ticks <= 1250:
            self.combo_counter += 1
        else:
            self.combo_counter = 1
        self.last_hit_ticks = now

        multiplier = min(5, self.combo_counter)
        if self.combo_counter >= 2:
            color = GREEN if multiplier == 2 else (CYAN if multiplier == 3 else (ORANGE if multiplier == 4 else MAGENTA))
            self.spawn_floating_text(x, y - 15, f"{multiplier}x COMBO!", color, font_size=24)
            if self.combo_counter >= 3:
                self.sound_manager.play_sound("combo_up")
        return base_pts * multiplier

    def load_game_data(self):
        """Lädt Spieldaten und Audio-Einstellungen aus game_data.json."""
        if os.path.exists("game_data.json"):
            try:
                with open("game_data.json", "r") as file:
                    data = json.load(file)
                    self.unlocked_level = data.get("unlocked_level", 1)
                    self.difficulty = data.get("difficulty", DIFFICULTY_NORMAL)
                    self.highscores = data.get("highscores", {})
                    
                    self.sound_manager.muted = data.get("sound_muted", False)
                    self.sound_manager.sfx_volume = data.get("sfx_volume", 0.8)
                    self.sound_manager.music_volume = data.get("music_volume", 0.5)
                    self.sound_manager.update_volumes()

                print(f"[Load] game_data.json geladen. Fortschritt: Level {self.unlocked_level}")
                return
            except Exception as e:
                print(f"[Load-Fehler] game_data.json beschädigt: {e}")

        self.save_game_data()

    def save_game_data(self):
        """Speichert Fortschritt, Highscores und Audio-Einstellungen in game_data.json."""
        data = {
            "unlocked_level": self.unlocked_level,
            "difficulty": self.difficulty,
            "highscores": self.highscores,
            "sound_muted": self.sound_manager.muted,
            "sfx_volume": self.sound_manager.sfx_volume,
            "music_volume": self.sound_manager.music_volume
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
        self.missiles.empty()
        self.shield_orbs.empty()
        self.particles.empty()
        self.secure_borders.empty()
        self.bosses.empty()
        self.boss_projectiles.empty()
        self.floating_texts.empty()
        if self.safety_net:
            self.safety_net.kill()
            self.safety_net = None

        self.active_effects.clear()
        self.time_factor = 1.0
        self.score_multiplier = 1.0
        self.shake_amount = 0.0
        self.combo_counter = 0
        self.last_hit_ticks = 0
        
        self.level_start_ticks = pygame.time.get_ticks()
        self.last_frame_ticks = pygame.time.get_ticks()
        self.effective_elapsed_seconds = 0.0
        self.elapsed_seconds_at_win = 0.0
        self.paddle_hits_count = 0
        self.powerups_collected_count = 0
        self.is_score_saved = False
        self.player_name = ""
        
        pygame.display.set_caption(f"{TITLE} - Level {self.current_level_num} ({DIFFICULTY_SETTINGS[self.difficulty]['label']})")
        
        level_file = get_level_name(self.current_level_num)
        sw, sh = self.screen.get_width(), self.screen.get_height()
        self.blocks, boss = self.level_manager.load_level(level_file, sw, sh, level_num=self.current_level_num)
        
        if boss:
            self.bosses.add(boss)
            self.all_sprites.add(boss)
            # Shield Boss Orbs erzeugen bei Level 5 oder 15
            if self.current_level_num in (5, 15):
                orb1 = ShieldOrb(boss, 0.0)
                orb2 = ShieldOrb(boss, math.pi)
                self.shield_orbs.add(orb1, orb2)
                self.all_sprites.add(orb1, orb2)

        if len(self.blocks) == 0 and not boss:
            self.state = STATE_MENU
            return

        self.reset_paddle()
        self.paddle_sticky = False
        
        diff_settings = DIFFICULTY_SETTINGS[self.difficulty]
        base_ball_speed = BALL_SPEED * float(diff_settings["ball_speed_mult"])
        
        start_ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - 8, speed_x=0, speed_y=-base_ball_speed)
        start_ball.attached = True
        self.balls.add(start_ball)
        
        self.all_sprites.add(self.paddle, self.balls, self.blocks)
        self.state = STATE_PLAYING
        
        # Retro Chiptune BGM starten
        self.sound_manager.play_bgm()

    def reset_paddle(self):
        sw, sh = self.screen.get_width(), self.screen.get_height()
        pos = self.paddle.rect.center if hasattr(self.paddle, 'rect') else (sw // 2, sh - 30)
        self.paddle.image = pygame.Surface((100, 15))
        self.paddle.image.fill(WHITE)
        self.paddle.rect = self.paddle.image.get_rect(centerx=pos[0], bottom=sh - 30)
        self.paddle.inverted_controls = False
        self.paddle.laser_ammo = 0
        self.paddle.missile_ammo = 0
        self.paddle.shield_active = False

    POSITIVE_EFFECTS = ["sticky_paddle", "expand_paddle", "slow_time",
                        "bigger_ball", "multiball", "piercing_shot",
                        "laser_paddle", "missile_paddle", "shield_aura",
                        "safety_net", "secure_border",
                        "magnet", "score_boost", "fireball"]
    NEGATIVE_EFFECTS = ["shrink_paddle", "speed_time", "smaller_ball",
                        "score_drain", "inverted_controls"]

    def spawn_powerup(self, x: int, y: int, guaranteed_type: str | None = None):
        diff_cfg = DIFFICULTY_SETTINGS[self.difficulty]
        spawn_chance: float = 1.0 if guaranteed_type else float(diff_cfg["powerup_chance"])
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
        duration = int(8000 * float(diff_cfg["timer_mult"]))
        etype = powerup.effect_type
        
        is_positive = etype in self.POSITIVE_EFFECTS
        sound_name = "powerup" if is_positive else "powerdown"
        self.sound_manager.play_sound(sound_name)

        color = GREEN if is_positive else RED
        self.spawn_floating_text(self.paddle.rect.centerx, self.paddle.rect.top - 10, etype.replace('_', ' ').upper(), color, font_size=24)

        if etype == "sticky_paddle":
            self.paddle_sticky = True
            current_width = self.paddle.rect.width
            self.paddle.image = pygame.Surface((current_width, 15))
            self.paddle.image.fill(YELLOW)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            self.active_effects["sticky_paddle"] = now + duration
            
        elif etype == "expand_paddle":
            self.paddle.image = pygame.Surface((150, 15))
            color_pad = YELLOW if self.paddle_sticky else GREEN
            self.paddle.image.fill(color_pad)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            self.active_effects["paddle_size"] = now + duration
            
        elif etype == "shrink_paddle":
            self.paddle.image = pygame.Surface((60, 15))
            color_pad = YELLOW if self.paddle_sticky else RED
            self.paddle.image.fill(color_pad)
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
            self.paddle.laser_ammo = 12  # Nerf: 12 Schuss
            self.active_effects["laser_paddle"] = now + duration
            
        elif etype == "missile_paddle":
            self.paddle.missile_ammo = 6  # 6 Zielsuchraketen
            self.active_effects["missile_paddle"] = now + duration

        elif etype == "shield_aura":
            self.paddle.shield_active = True
            self.active_effects["shield_aura"] = now + duration
            
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

        if "shield_aura" in self.active_effects and now > self.active_effects["shield_aura"]:
            self.paddle.shield_active = False
            del self.active_effects["shield_aura"]

    def trigger_explosion(self, origin_block: Block):
        origin_block.kill()
        center_x = origin_block.rect.centerx
        center_y = origin_block.rect.centery
        self.spawn_particles(center_x, center_y, ORANGE, count=25)
        self.spawn_particles(center_x, center_y, RED, count=15)
        self.add_screen_shake(6.0, 300)
        self.spawn_floating_text(center_x, center_y, "BOOM!", RED, font_size=26)
        self.sound_manager.play_sound("explosion")
        
        radius_x = origin_block.width * 1.6
        radius_y = origin_block.height * 1.6

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
            self.sound_manager.play_sound("laser")

    def launch_ball_or_laser(self):
        """Startet klebende Bälle, feuert Laser-Kanonen (mit Nerf/Ammo) oder Homing Missiles."""
        now = pygame.time.get_ticks()
        for ball in self.balls:
            if ball.attached:
                ball.attached = False
                hit_pos = getattr(ball, "sticky_offset_x", 0)
                relative_hit = max(-1.0, min(1.0, hit_pos / (self.paddle.rect.width / 2)))
                
                speed_mult = float(DIFFICULTY_SETTINGS[self.difficulty]["ball_speed_mult"])
                BALL_TEMPO = BALL_SPEED * speed_mult
                if abs(relative_hit) < 0.1:
                    relative_hit = random.choice([-0.15, 0.15])
                
                ball.speed_x = relative_hit * (BALL_TEMPO * 0.8)
                ball.speed_y = -math.sqrt(max(1.0, BALL_TEMPO**2 - ball.speed_x**2))
                self.sound_manager.play_sound("paddle_hit")

        # --- LASER NERF: 300ms Cooldown & Munitionsabzug ---
        if "laser_paddle" in self.active_effects and self.paddle.laser_ammo > 0:
            if now - self.paddle.last_shot_ticks >= 300:
                self.paddle.last_shot_ticks = now
                self.paddle.laser_ammo -= 1
                l1 = LaserProjectile(self.paddle.rect.left + 8, self.paddle.rect.top - 6)
                l2 = LaserProjectile(self.paddle.rect.right - 8, self.paddle.rect.top - 6)
                self.lasers.add(l1, l2)
                self.all_sprites.add(l1, l2)
                self.sound_manager.play_sound("laser")
                if self.paddle.laser_ammo <= 0:
                    del self.active_effects["laser_paddle"]

        # --- HOMING MISSILE LAUNCHER ---
        if "missile_paddle" in self.active_effects and self.paddle.missile_ammo > 0:
            if now - self.paddle.last_shot_ticks >= 300:
                self.paddle.last_shot_ticks = now
                self.paddle.missile_ammo -= 1
                m = HomingMissile(self.paddle.rect.centerx, self.paddle.rect.top - 6)
                self.missiles.add(m)
                self.all_sprites.add(m)
                self.sound_manager.play_sound("missile_launch")
                if self.paddle.missile_ammo <= 0:
                    del self.active_effects["missile_paddle"]

    def calculate_score(self, elapsed_seconds: float | None = None) -> int:
        base_score = 10000
        seconds = self.effective_elapsed_seconds if elapsed_seconds is None else elapsed_seconds
        time_penalty = int(seconds * 10)
        hit_penalty = self.paddle_hits_count * 20
        powerup_penalty = self.powerups_collected_count * 100
        
        score = (base_score - time_penalty - hit_penalty - powerup_penalty) * self.score_multiplier
        return max(0, int(score))

    def calculate_current_score(self) -> int:
        return self.calculate_score()

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
        self.settings_menu.screen = self.screen
        self.update_highscore_rects()
        
        self.bg_stars = [
            [random.randint(0, sw), random.randint(0, sh), random.uniform(0.2, 1.2)]
            for _ in range(50)
        ]
        
        if self.state == STATE_PLAYING:
            self.paddle.rect.bottom = sh - 30
            
            for block in self.blocks:
                if hasattr(block, 'reposition_and_rescale'):
                    block.reposition_and_rescale(sw, sh)

            for boss in self.bosses:
                if hasattr(boss, 'reposition_and_rescale'):
                    boss.reposition_and_rescale(sw, sh)
                    
            if self.safety_net and self.safety_net.alive():
                self.safety_net.image = pygame.Surface((sw, 8))
                self.safety_net.image.fill((0, 220, 255))
                pygame.draw.rect(self.safety_net.image, WHITE, (0, 0, sw, 8), 1)
                self.safety_net.rect = self.safety_net.image.get_rect(topleft=(0, sh - 12))
                
            for sb in self.secure_borders:
                sb.image = pygame.Surface((sw, 8))
                sb.image.fill(CYAN)
                pygame.draw.rect(sb.image, WHITE, (0, 0, sw, 8), 1)
                sb.rect = sb.image.get_rect(topleft=(0, sh - 12))

    def update_highscore_rects(self):
        sw, sh = self.screen.get_width(), self.screen.get_height()
        self.hs_prev_rect = pygame.Rect(sw // 2 - 140, 110, 40, 35)
        self.hs_next_rect = pygame.Rect(sw // 2 + 100, 110, 40, 35)
        self.hs_delete_rect = pygame.Rect(sw // 2 - 210, sh - 80, 200, 45)
        self.hs_back_rect = pygame.Rect(sw // 2 + 10, sh - 80, 200, 45)
        
        # Pause-Buttons
        self.pause_resume_rect = pygame.Rect(sw // 2 - 180, sh // 2 + 15, 110, 40)
        self.pause_opts_rect = pygame.Rect(sw // 2 - 55, sh // 2 + 15, 110, 40)
        self.pause_menu_rect = pygame.Rect(sw // 2 + 70, sh // 2 + 15, 110, 40)

    def trigger_menu_action(self, action: str | int | None):
        if not action:
            return
            
        if action == "PLAY":
            self.current_level_num = self.unlocked_level
            self.start_game()
            
        elif action == "LEVEL_SELECT":
            self.state = STATE_LEVEL_SELECT
            
        elif action == "SETTINGS":
            self.previous_state = STATE_MENU
            self.state = STATE_SETTINGS
            
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
            
        elif isinstance(action, int):
            self.current_level_num = action
            self.start_game()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.init_joysticks()

            if event.type == pygame.VIDEORESIZE:
                if not self.is_fullscreen:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.on_resize()

            # --- CONTROLLER STEUERKREUZ (D-PAD) NATIVE EVENTS ---
            if event.type == pygame.JOYHATMOTION:
                hx, hy = event.value
                if hx != 0 or hy != 0:
                    self.handle_controller_nav(d_x=hx, d_y=-hy)

            # --- CONTROLLER BUTTON EVENTS ---
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Button A / Cross: Bestätigen / Starten
                    if self.state == STATE_MENU:
                        self.trigger_menu_action(self.menu.get_selected_action())

                    elif self.state == STATE_LEVEL_SELECT:
                        act = self.level_selection_menu.get_selected_action(self.unlocked_level)
                        if act == "BACK":
                            self.state = STATE_MENU
                        elif isinstance(act, int):
                            self.trigger_menu_action(act)

                    elif self.state == STATE_SETTINGS:
                        act = self.settings_menu.trigger_selected_action(self.sound_manager)
                        if act == "BACK":
                            self.save_game_data()
                            self.state = self.previous_state
                        elif act == "TOGGLE_FULLSCREEN":
                            self.toggle_fullscreen()
                            self.save_game_data()

                    elif self.state == STATE_PAUSED:
                        if self.pause_selected_idx == 0:
                            self.state = STATE_PLAYING
                            self.sound_manager.play_bgm()
                        elif self.pause_selected_idx == 1:
                            self.previous_state = STATE_PAUSED
                            self.state = STATE_SETTINGS
                        elif self.pause_selected_idx == 2:
                            self.state = STATE_MENU

                    elif self.state == STATE_PLAYING:
                        self.launch_ball_or_laser()

                    elif self.state == STATE_HIGHSCORE:
                        if self.hs_selected_idx == 0 and self.highscore_view_level > 1:
                            self.highscore_view_level -= 1
                        elif self.hs_selected_idx == 1 and self.highscore_view_level < 50:
                            self.highscore_view_level += 1
                        elif self.hs_selected_idx == 2:
                            level_key = get_level_name(self.highscore_view_level)
                            if level_key in self.highscores:
                                del self.highscores[level_key]
                                self.save_game_data()
                        elif self.hs_selected_idx == 3:
                            self.state = STATE_MENU

                    elif self.state in (STATE_LEVEL_CLEARED, STATE_ALL_CLEARED):
                        if self.win_selected_idx == 0:
                            self.state = STATE_MENU
                            pygame.display.set_caption(TITLE)
                        elif self.win_selected_idx == 1:
                            next_level = self.current_level_num + 1
                            if os.path.exists(os.path.join("levels", get_level_name(next_level))):
                                self.current_level_num = next_level
                                self.start_game()

                    elif self.state == STATE_EDITOR:
                        self.editor.place_at_cursor()

                elif event.button == 1:  # Button B / Circle: Zurück
                    if self.state in (STATE_LEVEL_SELECT, STATE_SETTINGS, STATE_HIGHSCORE, STATE_EDITOR):
                        if self.state == STATE_SETTINGS:
                            self.save_game_data()
                            self.state = self.previous_state
                        else:
                            self.state = STATE_MENU
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_MENU

                elif event.button == 2:  # Button X: Löschen im Editor / Mute im Spiel
                    if self.state == STATE_EDITOR:
                        self.editor.erase_at_cursor()
                    else:
                        muted = self.sound_manager.toggle_mute()
                        status_text = "MUTED" if muted else "AUDIO ON"
                        self.spawn_floating_text(self.screen.get_width() // 2, 50, f"AUDIO: {status_text}", YELLOW, font_size=26)
                        self.save_game_data()

                elif event.button in (3, 4, 5):  # Button Y, LB, RB: Werkzeug wechseln
                    if self.state == STATE_EDITOR:
                        dir_val = -1 if event.button == 4 else 1
                        self.editor.cycle_type(dir_val)

                elif event.button in (6, 7):  # Button Start / Select: Pause
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                        self.sound_manager.stop_bgm()
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING
                        self.sound_manager.play_bgm()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    muted = self.sound_manager.toggle_mute()
                    status_text = "MUTED" if muted else "AUDIO ON"
                    self.spawn_floating_text(self.screen.get_width() // 2, 50, f"AUDIO: {status_text}", YELLOW, font_size=26)
                    self.save_game_data()

                if event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)):
                    self.toggle_fullscreen()
                    continue

            if self.state == STATE_MENU:
                action = self.menu.handle_event(event)
                self.trigger_menu_action(action)

            elif self.state == STATE_SETTINGS:
                act = self.settings_menu.handle_event(event, self.sound_manager)
                if act == "BACK":
                    self.save_game_data()
                    self.state = self.previous_state
                elif act == "TOGGLE_MUTE":
                    self.save_game_data()
                elif act == "TOGGLE_FULLSCREEN":
                    self.toggle_fullscreen()
                    self.save_game_data()

            elif self.state == STATE_LEVEL_SELECT:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    chosen_level = self.level_selection_menu.handle_click(pygame.mouse.get_pos())
                    if chosen_level == "BACK":
                        self.state = STATE_MENU
                    elif chosen_level is not None:
                        self.current_level_num = chosen_level
                        self.start_game()
                
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.level_selection_menu.navigate(0, -1, self.unlocked_level)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.level_selection_menu.navigate(0, 1, self.unlocked_level)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.level_selection_menu.navigate(-1, 0, self.unlocked_level)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.level_selection_menu.navigate(1, 0, self.unlocked_level)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        act = self.level_selection_menu.get_selected_action(self.unlocked_level)
                        if act == "BACK":
                            self.state = STATE_MENU
                        elif isinstance(act, int):
                            self.trigger_menu_action(act)
                    elif event.key == pygame.K_ESCAPE:
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

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.hs_selected_idx = (self.hs_selected_idx - 1) % 4
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.hs_selected_idx = (self.hs_selected_idx + 1) % 4
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

            elif self.state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        self.launch_ball_or_laser()
                    elif event.key == pygame.K_p:
                        self.state = STATE_PAUSED
                        self.sound_manager.stop_bgm()

            elif self.state == STATE_PAUSED:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mpos = pygame.mouse.get_pos()
                    if self.pause_resume_rect.collidepoint(mpos):
                        self.state = STATE_PLAYING
                        self.last_frame_ticks = pygame.time.get_ticks()
                        self.sound_manager.play_bgm()
                    elif self.pause_opts_rect.collidepoint(mpos):
                        self.previous_state = STATE_PAUSED
                        self.state = STATE_SETTINGS
                    elif self.pause_menu_rect.collidepoint(mpos):
                        self.state = STATE_MENU

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.pause_selected_idx = (self.pause_selected_idx - 1) % 3
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.pause_selected_idx = (self.pause_selected_idx + 1) % 3
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.pause_selected_idx == 0:
                            self.state = STATE_PLAYING
                            self.sound_manager.play_bgm()
                        elif self.pause_selected_idx == 1:
                            self.previous_state = STATE_PAUSED
                            self.state = STATE_SETTINGS
                        elif self.pause_selected_idx == 2:
                            self.state = STATE_MENU
                    elif event.key in (pygame.K_p, pygame.K_SPACE):
                        self.state = STATE_PLAYING
                        self.last_frame_ticks = pygame.time.get_ticks()
                        self.sound_manager.play_bgm()
                    elif event.key == pygame.K_o:
                        self.previous_state = STATE_PAUSED
                        self.state = STATE_SETTINGS
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

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

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                        self.win_selected_idx = 1 - self.win_selected_idx

            elif self.state == STATE_EDITOR:
                self.editor.handle_event(event) 
                
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
                    pygame.display.set_caption(TITLE)

    def handle_controller_nav(self, d_x: int, d_y: int):
        now = pygame.time.get_ticks()
        if now - self.last_ctrl_move_ticks < 150:
            return
        self.last_ctrl_move_ticks = now

        if self.state == STATE_MENU:
            if d_y != 0:
                self.menu.navigate(d_y)
        elif self.state == STATE_LEVEL_SELECT:
            self.level_selection_menu.navigate(d_x, d_y, self.unlocked_level)
        elif self.state == STATE_SETTINGS:
            if d_y != 0:
                self.settings_menu.navigate_row(d_y)
            elif d_x != 0:
                self.settings_menu.adjust_slider(0.05 * d_x, self.sound_manager)
        elif self.state == STATE_PAUSED:
            if d_x != 0 or d_y != 0:
                self.pause_selected_idx = (self.pause_selected_idx + (d_x if d_x != 0 else d_y)) % 3
        elif self.state == STATE_HIGHSCORE:
            if d_x != 0 or d_y != 0:
                self.hs_selected_idx = (self.hs_selected_idx + (d_x if d_x != 0 else d_y)) % 4
        elif self.state in (STATE_LEVEL_CLEARED, STATE_ALL_CLEARED):
            if d_x != 0:
                self.win_selected_idx = 1 - self.win_selected_idx
        elif self.state == STATE_EDITOR:
            self.editor.move_cursor(d_x, d_y)

    def update(self):
        if self.state == STATE_PLAYING:
            sw, sh = self.screen.get_width(), self.screen.get_height()
            
            now = pygame.time.get_ticks()
            dt = (now - self.last_frame_ticks) / 1000.0
            self.last_frame_ticks = now
            self.effective_elapsed_seconds += dt * self.time_factor

            self.check_timers()
            self.particles.update()
            self.floating_texts.update()
            self.shield_orbs.update()
            
            # --- HOMING MISSILE UPDATE ---
            target_obj = None
            if len(self.bosses) > 0:
                target_obj = list(self.bosses)[0]
            elif len(self.blocks) > 0:
                target_obj = list(self.blocks)[0]
                
            t_pos = (target_obj.rect.centerx, target_obj.rect.centery) if target_obj else None
            for m in self.missiles:
                m.update(target_pos=t_pos, screen_height=sh)

            # --- MISSILE KOLLISIONEN ---
            for m in list(self.missiles):
                hit_b = pygame.sprite.spritecollide(m, self.blocks, False)
                if hit_b:
                    m.kill()
                    for block in hit_b:
                        pts = self.register_hit_combo(block.rect.centerx, block.rect.centery, 100)
                        destroyed = block.hit(force_destroy=True)
                        if destroyed:
                            block.kill()
                            self.spawn_particles(block.rect.centerx, block.rect.centery, ORANGE, count=12)
                            self.sound_manager.play_sound("explosion")
                            if getattr(block, 'is_explosive', False) or block.block_type == 'B':
                                self.trigger_explosion(block)

                hit_boss = pygame.sprite.spritecollide(m, self.bosses, False)
                if hit_boss:
                    m.kill()
                    for boss in hit_boss:
                        defeated = boss.hit(2)
                        self.spawn_particles(boss.rect.centerx, boss.rect.centery, ORANGE, count=15)
                        self.add_screen_shake(5.0, 200)
                        self.sound_manager.play_sound("explosion")
                        if defeated:
                            boss.kill()
                            self.add_screen_shake(12.0, 600)
                            self.spawn_particles(boss.rect.centerx, boss.rect.centery, (255, 215, 0), count=40)
                            self.spawn_floating_text(boss.rect.centerx, boss.rect.centery, "BOSS DEFEATED!", (255, 215, 0), font_size=32)

            # --- BOSS UPDATE & GESCHOSSE ---
            for boss in list(self.bosses):
                boss.update(sw)
                if boss.pending_projectile:
                    self.boss_projectiles.add(boss.pending_projectile)
                    self.all_sprites.add(boss.pending_projectile)
                    boss.pending_projectile = None
                    self.sound_manager.play_sound("boss_shoot")
            
            self.boss_projectiles.update(sh)

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

            ctrl_x = 0.0
            for js in self.joysticks:
                try:
                    axis_x = js.get_axis(0)
                    if abs(axis_x) > 0.2:
                        ctrl_x = axis_x
                        break
                    if js.get_numhats() > 0:
                        hat = js.get_hat(0)
                        if hat[0] != 0:
                            ctrl_x = float(hat[0])
                            break
                except Exception:
                    pass

            self.paddle.update(sw, controller_move_x=ctrl_x)
            self.powerups.update(sh)
            self.blocks.update()
            self.lasers.update()
            
            for ball in self.balls:
                if not ball.attached:
                    if ball.rect.left <= 0 or ball.rect.right >= sw or ball.rect.top <= 0:
                        self.sound_manager.play_sound("wall_hit")

            self.balls.update(self.time_factor, sw, sh)

            # --- BOSS-GESCHOSS KOLLISIONEN MIT PADDLE (MIT SCHUTZSCHILD-AURA) ---
            hit_projectiles = pygame.sprite.spritecollide(cast(Any, self.paddle), self.boss_projectiles, True)
            for proj in hit_projectiles:
                if self.paddle.shield_active:
                    self.paddle.shield_active = False
                    self.sound_manager.play_sound("shield_hit")
                    self.spawn_floating_text(self.paddle.rect.centerx, self.paddle.rect.top - 10, "SHIELD ABSORBED!", CYAN)
                else:
                    self.paddle.stun(1500)
                    self.spawn_particles(self.paddle.rect.centerx, self.paddle.rect.top, YELLOW, count=15)
                    self.add_screen_shake(4.0, 200)
                    self.spawn_floating_text(self.paddle.rect.centerx, self.paddle.rect.top - 10, "STUNNED!", RED, font_size=24)
                    self.sound_manager.play_sound("paddle_stun")
                    self.score_multiplier = max(0.5, self.score_multiplier - 0.1)

            pygame.sprite.groupcollide(self.boss_projectiles, self.secure_borders, True, False)
            if self.safety_net and self.safety_net.alive():
                pygame.sprite.spritecollide(self.safety_net, self.boss_projectiles, True)

            # --- LASER-KOLLISIONEN ---
            for laser in list(self.lasers):
                hit_orbs = pygame.sprite.spritecollide(laser, self.shield_orbs, False)
                if hit_orbs:
                    laser.kill()
                    for orb in hit_orbs:
                        orb.hit(1)
                        self.sound_manager.play_sound("wall_hit")

                hit_bosses = pygame.sprite.spritecollide(laser, self.bosses, False)
                if hit_bosses:
                    laser.kill()
                    for boss in hit_bosses:
                        defeated = boss.hit(1)
                        pts = self.register_hit_combo(laser.rect.centerx, laser.rect.top, 250)
                        self.spawn_particles(laser.rect.centerx, laser.rect.top, RED, count=8)
                        self.spawn_floating_text(laser.rect.centerx, laser.rect.top - 5, f"+{pts}", ORANGE)
                        self.sound_manager.play_sound("boss_hit")
                        if defeated:
                            boss.kill()
                            self.add_screen_shake(12.0, 600)
                            self.spawn_particles(boss.rect.centerx, boss.rect.centery, (255, 215, 0), count=40)
                            self.spawn_floating_text(boss.rect.centerx, boss.rect.centery, "BOSS DEFEATED!", (255, 215, 0), font_size=32)
                            self.sound_manager.play_sound("explosion")
                            self.spawn_powerup(boss.rect.centerx, boss.rect.centery, guaranteed_type='P')

                hit_blocks = pygame.sprite.spritecollide(laser, self.blocks, False)
                if hit_blocks:
                    laser.kill()
                    for block in hit_blocks:
                        destroyed = block.hit(force_destroy=True)
                        if destroyed:
                            block.kill()
                            pts = self.register_hit_combo(block.rect.centerx, block.rect.centery, 100)
                            self.spawn_floating_text(block.rect.centerx, block.rect.centery, f"+{pts}", YELLOW)
                            self.sound_manager.play_sound("block_hit")
                            if getattr(block, 'is_explosive', False) or block.block_type == 'B':
                                self.trigger_explosion(block)
                            else:
                                self.spawn_powerup(block.rect.x, block.rect.y, guaranteed_type='P' if (block.is_powerup or block.block_type == 'P') else None)
            
            for ball in list(self.balls):
                # --- BALL KOLLISION MIT SHIELD ORBS ---
                hit_orbs = pygame.sprite.spritecollide(ball, self.shield_orbs, False)
                if hit_orbs:
                    for orb in hit_orbs:
                        ball.speed_y *= -1
                        orb.hit(1)
                        self.sound_manager.play_sound("wall_hit")

                # --- BALL KOLLISION MIT BOSS ---
                hit_bosses = pygame.sprite.spritecollide(ball, self.bosses, False)
                if hit_bosses:
                    for boss in hit_bosses:
                        ball.speed_y *= -1
                        self.spawn_particles(ball.rect.centerx, ball.rect.centery, ORANGE, count=10)
                        self.add_screen_shake(3.0, 150)
                        pts = self.register_hit_combo(ball.rect.centerx, ball.rect.centery, 250)
                        self.spawn_floating_text(ball.rect.centerx, ball.rect.centery, f"+{pts}", ORANGE)
                        self.sound_manager.play_sound("boss_hit")
                        defeated = boss.hit(1)
                        if defeated:
                            boss.kill()
                            self.add_screen_shake(12.0, 600)
                            self.spawn_particles(boss.rect.centerx, boss.rect.centery, (255, 215, 0), count=40)
                            self.spawn_floating_text(boss.rect.centerx, boss.rect.centery, "BOSS DEFEATED!", (255, 215, 0), font_size=32)
                            self.sound_manager.play_sound("explosion")
                            self.spawn_powerup(boss.rect.centerx, boss.rect.centery, guaranteed_type='P')

                # --- PADDLE-KOLLISION ---
                if pygame.sprite.collide_rect(ball, self.paddle) and ball.speed_y > 0:
                    self.paddle_hits_count += 1
                    self.sound_manager.play_sound("paddle_hit")
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
                        
                        speed_mult = float(DIFFICULTY_SETTINGS[self.difficulty]["ball_speed_mult"])
                        BALL_TEMPO = BALL_SPEED * speed_mult
                        ball.speed_x = relative_hit * (BALL_TEMPO * 0.8)
                        ball.speed_y = -math.sqrt(max(1.0, BALL_TEMPO**2 - ball.speed_x**2))

                # --- SECURE BORDER KOLLISION ---
                if pygame.sprite.spritecollide(ball, self.secure_borders, False) and ball.speed_y > 0:
                    ball.speed_y *= -1
                    self.spawn_particles(ball.rect.centerx, ball.rect.bottom, CYAN, count=8)
                    self.sound_manager.play_sound("wall_hit")

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
                            self.sound_manager.play_sound("block_hit")
                            if destroyed:
                                block.kill()
                                base_pts = 100 * block.health if hasattr(block, 'health') else 100
                                pts = self.register_hit_combo(block.rect.centerx, block.rect.centery, base_pts)
                                self.spawn_floating_text(block.rect.centerx, block.rect.centery, f"+{pts}", YELLOW)
                                if getattr(block, 'is_explosive', False) or block.block_type == 'B':
                                    self.trigger_explosion(block)
                                elif getattr(block, 'is_powerdown', False) or block.block_type == 'D':
                                    self.spawn_powerup(block.rect.x, block.rect.y, guaranteed_type='D')
                                else:
                                    self.spawn_powerup(block.rect.x, block.rect.y, guaranteed_type='P' if (block.is_powerup or block.block_type == 'P') else None)

                # Aus-dem-Spiel- & Schutznetz-Prüfung (Mit Schild-Aura Absicherung)
                if ball.rect.bottom >= sh - 15:
                    if self.paddle.shield_active:
                        self.paddle.shield_active = False
                        ball.speed_y = -abs(ball.speed_y)
                        self.sound_manager.play_sound("shield_hit")
                        self.spawn_floating_text(ball.rect.centerx, sh - 40, "SHIELD SAVED BALL!", CYAN)
                    elif self.safety_net and self.safety_net.alive():
                        ball.rect.bottom = self.safety_net.rect.top
                        ball.y = float(ball.rect.y)
                        ball.speed_y = -abs(ball.speed_y)
                        self.safety_net.kill()
                        self.safety_net = None
                        self.sound_manager.play_sound("wall_hit")
                        if "safety_net" in self.active_effects:
                            del self.active_effects["safety_net"]
                    elif ball.rect.top > sh:
                        ball.kill()

            collected_powerups = pygame.sprite.spritecollide(cast(Any, self.paddle), self.powerups, True)
            for p_up in collected_powerups:
                self.apply_powerup(p_up)

            if len(self.balls) == 0:
                self.sound_manager.stop_bgm()
                self.state = STATE_MENU
                pygame.display.set_caption(TITLE)

            # --- WIN CONDITION: Mandatory Bricks Cleared & Boss Defeated ---
            mandatory_remaining = [b for b in self.blocks if not b.is_unbreakable and not getattr(b, 'is_powerdown', False)]
            boss_alive = any(b.alive() for b in self.bosses)

            if len(mandatory_remaining) == 0 and not boss_alive:
                self.sound_manager.stop_bgm()
                self.sound_manager.play_sound("level_win")
                self.elapsed_seconds_at_win = (pygame.time.get_ticks() - self.level_start_ticks) / 1000.0
                self.final_score = self.calculate_score()
                
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
            self.floating_texts.update()
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
        
        # --- SCREEN SHAKE OFFSET BERECHNUNG ---
        offset_x = 0
        offset_y = 0
        now = pygame.time.get_ticks()
        if self.shake_amount > 0 and now < self.shake_until_ticks:
            offset_x = int(random.uniform(-self.shake_amount, self.shake_amount))
            offset_y = int(random.uniform(-self.shake_amount, self.shake_amount))
            self.shake_amount = max(0.0, self.shake_amount * 0.92)
        else:
            self.shake_amount = 0.0

        if self.state in (STATE_PLAYING, STATE_PAUSED):
            # 1. Ball Kometenschweif & Glow vor Sprites rendern
            for ball in self.balls:
                ball.draw_trail_and_glow(self.screen, offset_x, offset_y)

            # 2. Sprites mit Offset rendern
            if offset_x != 0 or offset_y != 0:
                for sprite in self.all_sprites:
                    self.screen.blit(sprite.image, (sprite.rect.x + offset_x, sprite.rect.y + offset_y))
            else:
                self.all_sprites.draw(self.screen)

            # 3. Paddle Munitionsanzeige & Schutzschild rendern
            self.paddle.draw_ammo_and_shield(self.screen)

            # 4. Floating Text Popups rendern
            for ft in self.floating_texts:
                self.screen.blit(ft.image, (ft.rect.x + offset_x, ft.rect.y + offset_y))
            
            font_hud = pygame.font.SysFont(None, 24)
            live_score = self.calculate_current_score()
            score_txt = font_hud.render(f"Score: {live_score}", True, YELLOW)
            diff_txt = font_hud.render(f"Diff: {DIFFICULTY_SETTINGS[self.difficulty]['label']}", True, CYAN)
            self.screen.blit(score_txt, (sw - 140, 15))
            self.screen.blit(diff_txt, (20, 15))

            # Combo & Controller & Mute Indicator
            ctrl_status = f"🎮 {len(self.joysticks)} Gamepad" if self.joysticks else "⌨️ Keyboard"
            audio_icon = "🔇 MUTED" if self.sound_manager.muted else "🔊 SFX"
            audio_txt = font_hud.render(f"{ctrl_status} | [M] {audio_icon}", True, (200, 200, 200))
            self.screen.blit(audio_txt, (sw - 230, 40))

            # Boss HP Bar im HUD rendern
            for boss in self.bosses:
                if boss.alive():
                    bar_w = 260
                    bar_h = 16
                    bar_x = sw // 2 - bar_w // 2
                    bar_y = 12
                    pct = max(0.0, boss.health / boss.max_health)
                    bar_col = (255, 30, 30) if boss.in_rage_phase else (220, 40, 40)
                    pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                    pygame.draw.rect(self.screen, bar_col, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)
                    pygame.draw.rect(self.screen, (255, 215, 0), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=4)
                    title_str = "BOSS PHASE 2 (WUT!)" if boss.in_rage_phase else "ENDGEGNER"
                    b_txt = font_hud.render(f"{title_str}: {boss.health} / {boss.max_health} HP", True, WHITE)
                    self.screen.blit(b_txt, (sw // 2 - b_txt.get_width() // 2, bar_y - 2))
            
            active_labels = []
            if self.paddle.is_stunned():
                active_labels.append("STUNNED (Betäubt!)")
            for etype, expire in list(self.active_effects.items()):
                rem = expire - now
                if rem <= 2000 and (now // 200) % 2 == 0:
                    continue
                active_labels.append(etype.replace("_", " ").title())
            
            if active_labels:
                color = RED if "STUNNED (Betäubt!)" in active_labels else GREEN
                eff_surf = font_hud.render(f"Effekte: {', '.join(active_labels)}", True, color)
                self.screen.blit(eff_surf, (20, sh - 25))
        
        if self.state == STATE_PAUSED:
            font = pygame.font.SysFont(None, 56, bold=True)
            text_surf = font.render("SPIEL PAUSIERT", True, WHITE)
            text_rect = text_surf.get_rect(center=(sw // 2, sh // 2 - 60))
            self.screen.blit(text_surf, text_rect)
            
            sub_font = pygame.font.SysFont(None, 22)
            
            # Interactive Pause Buttons mit Fokus-Rahmen
            mpos = pygame.mouse.get_pos()
            
            col_res = (50, 150, 50) if not self.pause_resume_rect.collidepoint(mpos) else (70, 190, 70)
            col_opt = (0, 130, 140) if not self.pause_opts_rect.collidepoint(mpos) else (0, 170, 180)
            col_men = (70, 70, 70) if not self.pause_menu_rect.collidepoint(mpos) else (100, 100, 100)
            
            pygame.draw.rect(self.screen, col_res, self.pause_resume_rect, border_radius=6)
            border_res = YELLOW if self.pause_selected_idx == 0 else WHITE
            pygame.draw.rect(self.screen, border_res, self.pause_resume_rect, width=3 if self.pause_selected_idx == 0 else 2, border_radius=6)
            txt_res = sub_font.render("Weiter [P/A]", True, WHITE)
            self.screen.blit(txt_res, (self.pause_resume_rect.centerx - txt_res.get_width() // 2, self.pause_resume_rect.centery - txt_res.get_height() // 2))

            pygame.draw.rect(self.screen, col_opt, self.pause_opts_rect, border_radius=6)
            border_opt = YELLOW if self.pause_selected_idx == 1 else WHITE
            pygame.draw.rect(self.screen, border_opt, self.pause_opts_rect, width=3 if self.pause_selected_idx == 1 else 2, border_radius=6)
            txt_opt = sub_font.render("Optionen [O]", True, WHITE)
            self.screen.blit(txt_opt, (self.pause_opts_rect.centerx - txt_opt.get_width() // 2, self.pause_opts_rect.centery - txt_opt.get_height() // 2))

            pygame.draw.rect(self.screen, col_men, self.pause_menu_rect, border_radius=6)
            border_men = YELLOW if self.pause_selected_idx == 2 else WHITE
            pygame.draw.rect(self.screen, border_men, self.pause_menu_rect, width=3 if self.pause_selected_idx == 2 else 2, border_radius=6)
            txt_men = sub_font.render("Hauptmenü [ESC]", True, WHITE)
            self.screen.blit(txt_men, (self.pause_menu_rect.centerx - txt_men.get_width() // 2, self.pause_menu_rect.centery - txt_men.get_height() // 2))

        elif self.state == STATE_SETTINGS:
            self.settings_menu.draw(self.sound_manager, self.difficulty, self.is_fullscreen)

        elif self.state in (STATE_LEVEL_CLEARED, STATE_ALL_CLEARED):
            self.particles.draw(self.screen)
            for ft in self.floating_texts:
                self.screen.blit(ft.image, ft.rect.topleft)
            
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
                    self.screen.blit(row_txt, (sw // 2 - 130, 265 + idx * 25))

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
            border_m = YELLOW if self.win_selected_idx == 0 else WHITE
            pygame.draw.rect(self.screen, border_m, self.menu_btn_rect, width=3 if self.win_selected_idx == 0 else 2, border_radius=8)
            menu_txt = row_font.render("Hauptmenü", True, WHITE)
            self.screen.blit(menu_txt, (self.menu_btn_rect.centerx - menu_txt.get_width() // 2, self.menu_btn_rect.centery - menu_txt.get_height() // 2))
            
            next_level = self.current_level_num + 1
            if os.path.exists(os.path.join("levels", get_level_name(next_level))):
                self.next_btn_rect = pygame.Rect(sw // 2 + 20, sh - 70, 190, 45)
                pygame.draw.rect(self.screen, (50, 150, 50), self.next_btn_rect, border_radius=8)
                border_n = YELLOW if self.win_selected_idx == 1 else WHITE
                pygame.draw.rect(self.screen, border_n, self.next_btn_rect, width=3 if self.win_selected_idx == 1 else 2, border_radius=8)
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
            border_p = YELLOW if self.hs_selected_idx == 0 else WHITE
            pygame.draw.rect(self.screen, border_p, self.hs_prev_rect, width=3 if self.hs_selected_idx == 0 else 1, border_radius=5)

            pygame.draw.rect(self.screen, (70, 70, 70), self.hs_next_rect, border_radius=5)
            border_nx = YELLOW if self.hs_selected_idx == 1 else WHITE
            pygame.draw.rect(self.screen, border_nx, self.hs_next_rect, width=3 if self.hs_selected_idx == 1 else 1, border_radius=5)

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
            border_d = YELLOW if self.hs_selected_idx == 2 else WHITE
            pygame.draw.rect(self.screen, border_d, self.hs_delete_rect, width=3 if self.hs_selected_idx == 2 else 2, border_radius=8)
            del_txt = row_font.render("Highscores löschen", True, WHITE)
            self.screen.blit(del_txt, (self.hs_delete_rect.centerx - del_txt.get_width() // 2, self.hs_delete_rect.centery - del_txt.get_height() // 2))

            pygame.draw.rect(self.screen, (70, 70, 70), self.hs_back_rect, border_radius=8)
            border_b = YELLOW if self.hs_selected_idx == 3 else WHITE
            pygame.draw.rect(self.screen, border_b, self.hs_back_rect, width=3 if self.hs_selected_idx == 3 else 2, border_radius=8)
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