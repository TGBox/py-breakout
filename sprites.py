from __future__ import annotations
from typing import Any
import pygame
import random
import math
from settings import *

if not pygame.font.get_init():
    pygame.font.init()

BLOCK_HEALTH_COLORS: dict[int, tuple[int, int, int]] = {
    1: YELLOW,
    2: ORANGE_YELLOW,
    3: ORANGE,
    4: REDDISH_ORANGE,
    5: RED,
}

class FloatingText(pygame.sprite.Sprite):
    """Aufsteigender, verblassender Text für Punkte und Treffer-Feedback"""
    def __init__(self, x: float, y: float, text: str, color: tuple[int, int, int] = WHITE, font_size: int = 22, lifetime: int = 40, speed_y: float = -1.2, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font_size = font_size
        self.lifetime = lifetime
        self.current_life = lifetime
        self.speed_y = speed_y
        
        self.font = pygame.font.SysFont(None, font_size, bold=True)
        self.image: pygame.Surface = pygame.Surface((10, 10))
        self.rect: pygame.Rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        self.update_image()

    def update_image(self):
        alpha = max(0, int(255 * (self.current_life / self.lifetime)))
        text_surf = self.font.render(self.text, True, self.color)
        shadow_surf = self.font.render(self.text, True, BLACK)
        
        self.image = pygame.Surface((text_surf.get_width() + 4, text_surf.get_height() + 4), pygame.SRCALPHA)
        self.image.blit(shadow_surf, (3, 3))
        self.image.blit(text_surf, (1, 1))
        self.image.set_alpha(alpha)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self):
        self.current_life -= 1
        if self.current_life <= 0:
            self.kill()
            return
        self.y += self.speed_y
        self.update_image()


