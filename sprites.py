# sprites.py
from __future__ import annotations
from typing import Any
import pygame
import random
import math
from settings import *

class FloatingText(pygame.sprite.Sprite):
    """Schwebende Score- und Feedback-Texte mit Alpha-Fadeout"""
    def __init__(self, x: float, y: float, text: str, color: tuple[int, int, int] = WHITE, font_size: int = 22, lifetime: int = 45, speed_y: float = -1.2, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.font = pygame.font.SysFont(None, font_size, bold=True)
        self.text = text
        self.color = color
        self.alpha = 255
        self.speed_y = speed_y
        self.lifetime = lifetime
        self.x = x
        self.y = y
        self._update_surface()

    def _update_surface(self):
        txt_surf = self.font.render(self.text, True, self.color)
        self.image = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
        txt_surf.set_alpha(self.alpha)
        self.image.blit(txt_surf, (0, 0))
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, *args: Any, **kwargs: Any):
        self.y += self.speed_y
        self.lifetime -= 1
        self.alpha = max(0, self.alpha - int(255 / 45))
        if self.lifetime <= 0 or self.alpha <= 0:
            self.kill()
        else:
            self._update_surface()


class Particle(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, color: tuple[int, ...], *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(3, 6)
        self.speed_x = random.uniform(-4.0, 4.0)
        self.speed_y = random.uniform(-4.0, 4.0)
        self.lifetime = random.randint(15, 30)
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.size // 2, self.size // 2), self.size // 2)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, *args: Any, **kwargs: Any):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        
        if self.lifetime <= 0:
            self.kill()
        else:
            alpha = max(0, int((self.lifetime / 30) * 255))
            self.image.set_alpha(alpha)
            self.rect.center = (int(self.x), int(self.y))


class PowerUp(pygame.sprite.Sprite):
    COLOR_MAP: dict[str, tuple[int, int, int]] = {
        "sticky_paddle": YELLOW,
        "expand_paddle": GREEN,
        "shrink_paddle": RED,
        "slow_time": CYAN,
        "speed_time": PURPLE,
        "bigger_ball": ORANGE_YELLOW,
        "smaller_ball": (150, 150, 255),
        "multiball": MAGENTA,
        "piercing_shot": (255, 50, 50),
        "laser_paddle": REDDISH_ORANGE,
        "missile_paddle": (255, 140, 0),
        "shield_aura": (0, 220, 255),
        "safety_net": (0, 255, 200),
        "secure_border": CYAN,
        "magnet": (255, 215, 0),
        "score_boost": GREEN,
        "score_drain": DARK_PURPLE,
        "fireball": (255, 100, 0),
        "inverted_controls": (180, 0, 180)
    }

    def __init__(self, x: int, y: int, effect_type: str, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.effect_type = effect_type
        self.width = 16
        self.height = 16
        
        self.image = pygame.Surface((self.width, self.height))
        color = self.COLOR_MAP.get(self.effect_type, WHITE)
        self.image.fill(color)
        pygame.draw.rect(self.image, WHITE, (0, 0, self.width, self.height), 2)

        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        self.speed_y = 2.5

    def update(self, screen_height: int = SCREEN_HEIGHT, *args: Any, **kwargs: Any):
        self.rect.y += int(self.speed_y)
        if self.rect.top > screen_height:
            self.kill()


class Block(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int = 60, height: int = 20, health: int | str = 1, is_powerup: bool = False, is_unbreakable: bool = False, block_type: str = "1", grid_col: int = 0, grid_row: int = 0, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        if isinstance(health, str):
            block_type = health
            try:
                health = int(health)
            except ValueError:
                health = 1

        self.health = health
        self.max_health = self.health
        self.is_powerup = is_powerup
        self.is_powerdown = (block_type == "D")
        self.is_unbreakable = is_unbreakable or (block_type == "X")
        self.is_explosive = (block_type == "B")
        self.is_moving = (block_type == "M")
        self.block_type = block_type
        self.grid_col = grid_col
        self.grid_row = grid_row
        
        self.base_speed_x = random.choice([-2.0, 2.0]) if self.is_moving else 0.0
        self.speed_x = self.base_speed_x

        self.width = width
        self.height = height
        self.image = pygame.Surface((self.width, self.height))
        self.rect: pygame.Rect = self.image.get_rect(topleft=(x, y))
        
        self._update_appearance()

    def reposition_and_rescale(self, screen_width: int, screen_height: int, total_cols: int = 15, total_rows: int = 12):
        self.width = screen_width // max(1, total_cols)
        grid_top = 82
        max_h = int((screen_height - grid_top - 45) * 0.95)
        self.height = max(12, max_h // max(1, total_rows))
        
        new_x = self.grid_col * self.width
        new_y = grid_top + self.grid_row * self.height
        
        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect(topleft=(new_x, new_y))
        self._update_appearance()

    def _update_appearance(self):
        if self.block_type == "B":
            color = (220, 40, 40)
        elif self.block_type == "X":
            color = (100, 100, 115)
        elif self.block_type == "T":
            color = (140, 30, 210)
        elif self.block_type == "M":
            color = (255, 170, 0)
        elif self.is_powerup or self.block_type == "P":
            color = GREEN
        elif self.is_powerdown:
            color = DARK_PURPLE
        else:
            if self.health >= 5: color = RED
            elif self.health == 4: color = REDDISH_ORANGE
            elif self.health == 3: color = ORANGE
            elif self.health == 2: color = ORANGE_YELLOW
            else: color = YELLOW
            
        self.image.fill(color)
        
        if self.is_unbreakable:
            pygame.draw.rect(self.image, (220, 220, 240), (0, 0, self.width, self.height), 3)
            pygame.draw.line(self.image, (220, 220, 240), (0, 0), (self.width, self.height), 2)
            pygame.draw.line(self.image, (220, 220, 240), (0, self.height), (self.width, 0), 2)
        elif self.block_type == "B":
            pygame.draw.rect(self.image, YELLOW, (0, 0, self.width, self.height), 2)
            pygame.draw.circle(self.image, BLACK, (self.width // 2, self.height // 2), min(self.width, self.height) // 4)
        elif self.block_type == "T":
            pygame.draw.rect(self.image, CYAN, (0, 0, self.width, self.height), 2)
            pygame.draw.ellipse(self.image, WHITE, (self.width // 4, self.height // 4, self.width // 2, self.height // 2))
        elif self.is_powerup or self.block_type == "P":
            pygame.draw.rect(self.image, WHITE, (0, 0, self.width, self.height), 2)
            pygame.draw.line(self.image, WHITE, (self.width // 2, 3), (self.width // 2, self.height - 3), 2)
            pygame.draw.line(self.image, WHITE, (3, self.height // 2), (self.width - 3, self.height // 2), 2)
        elif self.is_powerdown:
            pygame.draw.rect(self.image, MAGENTA, (0, 0, self.width, self.height), 2)
            pygame.draw.line(self.image, MAGENTA, (3, self.height // 2), (self.width - 3, self.height // 2), 2)
        else:
            pygame.draw.rect(self.image, BLACK, (0, 0, self.width, self.height), 1)

    def update(self, *args: Any, **kwargs: Any):
        if self.is_moving:
            self.rect.x += int(self.speed_x)
            if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
                self.speed_x *= -1

    def hit(self, damage: int = 1, force_destroy: bool = False) -> bool:
        if self.is_unbreakable and not force_destroy:
            return False
            
        if force_destroy:
            self.health = 0
            return True
            
        self.health -= damage
        if self.health > 0:
            self._update_appearance()
            
        return self.health <= 0


class LaserProjectile(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.width = 4
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(RED)
        pygame.draw.rect(self.image, WHITE, (1, 1, 2, self.height - 2))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = -12.0

    def update(self, *args: Any, **kwargs: Any):
        self.rect.y += int(self.speed_y)
        if self.rect.bottom < 0:
            self.kill()


class HomingMissile(pygame.sprite.Sprite):
    """Zielsuchrakete für den Homing Missile Launcher"""
    def __init__(self, x: int, y: int, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.width = 12
        self.height = 20
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (255, 140, 0), [(6, 0), (12, 16), (6, 12), (0, 16)])
        pygame.draw.ellipse(self.image, (255, 220, 0), (3, 4, 6, 10))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 7.0

    def update(self, target_pos: tuple[int, int] | None = None, screen_height: int = SCREEN_HEIGHT):
        if target_pos:
            tx, ty = target_pos
            dx = tx - self.rect.centerx
            dy = ty - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.rect.x += int((dx / dist) * self.speed)
                self.rect.y += int((dy / dist) * self.speed)
        else:
            self.rect.y -= int(self.speed)

        if self.rect.bottom < 0 or self.rect.top > screen_height:
            self.kill()


class ShieldOrb(pygame.sprite.Sprite):
    """Kreisendes Schutzschild-Orb für Shield-Boss"""
    def __init__(self, boss: Any, angle_offset: float = 0.0, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.boss = boss
        self.angle = angle_offset
        self.radius = 12
        self.orbit_distance = 85
        self.health = 4
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 220, 255), (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, WHITE, (self.radius, self.radius), self.radius, 2)
        self.rect = self.image.get_rect()

    def update(self, *args: Any, **kwargs: Any):
        if not self.boss.alive():
            self.kill()
            return
        self.angle += 0.05
        cx = self.boss.rect.centerx + int(math.cos(self.angle) * self.orbit_distance)
        cy = self.boss.rect.centery + int(math.sin(self.angle) * 30)
        self.rect.center = (cx, cy)

    def hit(self, damage: int = 1) -> bool:
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        return False


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
    def __init__(self, screen_width: int = SCREEN_WIDTH, health: int = 25, boss_type: str = "NORMAL", *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.health = health
        self.max_health = health
        self.boss_type = boss_type
        self.in_rage_phase = False
        
        self.width = 140
        self.height = 42
        self.speed_x = 3.5
        self.shoot_timer = 0
        self.shoot_interval = 75 if boss_type != "SPAWNER" else 110
        self.pending_projectile: BossProjectile | None = None
        
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=screen_width // 2, top=65)
        self._update_appearance()

    def _update_appearance(self):
        self.image.fill((0, 0, 0, 0))
        
        bg_col = (180, 20, 20) if self.in_rage_phase else (160, 30, 40)
        border_col = (255, 50, 50) if self.in_rage_phase else (255, 215, 0)
        
        pygame.draw.rect(self.image, bg_col, (0, 0, self.width, self.height), border_radius=10)
        pygame.draw.rect(self.image, (255, 80, 80), (4, 4, self.width - 8, self.height - 8), border_radius=8)
        pygame.draw.rect(self.image, border_col, (0, 0, self.width, self.height), width=3, border_radius=10)
        
        core_w = max(20, self.width // 4)
        core_col = (255, 255, 0) if self.in_rage_phase else (255, 255, 255)
        pygame.draw.ellipse(self.image, core_col, (self.width // 2 - core_w // 2, self.height // 2 - 8, core_w, 16))
        pygame.draw.ellipse(self.image, (255, 0, 0), (self.width // 2 - core_w // 4, self.height // 2 - 5, core_w // 2, 10))

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
        if not self.in_rage_phase and self.health <= self.max_health // 2:
            self.in_rage_phase = True
            self.speed_x *= 1.4
            self.shoot_interval = max(35, self.shoot_interval - 25)

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


class SafetyNet(pygame.sprite.Sprite):
    """Schutznetz-Sprite für den Unterrand"""
    def __init__(self, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT, *groups: pygame.sprite.Group[Any]):
        super().__init__(*groups)
        self.image = pygame.Surface((screen_width, 8))
        self.image.fill((0, 220, 255))
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
        
        # Munition & Schild-Systeme
        self.laser_ammo = 0
        self.missile_ammo = 0
        self.shield_active = False
        self.last_shot_ticks = -1000

    def draw_ammo_and_shield(self, screen: pygame.Surface):
        # Schutzschild-Aura zeichnen
        if self.shield_active:
            s_rect = self.rect.inflate(16, 12)
            pygame.draw.rect(screen, CYAN, s_rect, width=3, border_radius=10)
            
        # Munitionsanzeige über dem Paddle
        font = pygame.font.SysFont(None, 18, bold=True)
        if self.laser_ammo > 0:
            txt = font.render(f"LASER: {self.laser_ammo}", True, RED)
            screen.blit(txt, (self.rect.left, self.rect.top - 18))
            
        if self.missile_ammo > 0:
            txt_m = font.render(f"MISSILE: {self.missile_ammo}", True, ORANGE)
            screen.blit(txt_m, (self.rect.right - txt_m.get_width(), self.rect.top - 18))

    def stun(self, duration_ms: int = 1500):
        now = pygame.time.get_ticks()
        self.stunned_until_ticks = now + duration_ms

    def is_stunned(self) -> bool:
        return pygame.time.get_ticks() < self.stunned_until_ticks

    def update(self, screen_width: int = SCREEN_WIDTH, controller_move_x: float = 0.0):
        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        
        move_val = 0.0
        if move_left: move_val -= 1.0
        if move_right: move_val += 1.0
        if controller_move_x != 0.0:
            move_val = controller_move_x
            
        if self.inverted_controls:
            move_val *= -1.0

        current_speed = self.speed * 0.35 if self.is_stunned() else self.speed

        if move_val != 0.0:
            self.rect.x += int(move_val * current_speed)
            
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

        self.pos_history: list[tuple[float, float]] = []
        self.max_history_length = 6

        self.x = float(x)
        self.y = float(y)
        self.speed_x = speed_x
        self.speed_y = speed_y

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self._update_appearance()
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))

    def set_size(self, new_radius: int):
        self.radius = new_radius
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self._update_appearance()
        pos = self.rect.center if hasattr(self, 'rect') else (self.x, self.y)
        self.rect = self.image.get_rect(center=pos)

    def set_piercing(self, piercing: bool):
        self.is_piercing = piercing
        self._update_appearance()

    def set_fireball(self, fireball: bool):
        self.is_fireball = fireball
        self._update_appearance()

    def _update_appearance(self):
        self.image.fill((0, 0, 0, 0))
        if self.is_fireball:
            color = (255, 80, 0)
        elif self.is_piercing:
            color = (255, 50, 50)
        else:
            color = WHITE

        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        if self.is_piercing or self.is_fireball:
            pygame.draw.circle(self.image, YELLOW, (self.radius, self.radius), max(2, self.radius // 2))

    def draw_trail_and_glow(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        trail_color = (255, 120, 0) if self.is_fireball else ((255, 50, 50) if self.is_piercing else (0, 220, 255))
        for idx, (hx, hy) in enumerate(self.pos_history):
            alpha = int((idx + 1) / len(self.pos_history) * 120)
            r = max(2, int(self.radius * ((idx + 1) / len(self.pos_history))))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*trail_color, alpha), (r, r), r)
            screen.blit(surf, (hx - r + offset_x, hy - r + offset_y))

        glow_surf = pygame.Surface(((self.radius + 6) * 2, (self.radius + 6) * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*trail_color, 70), (self.radius + 6, self.radius + 6), self.radius + 6)
        screen.blit(glow_surf, (self.rect.centerx - self.radius - 6 + offset_x, self.rect.centery - self.radius - 6 + offset_y))

    def update(self, time_factor: float = 1.0, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT, *args: Any, **kwargs: Any):
        if self.attached:
            return

        self.pos_history.append((self.x, self.y))
        if len(self.pos_history) > self.max_history_length:
            self.pos_history.pop(0)

        effective_speed_x = self.speed_x * time_factor
        effective_speed_y = self.speed_y * time_factor

        self.x += effective_speed_x
        self.y += effective_speed_y

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        if self.rect.left <= 0:
            self.rect.left = 0
            self.x = float(self.rect.centerx)
            self.speed_x *= -1
        elif self.rect.right >= screen_width:
            self.rect.right = screen_width
            self.x = float(self.rect.centerx)
            self.speed_x *= -1

        if self.rect.top <= 0:
            self.rect.top = 0
            self.y = float(self.rect.centery)
            self.speed_y *= -1