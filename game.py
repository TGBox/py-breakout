import math
import pygame
import os
import json
import random
from settings import *
from level_manager import LevelManager
from sprites import Paddle, Ball, PowerUp
from menu import LevelSelectionMenu

def get_level_name(lvl_nr: int) -> str:
    """Method to take the level number int and convert it to the corresponding level file name.

    Args:
        lvl_nr (int): The current level number.

    Returns:
        str: The level file name for the given level number.
    """
    if lvl_nr <= 9:
        return f"Level00{lvl_nr}.txt"
    elif lvl_nr > 9 and lvl_nr <= 99:
        return f"Level0{lvl_nr}.txt"
    else: # lvl_nr > 99
        return f"Level{lvl_nr}.txt"

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MENU
        
        # Level-Verwaltung
        self.level_manager = LevelManager()
        self.current_level_num = 1
        self.unlocked_level = 1 # NEU: Der Spielfortschritt des Spielers
        
        # Spielstand laden.
        self.load_game()
        
        # Menü initialisieren
        self.menu = LevelSelectionMenu(self.screen) # NEU
        
        # Sprite-Gruppen
        self.all_sprites = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.balls = pygame.sprite.Group()
        
        self.paddle = Paddle()
        self.time_factor = 1.0 
        self.active_effects = {}
    
    def save_game(self):
        """Speichert den aktuellen Fortschritt in einer JSON-Datei."""
        save_data = {
            "unlocked_level": self.unlocked_level
        }
        try:
            with open("save_progress.json", "w") as file:
                json.dump(save_data, file, indent=4)
            print(f"[Save] Fortschritt gespeichert! Höchstes Level: {self.unlocked_level}")
        except Exception as e:
            print(f"[Save-Fehler] Konnte Spielstand nicht speichern: {e}")

    def load_game(self):
        """Lädt den Fortschritt. Falls keine Datei existiert, startet der Spieler bei Level 1."""
        if os.path.exists("save_progress.json"):
            try:
                with open("save_progress.json", "r") as file:
                    save_data = json.load(file)
                    self.unlocked_level = save_data.get("unlocked_level", 1)
                print(f"[Load] Spielstand erfolgreich geladen. Freigeschaltet bis Level: {self.unlocked_level}")
            except Exception as e:
                print(f"[Load-Fehler] Datei beschädigt, starte bei Level 1. Fehler: {e}")
                self.unlocked_level = 1
        else:
            print("[Load] Kein Spielstand gefunden. Starte neues Spiel.")
            self.unlocked_level = 1

    def start_game(self):
        self.all_sprites.empty()
        self.blocks.empty()
        self.powerups.empty()
        self.balls.empty()
        self.active_effects.clear()
        self.time_factor = 1.0
        
        level_file = get_level_name(self.current_level_num)
        self.blocks = self.level_manager.load_level(level_file)
        
        if len(self.blocks) == 0:
            self.state = STATE_MENU
            return

        self.reset_paddle()
        
        self.paddle_sticky = False # NEU: Klebe-Effekt zu Beginn ausschalten
        
        # ANGEPASST: Ball startet direkt auf der Position des Paddles
        start_ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - 8)
        start_ball.attached = True # NEU: Ball anheften
        self.balls.add(start_ball)
        
        self.all_sprites.add(self.paddle, self.balls, self.blocks)
        self.state = STATE_PLAYING

    def reset_paddle(self):
        pos = self.paddle.rect.center if hasattr(self.paddle, 'rect') else (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)
        self.paddle.image = pygame.Surface((100, 15))
        self.paddle.image.fill(WHITE)
        self.paddle.rect = self.paddle.image.get_rect(centerx=pos[0], bottom=SCREEN_HEIGHT-30)

    def spawn_powerup(self, x, y, guaranteed=False):
        if guaranteed or random.random() < 0.30:
            effects = ["sticky_paddle", "expand_paddle", "shrink_paddle", "slow_time", "speed_time", 
                       "bigger_ball", "smaller_ball", "multiball", "piercing_shot"]
            chosen_effect = random.choice(effects)
            p_up = PowerUp(x, y, chosen_effect)
            self.powerups.add(p_up)
            self.all_sprites.add(p_up)

    def apply_powerup(self, powerup):
        now = pygame.time.get_ticks()
        duration = 8000
        
        if powerup.effect_type == "sticky_paddle":
            print("Power up - sticky paddle")
            self.paddle_sticky = True
            self.paddle.image = pygame.Surface((100, 15))
            self.paddle.image.fill(YELLOW)
            self.active_effects["sticky_paddle"] = now + duration
        elif powerup.effect_type == "expand_paddle":
            print("Power up - larger paddle")
            self.paddle.image = pygame.Surface((160, 15))
            self.paddle.image.fill(GREEN)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            self.active_effects["paddle_size"] = now + duration
        elif powerup.effect_type == "shrink_paddle":
            print("Power down - smaller paddle")
            self.paddle.image = pygame.Surface((50, 15))
            self.paddle.image.fill(RED)
            self.paddle.rect = self.paddle.image.get_rect(center=self.paddle.rect.center)
            self.active_effects["paddle_size"] = now + duration
        elif powerup.effect_type == "slow_time":
            print("Power up - slow motion")
            self.time_factor = 0.5
            self.active_effects["time_distortion"] = now + duration
        elif powerup.effect_type == "speed_time":
            print("Power down - fast motion")
            self.time_factor = 1.5
            self.active_effects["time_distortion"] = now + duration
        elif powerup.effect_type == "bigger_ball":
            print("Power up - bigger ball")
            for ball in self.balls: ball.set_size(15)
            self.active_effects["ball_size"] = now + duration
        elif powerup.effect_type == "smaller_ball":
            print("Power down - smaller ball")
            for ball in self.balls: ball.set_size(4)
            self.active_effects["ball_size"] = now + duration
        elif powerup.effect_type == "piercing_shot":
            print("Power up - piercing")
            for ball in self.balls: ball.set_piercing(True)
            self.active_effects["piercing"] = now + duration
        elif powerup.effect_type == "multiball":
            print("Power up - multiball")
            current_balls = list(self.balls)
            for b in current_balls:
                new_ball = Ball(b.rect.centerx, b.rect.centery, b.speed_x * -1, b.speed_y)
                if "ball_size" in self.active_effects: new_ball.set_size(b.radius)
                if "piercing" in self.active_effects: new_ball.set_piercing(True)
                self.balls.add(new_ball)
                self.all_sprites.add(new_ball)

    def check_timers(self):
        now = pygame.time.get_ticks()
        if "paddle_size" in self.active_effects and now > self.active_effects["paddle_size"]:
            self.reset_paddle()
            del self.active_effects["paddle_size"]
        if "time_distortion" in self.active_effects and now > self.active_effects["time_distortion"]:
            self.time_factor = 1.0
            del self.active_effects["time_distortion"]
        if "ball_size" in self.active_effects and now > self.active_effects["ball_size"]:
            for ball in self.balls: ball.set_size(8)
            del self.active_effects["ball_size"]
        if "piercing" in self.active_effects and now > self.active_effects["piercing"]:
            for ball in self.balls: ball.set_piercing(False)
            del self.active_effects["piercing"]

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # NEU: Automatisch pausieren, wenn das Fenster vom Betriebssystem minimiert wird
            if event.type == pygame.WINDOWMINIMIZED:
                if self.state == STATE_PLAYING:
                    self.state = STATE_PAUSED

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED # ESC pausiert jetzt auch gemütlich
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING
                    else:
                        self.running = False
                
                # NEU: Reguläre Pause mit der Taste 'P' toggeln
                if event.key == pygame.K_p:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING

                # NEU: Pause + Minimieren mit der Taste 'M'
                if event.key == pygame.K_m:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    pygame.display.iconify() # Minimiert das Pygame-Fenster in die Taskleiste
                
                # NEU: Leertaste schießt den angehefteten Ball ab
                if event.key == pygame.K_SPACE and self.state == STATE_PLAYING:
                    for ball in self.balls:
                        if ball.attached:
                            ball.attached = False
                            ball.speed_x = 0.0  
                            ball.speed_y = -1 * BALL_SPEED

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == STATE_MENU:
                    clicked_level = self.menu.handle_click(event.pos)
                    if clicked_level:
                        self.current_level_num = clicked_level
                        self.start_game()

    def update(self):
        # Logik läuft NUR im PLAYING-Zustand. Im PAUSED-Zustand friert alles ein.
        if self.state == STATE_PLAYING:
            self.check_timers()
            
            # 1. Am Paddle klebende Bälle exakt positionieren
            for ball in self.balls:
                if ball.attached:
                    ball.rect.centerx = self.paddle.rect.centerx
                    ball.rect.bottom = self.paddle.rect.top
                    ball.x = float(ball.rect.x)
                    ball.y = float(ball.rect.y)

            # 2. Alle Sprites aktualisieren (Doppelten Ball-Aufruf entfernt!)
            self.paddle.update()
            self.powerups.update()
            self.blocks.update()
            self.balls.update(self.time_factor)
            
            # 3. Kollisionen und Ereignisse für jeden Ball prüfen
            for ball in list(self.balls):
                
                # --- PADDLE-KOLLISION ---
                if pygame.sprite.collide_rect(ball, self.paddle) and ball.speed_y > 0:
                    if self.paddle_sticky:
                        ball.attached = True
                        ball.rect.bottom = self.paddle.rect.top
                        ball.x = float(ball.rect.x)
                        ball.y = float(ball.rect.y)
                    else:
                        hit_pos = ball.rect.centerx - self.paddle.rect.centerx
                        relative_hit = max(-1.0, min(1.0, hit_pos / (self.paddle.rect.width / 2)))
                        
                        if abs(relative_hit) < 0.1:
                            relative_hit = random.choice([-0.15, 0.15])
                        
                        ball.speed_x = relative_hit * (BALL_SPEED * 0.8)
                        ball.speed_y = -math.sqrt(BALL_SPEED**2 - ball.speed_x**2)

                # --- BLOCK-KOLLISION ---
                hit_blocks = pygame.sprite.spritecollide(ball, self.blocks, False)
                if hit_blocks:
                    if not ball.is_piercing:
                        ball.speed_y *= -1
                        
                    for block in hit_blocks:
                        block.health -= 1
                        
                        # KORREKTUR: Prüft flexibel auf Zahl 2 ODER Text '2' ODER 'R'
                        if block.block_type in [2, '2', 'R', 'RED']:
                            # Falls er noch lebt, färbe ihn um
                            if block.health > 0:
                                block.image.fill(ORANGE)
                        
                        # Erst bei 0 Leben zerstören
                        if block.health <= 0:
                            self.spawn_powerup(block.rect.x, block.rect.y, guaranteed=(block.block_type == 'P'))
                            block.kill()

                # --- AUS-DEM-SPIEL-PRÜFUNG ---
                if ball.rect.top > SCREEN_HEIGHT:
                    ball.kill()

            # 4. Power-Ups einsammeln
            collected_powerups = pygame.sprite.spritecollide(self.paddle, self.powerups, True)
            for p_up in collected_powerups:
                self.apply_powerup(p_up)

            # 5. Game Over Prüfung (Keine Bälle mehr auf dem Feld)
            if len(self.balls) == 0:
                self.state = STATE_MENU

            # 6. Level geschafft Prüfung
            if len(self.blocks) == 0:
                next_level = self.current_level_num + 1
                if next_level > self.unlocked_level:
                    self.unlocked_level = next_level
                    self.save_game() # Fortschritt speichern
                
                if os.path.exists(os.path.join("levels", get_level_name(next_level))):
                    self.current_level_num = next_level
                    self.start_game()
                else:
                    print("Glückwunsch! Alle verfügbaren Level gemeistert!")
                    self.state = STATE_MENU

    def draw(self):
        self.screen.fill(BLACK) # Oder dein Hintergrund
        
        # Zeichne nur alle Sprites, wenn kein Menü offen ist, damit man das eingefrorene Spiel auch während der Pause im Hintergrund sieht
        if self.state == STATE_PLAYING or self.state == STATE_PAUSED:
            self.all_sprites.draw(self.screen)
        
        # NEU: Wenn pausiert, legen wir einen Text drüber
        if self.state == STATE_PAUSED:
            # Ein großer, fetter Pause-Schriftzug
            font = pygame.font.SysFont(None, 60, bold=True)
            text_surf = font.render("SPIEL PAUSIERT", True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Optional: Kleiner Untertext mit Anleitung
            sub_font = pygame.font.SysFont(None, 24)
            sub_surf = sub_font.render("Drücke 'P' oder 'ESC' zum Weiterspielen", True, (200, 200, 200))
            sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 50))
            
            self.screen.blit(text_surf, text_rect)
            self.screen.blit(sub_surf, sub_rect)
            
        elif self.state == STATE_MENU:
            self.menu.draw(self.unlocked_level)
            
        pygame.display.flip()
        
    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)