class Particle(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, color: tuple[int, ...], speed_x: float | None = None, speed_y: float | None = None, lifetime: int = 30, size: int = 4):
        super().__init__()
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.current_life = lifetime
        
        self.speed_x = random.uniform(-3.0, 3.0) if speed_x is None else speed_x
        self.speed_y = random.uniform(-4.0, 2.0) if speed_y is None else speed_y
        self.gravity = 0.15
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        self._update_image()

    def _update_image(self):
        alpha = max(0, int(255 * (self.current_life / self.lifetime)))
        r, g, b = self.color[:3]
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (r, g, b, alpha), (self.size // 2, self.size // 2), max(1, self.size // 2))

    def update(self):
        self.current_life -= 1
        if self.current_life <= 0:
            self.kill()
            return
            
        self.x += self.speed_x
        self.speed_y += self.gravity
        self.y += self.speed_y
        
        self.rect.center = (int(self.x), int(self.y))
        self._update_image()


class Block(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int, block_type: str, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.block_type = block_type
        self.width = width if width > 0 else BLOCK_WIDTH
        self.height = height if height > 0 else BLOCK_HEIGHT
        
        self.grid_col = 0
        self.grid_row = 0
        self.grid_cols = 10
        self.grid_rows = 10
        
        # Standardwerte
        self.health = 1
        self.is_powerup = False
        self.is_powerdown = False
        self.is_explosive = False
        self.is_unbreakable = False
        self.move_speed = 0
        self.start_x = x
        self.move_range = 70
        self.move_dir = 1

        if self.block_type in ('2', '3', '4', '5'):
            self.health = int(self.block_type)
        elif self.block_type in ('P', 'powerup'):
            self.is_powerup = True
        elif self.block_type in ('D', 'powerdown'):
            self.is_powerdown = True
        elif self.block_type in ('B', 'E', 'bomb', 'explosive'):
            self.health = 1
            self.is_explosive = True
        elif self.block_type in ('X', 'U', 'steel', 'unbreakable'):
            self.health = 999
            self.is_unbreakable = True
        elif self.block_type == 'T':
            self.health = 999
            self.is_unbreakable = True
        elif self.block_type == 'M':
            self.health = 1
            self.move_speed = 2
            
        self.image: pygame.Surface = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self._update_appearance()

    def _update_appearance(self):
        self.image = pygame.Surface((self.width, self.height))
        font_size = max(10, min(18, int(self.height * 0.6)))
        font = pygame.font.SysFont(None, font_size, bold=True)

        if self.block_type == '1':
            self.image.fill(GREEN)
        elif self.block_type in ('2', '3', '4', '5'):
            self.image.fill(BLOCK_HEALTH_COLORS.get(self.health, YELLOW))
        elif self.block_type in ('P', 'powerup'):
            self.image.fill(BLUE)
        elif self.block_type in ('D', 'powerdown'):
            self.image.fill(DARK_PURPLE)
        elif self.block_type in ('B', 'E', 'bomb', 'explosive'):
            self.image.fill((220, 40, 40))
            pygame.draw.rect(self.image, (255, 220, 0), (0, 0, self.width, self.height), 2)
            txt = font.render("BOMB", True, WHITE)
            self.image.blit(txt, txt.get_rect(center=(self.width // 2, self.height // 2)))
        elif self.block_type in ('X', 'U', 'steel', 'unbreakable'):
            self.image.fill((100, 100, 115))
            pygame.draw.rect(self.image, (210, 210, 230), (0, 0, self.width, self.height), 2)
            txt = font.render("STAHL", True, (220, 220, 220))
            self.image.blit(txt, txt.get_rect(center=(self.width // 2, self.height // 2)))
        elif self.block_type == 'T':
            self.image.fill((140, 30, 210))
            pygame.draw.rect(self.image, (0, 255, 255), (0, 0, self.width, self.height), 2)
            txt = font.render("PORTAL", True, (0, 255, 255))
            self.image.blit(txt, txt.get_rect(center=(self.width // 2, self.height // 2)))
        elif self.block_type == 'M':
            self.image.fill((255, 170, 0))
            pygame.draw.rect(self.image, WHITE, (0, 0, self.width, self.height), 2)
            txt = font.render("MOVE", True, BLACK)
            self.image.blit(txt, txt.get_rect(center=(self.width // 2, self.height // 2)))
            
        self._render_decorations()

    def _render_decorations(self):
        font_size = max(10, min(18, int(self.height * 0.6)))
        font = pygame.font.SysFont(None, font_size, bold=True)
        if self.is_powerup:
            pygame.draw.rect(self.image, WHITE, (0, 0, self.width, self.height), 2)
            txt = font.render("P", True, WHITE)
            self.image.blit(txt, (self.width // 2 - txt.get_width() // 2, self.height // 2 - txt.get_height() // 2))
        elif self.is_powerdown:
            pygame.draw.rect(self.image, MAGENTA, (0, 0, self.width, self.height), 2)
            txt = font.render("D", True, MAGENTA)
            self.image.blit(txt, (self.width // 2 - txt.get_width() // 2, self.height // 2 - txt.get_height() // 2))

    def reposition_and_rescale(self, screen_width: int, screen_height: int, padding: int = 4, offset_y: int = 60):
        if not hasattr(self, 'grid_cols') or self.grid_cols <= 0:
            return
        avail_width = screen_width - 40
        block_width = max(15, (avail_width - (self.grid_cols - 1) * padding) // self.grid_cols)
        avail_height = int(screen_height * 0.45) - offset_y
        block_height = max(12, (avail_height - (self.grid_rows - 1) * padding) // self.grid_rows) if self.grid_rows > 0 else 30
        total_width = self.grid_cols * block_width + (self.grid_cols - 1) * padding
        offset_x = (screen_width - total_width) // 2

        self.width = block_width
        self.height = block_height
        self.start_x = offset_x + self.grid_col * (block_width + padding)
        self.rect = pygame.Rect(
            self.start_x,
            offset_y + self.grid_row * (block_height + padding),
            block_width,
            block_height
        )
        self._update_appearance()

    def update(self):
        if self.block_type == 'M' and self.move_speed > 0:
            self.rect.x += self.move_speed * self.move_dir
            if self.rect.x > self.start_x + self.move_range:
                self.rect.x = self.start_x + self.move_range
                self.move_dir = -1
            elif self.rect.x < self.start_x - self.move_range:
                self.rect.x = self.start_x - self.move_range
                self.move_dir = 1

    def hit(self, force_destroy: bool = False) -> bool:
        if self.is_unbreakable and not force_destroy:
            return False
            
        if force_destroy:
            self.health = 0
            return True
            
        self.health -= 1
        self._update_appearance()
            
        return self.health <= 0


class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.width = 10
        self.height = 18
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255, 60, 60), (0, 0, self.width, self.height))
        pygame.draw.ellipse(self.image, (255, 220, 0), (2, 2, self.width - 4, self.height - 4))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = 5.5

    def update(self, screen_height: int = SCREEN_HEIGHT):
        self.rect.y += int(self.speed_y)
        if self.rect.top > screen_height:
            self.kill()


class Boss(pygame.sprite.Sprite):
    def __init__(self, screen_width: int = SCREEN_WIDTH, health: int = 25, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.health = health
        self.max_health = health
        self.width = 140
        self.height = 42
        self.speed_x = 3.5
        self.shoot_timer = 0
        self.shoot_interval = 85  # Frames (ca. 1.4 Sekunden)
        self.pending_projectile: BossProjectile | None = None
        
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=screen_width // 2, top=65)
        self._update_appearance()

    def _update_appearance(self):
        self.image.fill((0, 0, 0, 0))
        # Metallischer Rumpf mit leuchtendem Kern
        pygame.draw.rect(self.image, (160, 30, 40), (0, 0, self.width, self.height), border_radius=10)
        pygame.draw.rect(self.image, (255, 80, 80), (4, 4, self.width - 8, self.height - 8), border_radius=8)
        pygame.draw.rect(self.image, (255, 215, 0), (0, 0, self.width, self.height), width=3, border_radius=10)
        
        # Leuchtendes Auge / Kern
        core_w = max(20, self.width // 4)
        pygame.draw.ellipse(self.image, (255, 255, 255), (self.width // 2 - core_w // 2, self.height // 2 - 8, core_w, 16))
        pygame.draw.ellipse(self.image, (255, 0, 0), (self.width // 2 - core_w // 4, self.height // 2 - 5, core_w // 2, 10))

        # HP-Text auf dem Boss
        font = pygame.font.SysFont(None, 20, bold=True)
        txt = font.render(f"BOSS HP: {max(0, self.health)}", True, WHITE)
        self.image.blit(txt, (self.width // 2 - txt.get_width() // 2, 4))

    def reposition_and_rescale(self, screen_width: int, _screen_height: int):
        self.width = max(120, int(screen_width * 0.18))
        self.height = 42
        old_centerx = self.rect.centerx
        self.rect = pygame.Rect(0, 65, self.width, self.height)
        self.rect.centerx = max(self.width // 2, min(screen_width - self.width // 2, old_centerx))
        self._update_appearance()

    def update(self, screen_width: int = SCREEN_WIDTH, *args: Any, **kwargs: Any) -> None:
        self.rect.x += int(self.speed_x)
        if self.rect.left <= 20:
            self.rect.left = 20
            self.speed_x *= -1
        elif self.rect.right >= screen_width - 20:
            self.rect.right = screen_width - 20
            self.speed_x *= -1

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            self.pending_projectile = BossProjectile(self.rect.centerx, self.rect.bottom)

    def hit(self, damage: int = 1) -> bool:
        self.health -= damage
        self._update_appearance()
        return self.health <= 0


class SecureBorder(pygame.sprite.Sprite):
    """Sicherheitsnetz unten am Bildschirmrand"""
    def __init__(self, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.image = pygame.Surface((screen_width, 8))
        self.image.fill(CYAN)
        pygame.draw.rect(self.image, WHITE, (0, 0, screen_width, 8), 1)
        self.rect = self.image.get_rect(topleft=(0, screen_height - 12))


class Paddle(pygame.sprite.Sprite):
    def __init__(self, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.width = 100
        self.height = 15
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(WHITE)
        
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.speed = 8
        self.inverted_controls = False
        self.stunned_until_ticks = 0

    def stun(self, duration_ms: int = 1500):
        now = pygame.time.get_ticks()
        self.stunned_until_ticks = now + duration_ms

    def is_stunned(self) -> bool:
        return pygame.time.get_ticks() < self.stunned_until_ticks

    def update(self, screen_width: int = SCREEN_WIDTH):
        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        
        if self.inverted_controls:
            move_left, move_right = move_right, move_left

        current_speed = self.speed * 0.35 if self.is_stunned() else self.speed

        if move_left:
            self.rect.x -= int(current_speed)
        if move_right:
            self.rect.x += int(current_speed)
            
        if self.rect.left < 0: 
            self.rect.left = 0
        if self.rect.right > screen_width: 
            self.rect.right = screen_width

        # Visuelles Feedback bei Betäubung
        if self.is_stunned() and (pygame.time.get_ticks() // 100) % 2 == 0:
            pygame.draw.rect(self.image, (255, 230, 0), (0, 0, self.rect.width, self.rect.height), 2)


class Ball(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, speed_x: float = 5.0, speed_y: float = -5.0, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.radius = 8
        self.is_piercing = False
        self.is_fireball = False
        self.last_teleport_ticks = 0
        self.attached = False 
        self.sticky_offset_x = 0
        
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PURPLE, (self.radius, self.radius), self.radius)
        
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.pos_history: list[tuple[float, float]] = []

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
        else:
            pygame.draw.circle(self.image, WHITE, (self.radius, self.radius), self.radius, 1)

    def update(self, time_factor: float = 1.0, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT):
        if self.attached:
            self.pos_history.clear()
            return
            
        self.x += self.speed_x * time_factor
        self.y += self.speed_y * time_factor
        
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # Positionshistorie für Kometenschweif
        self.pos_history.append((self.rect.centerx, self.rect.centery))
        if len(self.pos_history) > 8:
            self.pos_history.pop(0)

        if self.rect.left <= 0:
            self.rect.left = 0
            self.x = float(self.rect.x)
            self.speed_x *= -1
        elif self.rect.right >= screen_width:
            self.rect.right = screen_width
            self.x = float(self.rect.x)
            self.speed_x *= -1
            
        if self.rect.top <= 0:
            self.rect.top = 0
            self.y = float(self.rect.y)
            self.speed_y *= -1

    def draw_trail_and_glow(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        if not self.alive() or self.attached:
            return
            
        if self.is_fireball:
            base_color = (255, 140, 0)
        elif self.is_piercing:
            base_color = (255, 50, 50)
        else:
            base_color = (195, 56, 255)

        # 1. Kometenschweif
        num_pts = len(self.pos_history)
        for idx, (px, py) in enumerate(self.pos_history[:-1]):
            alpha = int(210 * (idx + 1) / max(1, num_pts))
            r_scale = max(2, int(self.radius * (idx + 1) / max(1, num_pts)))
            
            trail_surf = pygame.Surface((r_scale * 2, r_scale * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*base_color, alpha), (r_scale, r_scale), r_scale)
            surface.blit(trail_surf, (int(px) + offset_x - r_scale, int(py) + offset_y - r_scale))

        # 2. Pulsierender Glow-Ring
        glow_radius = self.radius + 5
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*base_color, 75), (glow_radius, glow_radius), glow_radius)
        pygame.draw.circle(glow_surf, (255, 255, 255, 130), (glow_radius, glow_radius), self.radius + 1, 2)
        surface.blit(glow_surf, (self.rect.centerx + offset_x - glow_radius, self.rect.centery + offset_y - glow_radius))


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
    def __init__(self, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.image = pygame.Surface((screen_width, 8))
        self.image.fill((0, 220, 255))
        pygame.draw.rect(self.image, WHITE, (0, 0, screen_width, 8), 1)
        self.rect = self.image.get_rect(topleft=(0, screen_height - 12))


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, powerup_type: str, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.effect_type = powerup_type
        self.size = 28
        
        self.config: dict[str, dict[str, Any]] = {
            # --- POSITIVE EFFEKTE (Kreise) ---
            "slow_time":        {"color": (50, 150, 255), "char": "S", "shape": "circle"},
            "bigger_ball":      {"color": (150, 50, 200), "char": "B", "shape": "circle"},
            "multiball":        {"color": (50, 230, 50),  "char": "M", "shape": "circle"},
            "expand_paddle":    {"color": (50, 200, 200), "char": "W", "shape": "circle"},
            "piercing_shot":    {"color": (255, 215, 0),  "char": "P", "shape": "circle"},
            "sticky_paddle":    {"color": (230, 50, 230), "char": "K", "shape": "circle"},
            "laser_paddle":     {"color": (255, 50, 50),   "char": "L", "shape": "circle"},
            "safety_net":       {"color": (0, 220, 255),  "char": "N", "shape": "circle"},
            "secure_border":    {"color": (0, 255, 255),   "char": "N", "shape": "circle"},
            "fireball":         {"color": (255, 140, 0),  "char": "F", "shape": "circle"},
            "magnet":           {"color": (255, 100, 255), "char": "U", "shape": "circle"},
            "score_boost":      {"color": (255, 255, 100), "char": "+", "shape": "circle"},
            
            # --- NEGATIVE EFFEKTE (Dreiecke) ---
            "shrink_paddle":    {"color": (255, 50, 50),  "char": "C", "shape": "triangle"},
            "speed_time":       {"color": (255, 100, 0),  "char": "F", "shape": "triangle"},
            "smaller_ball":     {"color": (255, 150, 0),  "char": "s", "shape": "triangle"},
            "score_drain":      {"color": (200, 0, 0),    "char": "-", "shape": "triangle"},
            "inverted_controls":{"color": (180, 0, 180),  "char": "I", "shape": "triangle"},
        }
        
        cfg = self.config.get(self.effect_type, {"color": (130, 130, 130), "char": "?", "shape": "square"})
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        radius = self.size // 2
        
        font = pygame.font.SysFont(None, 20, bold=True)
        text_color = BLACK if sum(cfg["color"]) > 380 else WHITE
        text_surf = font.render(cfg["char"], True, text_color)
        
        if cfg["shape"] == "circle":
            pygame.draw.circle(self.image, cfg["color"], (radius, radius), radius)
            pygame.draw.circle(self.image, WHITE, (radius, radius), radius, 2)
            text_rect = text_surf.get_rect(center=(radius, radius))
            
        elif cfg["shape"] == "triangle":
            points = [(2, 2), (self.size - 2, 2), (radius, self.size - 2)]
            pygame.draw.polygon(self.image, cfg["color"], points)
            pygame.draw.polygon(self.image, WHITE, points, 2)
            text_rect = text_surf.get_rect(center=(radius, radius - 3))
            
        else:
            pygame.draw.rect(self.image, cfg["color"], (0, 0, self.size, self.size))
            pygame.draw.rect(self.image, WHITE, (0, 0, self.size, self.size), 2)
            text_rect = text_surf.get_rect(center=(radius, radius))

        self.image.blit(text_surf, text_rect)
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        self.speed_y = 3  

    def update(self, screen_height: int = SCREEN_HEIGHT):
        self.rect.y += self.speed_y
        if self.rect.top > screen_height:
            self.kill()