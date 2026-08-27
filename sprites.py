from __future__ import annotations
from typing import Any

from pygame import Rect, sprite, Surface
import pygame
from settings import *

if not pygame.font.get_init():
    pygame.font.init()

# Farbe je verbleibendem Leben für die mehrschlägigen Blöcke (Typen '2'-'5').
# So bekommt jeder Treffer sichtbar eine "schwächere" Farbe, unabhängig davon,
# mit wie viel Leben der Block gestartet ist.
BLOCK_HEALTH_COLORS: dict[int, tuple[int, int, int]] = {
    1: YELLOW,
    2: ORANGE_YELLOW,
    3: ORANGE,
    4: REDDISH_ORANGE,
    5: RED
}

class Block(sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int, block_type: str, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.block_type = block_type # '1'-'5' = normale/starke Blöcke, 'P' = PowerUp, 'B' = Bomb, 'X' = Stahl, 'T' = Portal, 'M' = Moving
        self.width = BLOCK_WIDTH
        self.height = BLOCK_HEIGHT
        
        self.image: Surface = Surface((width, height))
        
        # Standardwerte
        self.health = 1
        self.is_powerup = False
        self.is_unbreakable = False
        self.move_speed = 0
        self.start_x = x
        self.move_range = 70
        self.move_dir = 1
        
        font = pygame.font.SysFont(None, 18, bold=True)

        # Farbe und Eigenschaften basierend auf dem Typ setzen
        if self.block_type == '1':
            self.image.fill(GREEN)
        elif self.block_type in ('2', '3', '4', '5'):
            self.health = int(self.block_type)
            self.image.fill(BLOCK_HEALTH_COLORS[self.health])
        elif self.block_type == 'P':
            self.image.fill(BLUE)
            self.is_powerup = True # Lässt später ein Power-Up fallen
        elif self.block_type == 'B':  # Explosions- / Bombenblock
            self.health = 1
            self.image.fill((220, 40, 40))
            pygame.draw.rect(self.image, (255, 220, 0), (0, 0, width, height), 2)
            txt = font.render("BOMB", True, WHITE)
            self.image.blit(txt, txt.get_rect(center=(width // 2, height // 2)))
        elif self.block_type == 'X':  # Unzerstörbarer Stahlblock
            self.health = 999
            self.is_unbreakable = True
            self.image.fill((100, 100, 115))
            pygame.draw.rect(self.image, (210, 210, 230), (0, 0, width, height), 2)
            txt = font.render("STAHL", True, (220, 220, 220))
            self.image.blit(txt, txt.get_rect(center=(width // 2, height // 2)))
        elif self.block_type == 'T':  # Portal- / Teleportblock
            self.health = 999
            self.is_unbreakable = True
            self.image.fill((140, 30, 210))
            pygame.draw.rect(self.image, (0, 255, 255), (0, 0, width, height), 2)
            txt = font.render("PORTAL", True, (0, 255, 255))
            self.image.blit(txt, txt.get_rect(center=(width // 2, height // 2)))
        elif self.block_type == 'M':  # Beweglicher Block
            self.health = 1
            self.move_speed = 2
            self.image.fill((255, 170, 0))
            pygame.draw.rect(self.image, WHITE, (0, 0, width, height), 2)
            txt = font.render("MOVE", True, BLACK)
            self.image.blit(txt, txt.get_rect(center=(width // 2, height // 2)))
            
        # Hitbox (Rect) setzen und positionieren
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self):
        if self.block_type == 'M' and self.move_speed > 0:
            self.rect.x += self.move_speed * self.move_dir
            if self.rect.x > self.start_x + self.move_range:
                self.rect.x = self.start_x + self.move_range
                self.move_dir = -1
            elif self.rect.x < self.start_x - self.move_range:
                self.rect.x = self.start_x - self.move_range
                self.move_dir = 1
        
    # Diese Methode wird aufgerufen, wenn der Ball den Block trifft
    def hit(self, force_destroy: bool = False) -> bool:
        if self.is_unbreakable and not force_destroy:
            return False

        self.health -= 1
        
        # Solange der Block noch steht, Farbe an das verbleibende Leben anpassen
        if self.health >= 1 and self.health in BLOCK_HEALTH_COLORS:
            self.image.fill(BLOCK_HEALTH_COLORS[self.health])
            
        # Gibt True zurück, wenn der Block komplett zerstört ist (0 Leben)
        return self.health <= 0 or force_destroy


class Paddle(sprite.Sprite):
    def __init__(self, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.width = 100
        self.height = 15
        self.image = Surface((self.width, self.height))
        self.image.fill(WHITE) # Nutzt WHITE aus settings.py
        
        self.rect: Rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.speed = 8

    def update(self):
        # Steuerung
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
            
        # Randbegrenzung (Paddle darf nicht aus dem Bildschirm fliegen)
        if self.rect.left < 0: 
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: 
            self.rect.right = SCREEN_WIDTH


class Ball(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, speed_x: float = 5.0, speed_y: float = -5.0, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.radius = 8
        self.is_piercing: bool = False
        self.is_fireball: bool = False
        self.last_teleport_ticks: int = 0
        
        self.attached = False 
        
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PURPLE, (self.radius, self.radius), self.radius)
        
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)

    def set_size(self, new_radius: int):
        self.radius = new_radius
        old_center = self.rect.center
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.update_appearance()
        self.rect = self.image.get_rect(center=old_center)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def set_piercing(self, piercing: bool):
        self.is_piercing = piercing
        self.update_appearance()

    def set_fireball(self, fireball: bool):
        self.is_fireball = fireball
        self.update_appearance()

    def update_appearance(self):
        self.image.fill((0, 0, 0, 0))
        if self.is_fireball:
            color = (255, 120, 0)
        elif self.is_piercing:
            color = RED
        else:
            color = PURPLE
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        if self.is_fireball:
            pygame.draw.circle(self.image, (255, 240, 0), (self.radius, self.radius), max(2, self.radius - 3))

    def update(self, time_factor: float = 1.0):
        if self.attached:
            return
        self.x += self.speed_x * time_factor
        self.y += self.speed_y * time_factor
        
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if self.rect.left <= 0:
            self.rect.left = 0
            self.x = float(self.rect.x)
            self.speed_x *= -1
        elif self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.x = float(self.rect.x)
            self.speed_x *= -1
            
        if self.rect.top <= 0:
            self.rect.top = 0
            self.y = float(self.rect.y)
            self.speed_y *= -1


class LaserProjectile(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.width = 4
        self.height = 14
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((255, 50, 50))
        pygame.draw.rect(self.image, (255, 200, 200), (1, 1, 2, self.height - 2))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10.0

    def update(self):
        self.rect.y -= int(self.speed)
        if self.rect.bottom < 0:
            self.kill()


class SafetyNet(pygame.sprite.Sprite):
    def __init__(self, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.image = pygame.Surface((SCREEN_WIDTH, 8))
        self.image.fill((0, 220, 255))
        pygame.draw.rect(self.image, WHITE, (0, 0, SCREEN_WIDTH, 8), 1)
        self.rect = self.image.get_rect(topleft=(0, SCREEN_HEIGHT - 12))


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, powerup_type: str, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.effect_type = powerup_type
        self.size = 28
        
        print(f"[PowerUp-Info] Typ '{self.effect_type}' ist gespawnt!")

        self.config: dict[str, dict[str, tuple[int, int, int] | str]] = {
            # --- POSITIVE EFFEKTE (Kreise) ---
            "slow_time":     {"color": (50, 150, 255), "char": "S", "shape": "circle"},
            "bigger_ball":   {"color": (50, 10, 50),   "char": "B", "shape": "circle"},
            "multiball":     {"color": (50, 230, 50),  "char": "M", "shape": "circle"},
            "expand_paddle": {"color": (50, 200, 200), "char": "W", "shape": "circle"},
            "piercing_shot": {"color": (255, 215, 0),  "char": "P", "shape": "circle"},
            "sticky_paddle": {"color": (230, 50, 230), "char": "K", "shape": "circle"},
            "laser_paddle":  {"color": (255, 50, 50),   "char": "L", "shape": "circle"},
            "safety_net":    {"color": (0, 220, 255),  "char": "N", "shape": "circle"},
            "fireball":      {"color": (255, 140, 0),  "char": "F", "shape": "circle"},
            
            # --- NEGATIVE EFFEKTE (Dreiecke) ---
            "shrink_paddle": {"color": (255, 50, 50),  "char": "C", "shape": "triangle"},
            "speed_time":    {"color": (255, 100, 0),  "char": "F", "shape": "triangle"},
            "smaller_ball":  {"color": (255, 150, 0),  "char": "S", "shape": "triangle"},
        }
        
        cfg = self.config.get(self.effect_type, {"color": (130, 130, 130), "char": "?", "shape": "square"})
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        radius = self.size // 2
        
        font = pygame.font.SysFont(None, 18, bold=True)
        text_surf = font.render(str(cfg["char"]), True, (0, 0, 0))
        
        if cfg["shape"] == "circle":
            pygame.draw.circle(self.image, cfg["color"], (radius, radius), radius)
            pygame.draw.circle(self.image, (255, 255, 255), (radius, radius), radius, 2)
            text_rect = text_surf.get_rect(center=(radius, radius))
            
        elif cfg["shape"] == "triangle":
            points = [(2, 2), (self.size - 2, 2), (radius, self.size - 2)]
            pygame.draw.polygon(self.image, cfg["color"], points)
            pygame.draw.polygon(self.image, (255, 255, 255), points, 2)
            text_rect = text_surf.get_rect(center=(radius, radius - 3))
            
        else:
            pygame.draw.rect(self.image, cfg["color"], (0, 0, self.size, self.size))
            pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.size, self.size), 2)
            text_rect = text_surf.get_rect(center=(radius, radius))

        self.image.blit(text_surf, text_rect)
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        self.speed_y = 3  

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()