# menu.py
import pygame
import os
from settings import *

class LevelSelectionMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.title_font = pygame.font.SysFont(None, 60)
        
        # Dynamisch zählen, wie viele Level existieren
        self.levels = []
        self.detect_levels()
        
        # Speicher für die Buttons (wichtig für die Klick-Erkennung)
        self.buttons = []

    def detect_levels(self):
        # Liest den Ordner aus und filtert nach levelX.txt
        if os.path.exists("levels"):
            files = os.listdir("levels")
            level_files = [f for f in files if f.startswith("Level") and f.endswith(".txt")]
            # Sortiert sie numerisch (level1, level2, level10 etc.)
            self.levels = sorted(level_files, key=lambda x: int(''.join(filter(str.isdigit, x))))
        
        if not self.levels:
            self.levels = ["level1.txt"] # Fallback, falls der Ordner leer ist

    def draw(self, unlocked_level):
        self.detect_levels()  # NEU: Scannt den Ordner bei jedem Frame live nach Dateien!
        self.buttons.clear()
        
        # Titel zeichnen
        title_text = self.title_font.render("BREAKOUT - LEVELAUSWAHL", True, YELLOW)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 60))
        
        # Grid-Einstellungen für die Buttons
        btn_w, btn_h = 130, 90
        start_x = 90
        start_y = 180
        gap_x, gap_y = 40, 40
        cols = 4 # 4 Buttons pro Reihe
        
        mouse_pos = pygame.mouse.get_pos()
        
        for idx, level_file in enumerate(self.levels):
            level_num = idx + 1
            is_unlocked = level_num <= unlocked_level
            
            # Position im Raster berechnen
            col = idx % cols
            row = idx // cols
            x = start_x + col * (btn_w + gap_x)
            y = start_y + row * (btn_h + gap_y)
            
            rect = pygame.Rect(x, y, btn_w, btn_h)
            # Speichern für das Event-Handling
            self.buttons.append((rect, level_num, is_unlocked))
            
            # Button zeichnen basierend auf Zustand (Freigeschaltet / Gesperrt / Hover)
            if is_unlocked:
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(self.screen, GREEN, rect, border_radius=8) # Hover-Effekt
                else:
                    pygame.draw.rect(self.screen, BLUE, rect, border_radius=8)
                text_color = WHITE
            else:
                pygame.draw.rect(self.screen, (70, 70, 70), rect, border_radius=8) # Grau für gesperrt
                text_color = (130, 130, 130)
            
            # Text auf dem Button platzieren
            txt = self.font.render(f"Level {level_num}", True, text_color)
            self.screen.blit(txt, (x + btn_w//2 - txt.get_width()//2, y + btn_h//2 - txt.get_height()//2))
            
            # Kleiner "Gesperrt"-Hinweis
            if not is_unlocked:
                lock_font = pygame.font.SysFont(None, 20)
                lock_txt = lock_font.render("X Gesperrt", True, RED)
                self.screen.blit(lock_txt, (x + btn_w//2 - lock_txt.get_width()//2, y + btn_h - 22))

    def handle_click(self, mouse_pos):
        # Prüft, ob ein freigeschaltetes Level angeklickt wurde
        for rect, level_num, is_unlocked in self.buttons:
            if rect.collidepoint(mouse_pos) and is_unlocked:
                return level_num
        return None