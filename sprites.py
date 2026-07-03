import pygame
from settings import *

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, block_type):
        super().__init__()
        self.block_type = block_type
        self.width = 60
        self.height = 30
        
        # Grafik-Oberfläche für den Block erstellen
        self.image = pygame.Surface((self.width, self.height))
        
        # Standardwerte
        self.health = 1
        self.is_powerup = False
        
        # Farbe und Eigenschaften basierend auf dem Typ setzen
        if self.block_type == '1':
            self.image.fill(GREEN)
        elif self.block_type == '2':
            self.image.fill(RED)
            self.health = 2 # Braucht zwei Treffer
        elif self.block_type == 'P':
            self.image.fill(BLUE)
            self.is_powerup = True # Lässt später ein Power-Up fallen
            
        # Hitbox (Rect) setzen und positionieren
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        

class Paddle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = 100
        self.height = 15
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(WHITE) # Nutzt WHITE aus settings.py
        
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.speed = 8

    def update(self):
        # Steuerung
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            
        # Randbegrenzung (Paddle darf nicht aus dem Bildschirm fliegen)
        if self.rect.left < 0: 
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: 
            self.rect.right = SCREEN_WIDTH

# Ersetze die Ball-Klasse in sprites.py mit dieser Version:

class Ball(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_x=5, speed_y=-5):
        super().__init__()
        self.radius = 8
        self.is_piercing = False
        
        # Grafik erstellen
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (self.radius, self.radius), self.radius)
        
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        self.speed_x = speed_x
        self.speed_y = speed_y

    def set_size(self, new_radius):
        # Ändert die Größe des Balls dynamisch
        self.radius = new_radius
        old_center = self.rect.center
        self.image: pygame.Surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        color = RED if self.is_piercing else YELLOW
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=old_center)

    def set_piercing(self, piercing):
        self.is_piercing = piercing
        # Optisches Feedback: Ein stechender Ball wird feurig rot
        color = RED if piercing else YELLOW
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)

    def update(self):
        # Bewegung anwenden
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # ==========================================
        # KORRIGIERTE WAND-KOLLISIONEN (mit Reset)
        # ==========================================
        
        # Kollision mit der linken Wand
        if self.rect.left <= 0:
            self.rect.left = 0          # Setzt den Ball exakt an den linken Rand
            self.speed_x *= -1          # Richtung umkehren
            
        # Kollision mit der rechten Wand
        elif self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH  # Setzt den Ball exakt an den rechten Rand
            self.speed_x *= -1              # Richtung umkehren
            
        # Kollision mit der Decke
        if self.rect.top <= 0:
            self.rect.top = 0           # Setzt den Ball exakt unter die Decke
            self.speed_y *= -1          # Richtung umkehren
            
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, effect_type):
        super().__init__()
        self.effect_type = effect_type # z.B. "expand_paddle", "shrink_paddle", "speed_ball"
        self.width = 25
        self.height = 15
        self.image = pygame.Surface((self.width, self.height))
        
        # Optische Unterscheidung: Positiv (Grün), Negativ (Rot)
        if effect_type in ["expand_paddle", "slow_time", "bigger_ball"]:
            self.image.fill(GREEN)
        else:
            self.image.fill(RED)
            
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 3 # Fallgeschwindigkeit

    def update(self):
        # Das Power-Up fällt nach unten
        self.rect.y += self.speed
        # Wenn es den Bildschirm verlässt, löscht es sich selbst
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()