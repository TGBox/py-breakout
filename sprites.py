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
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
            
        # Randbegrenzung (Paddle darf nicht aus dem Bildschirm fliegen)
        if self.rect.left < 0: 
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: 
            self.rect.right = SCREEN_WIDTH

# In sprites.py die Ball-Klasse ersetzen:

class Ball(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_x=5, speed_y=-5):
        super().__init__()
        self.radius = 8
        self.is_piercing = False
        
        # NEU: Standardmäßig ist der Ball erst einmal NICHT festgeklebt (wichtig für Multiball)
        self.attached = False 
        
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (self.radius, self.radius), self.radius)
        
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)


    def set_size(self, new_radius):
        self.radius = new_radius
        old_center = self.rect.center
        self.image: pygame.Surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        color = RED if self.is_piercing else YELLOW
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=old_center)
        # Wichtig: Nach Größenänderung die Float-Koordinaten neu abgleichen
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def set_piercing(self, piercing):
        self.is_piercing = piercing
        color = RED if piercing else YELLOW
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)

    # ANGEPASST: update() nimmt jetzt direkt den Zeitfaktor entgegen    
    def update(self, time_factor=1.0):
        # NEU: Wenn der Ball angeheftet ist, überspringen wir die Eigenbewegung!
        if self.attached:
            return
        # 1. Bewegung hochpräzise auf den Float-Variablen berechnen
        self.x += self.speed_x * time_factor
        self.y += self.speed_y * time_factor
        
        # 2. Erst JETZT den ganzzahligen Wert an das Rect für die Grafik übergeben
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # 3. Wand-Kollisionen (mit Float-Positionskorrektur!)
        if self.rect.left <= 0:
            self.rect.left = 0
            self.x = float(self.rect.x)  # Float-Speicher exakt mit Wand synchronisieren
            self.speed_x *= -1
        elif self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.x = float(self.rect.x)  # Float-Speicher exakt mit Wand synchronisieren
            self.speed_x *= -1
            
        if self.rect.top <= 0:
            self.rect.top = 0
            self.y = float(self.rect.y)  # Float-Speicher exakt mit Decke synchronisieren
            self.speed_y *= -1
            
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, powerup_type):
        super().__init__()
        self.effect_type = powerup_type
        self.size = 28  # Ein winziges bisschen größer für bessere Form-Erkennung
        
        # Detektiv-Log für das Terminal bleibt aktiv
        print(f"[PowerUp-Info] Typ '{self.effect_type}' ist gespawnt!")

        # CONFIG JETZT MIT ZUSÄTZLICHER "shape"-EIGENSCHAFT
        self.config = {
            # --- POSITIVE EFFEKTE (Kreise) ---
            "slow_time":     {"color": (50, 150, 255), "char": "S", "shape": "circle"},
            "bigger_ball":     {"color": (50, 10, 50), "char": "B", "shape": "circle"},
            "multiball":     {"color": (50, 230, 50),  "char": "M", "shape": "circle"},
            "expand_paddle": {"color": (50, 200, 200), "char": "W", "shape": "circle"},
            "piercing_shot":      {"color": (255, 215, 0),  "char": "P", "shape": "circle"},
            
            # --- NEGATIVE EFFEKTE (Dreiecke) ---
            "shrink_paddle": {"color": (255, 50, 50),  "char": "C", "shape": "triangle"},
            "speed_time":     {"color": (255, 100, 0),  "char": "F", "shape": "triangle"},
            "smaller_ball":     {"color": (255, 150, 0),  "char": "S", "shape": "triangle"},
        }
        
        # Fallback für Unbekanntes (wird als graues Viereck gezeichnet!)
        cfg = self.config.get(self.effect_type, {"color": (130, 130, 130), "char": "?", "shape": "square"})
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        radius = self.size // 2
        
        # Schrifteinstellungen vorbereiten
        font = pygame.font.SysFont(None, 18, bold=True)
        text_surf = font.render(cfg["char"], True, (0, 0, 0))
        
        # =======================================================
        # DYNAMISCHES ZEICHNEN JE NACH FORM
        # =======================================================
        if cfg["shape"] == "circle":
            # Positiv: Runder Kreis
            pygame.draw.circle(self.image, cfg["color"], (radius, radius), radius)
            pygame.draw.circle(self.image, (255, 255, 255), (radius, radius), radius, 2)
            text_rect = text_surf.get_rect(center=(radius, radius))
            
        elif cfg["shape"] == "triangle":
            # Negativ: Gefahren-Dreieck (Spitze zeigt nach unten)
            # Punkte: Oben-Links, Oben-Rechts, Unten-Mitte
            points = [(2, 2), (self.size - 2, 2), (radius, self.size - 2)]
            pygame.draw.polygon(self.image, cfg["color"], points)
            pygame.draw.polygon(self.image, (255, 255, 255), points, 2) # Weißer Rahmen
            
            # Text-Zentrierung für Dreiecke (leicht nach oben verschoben, weil es unten eng wird)
            text_rect = text_surf.get_rect(center=(radius, radius - 3))
            
        else:
            # Fallback / Unbekannt: Quadrat (Graues Fragezeichen)
            pygame.draw.rect(self.image, cfg["color"], (0, 0, self.size, self.size))
            pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.size, self.size), 2)
            text_rect = text_surf.get_rect(center=(radius, radius))

        # Text auf das Power-Up blitten
        self.image.blit(text_surf, text_rect)
        
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        self.speed_y = 3  

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()