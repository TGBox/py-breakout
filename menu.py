# menu.py
import pygame
import os
import random
import math
from settings import *

class Button:
    """Universelle Button-Klasse für das Hauptmenü"""
    def __init__(self, x, y, width, height, text, base_color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = base_color
        self.font = pygame.font.SysFont(None, 28, bold=True)

    def draw(self, screen):
        # Zeichnet ein abgerundetes Rechteck mit weißem Rahmen
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, width=2, border_radius=8)
        
        # Text rendern und zentrieren
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
            return True
        self.current_color = self.base_color
        return False


class MainMenu:
    """Das neue, interaktive Hauptmenü"""
    def __init__(self):
        # Nutzt direkt die Konstanten aus deiner settings.py
        b_width, b_height = 280, 45
        start_y = 200
        spacing = 60
        center_x = SCREEN_WIDTH // 2 - b_width // 2
        
        # Alle Buttons mit ihren Farbstilen anlegen
        self.buttons = {
            "PLAY":         Button(center_x, start_y,             b_width, b_height, "Spiel Starten", (50, 150, 50), (70, 200, 70)),
            "LEVEL_SELECT": Button(center_x, start_y + spacing,     b_width, b_height, "Level Auswählen", (40, 100, 180), (60, 130, 230)),
            "EDITOR":       Button(center_x, start_y + spacing * 2, b_width, b_height, "Level Editor", (120, 50, 150), (160, 70, 200)),
            "RESET":        Button(center_x, start_y + spacing * 3, b_width, b_height, "Fortschritt Löschen", (160, 50, 50), (210, 70, 70)),
            "QUIT":         Button(center_x, start_y + spacing * 4, b_width, b_height, "Beenden", (70, 70, 70), (100, 100, 100))
        }
        
        self.title_font = pygame.font.SysFont(None, 54, bold=True)
        self.info_font = pygame.font.SysFont(None, 22)

    def draw(self, screen, unlocked_level):
        # Titel (Nutzt dein gelb aus den Settings)
        title_surf = self.title_font.render("BREAKOUT CHAMPION", True, YELLOW)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title_surf, title_rect)
        
        # Info über Fortschritt
        info_surf = self.info_font.render(f"Freigeschaltete Level: {unlocked_level}", True, (180, 180, 180))
        info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, 140))
        screen.blit(info_surf, info_rect)
        
        # Alle Buttons zeichnen
        for button in self.buttons.values():
            button.draw(screen)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons.values():
                button.check_hover(mouse_pos)
                
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action_name, button in self.buttons.items():
                if button.rect.collidepoint(mouse_pos):
                    return action_name
                    
        return None


class LevelSelectionMenu:
    """Deine bestehende Levelauswahl – jetzt mit Zurück-Button"""
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.title_font = pygame.font.SysFont(None, 60)
        self.levels = []
        self.detect_levels()
        self.buttons = []
        
        # NEU: Der Zurück-Button wird unten in der Mitte platziert
        self.back_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 45)

    def detect_levels(self):
        if os.path.exists("levels"):
            files = os.listdir("levels")
            level_files = [f for f in files if f.startswith("Level") and f.endswith(".txt")]
            self.levels = sorted(level_files, key=lambda x: int(''.join(filter(str.isdigit, x))))
        
        if not self.levels:
            self.levels = ["level1.txt"]

    def draw(self, unlocked_level):
        self.detect_levels()  
        self.buttons.clear()
        
        title_text = self.title_font.render("BREAKOUT - LEVELAUSWAHL", True, YELLOW)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 60))
        
        btn_w, btn_h = 130, 90
        start_x = 90
        start_y = 180
        gap_x, gap_y = 40, 40
        cols = 4 
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Level-Grid zeichnen
        for idx, level_file in enumerate(self.levels):
            level_num = idx + 1
            is_unlocked = level_num <= unlocked_level
            
            col = idx % cols
            row = idx // cols
            x = start_x + col * (btn_w + gap_x)
            y = start_y + row * (btn_h + gap_y)
            
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.buttons.append((rect, level_num, is_unlocked))
            
            if is_unlocked:
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(self.screen, GREEN, rect, border_radius=8) 
                else:
                    pygame.draw.rect(self.screen, BLUE, rect, border_radius=8)
                text_color = WHITE
            else:
                pygame.draw.rect(self.screen, (70, 70, 70), rect, border_radius=8) 
                text_color = (130, 130, 130)
            
            txt = self.font.render(f"Level {level_num}", True, text_color)
            self.screen.blit(txt, (x + btn_w//2 - txt.get_width()//2, y + btn_h//2 - txt.get_height()//2))
            
            if not is_unlocked:
                lock_font = pygame.font.SysFont(None, 20)
                lock_txt = lock_font.render("X Gesperrt", True, RED)
                self.screen.blit(lock_txt, (x + btn_w//2 - lock_txt.get_width()//2, y + btn_h - 22))

        # --- NEU: ZURÜCK-BUTTON ZEICHNEN ---
        if self.back_btn_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, (100, 100, 100), self.back_btn_rect, border_radius=8) # Helleres Grau bei Hover
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.back_btn_rect, border_radius=8) # Dunkles Grau standardmäßig
            
        pygame.draw.rect(self.screen, WHITE, self.back_btn_rect, width=2, border_radius=8) # Weißer Rahmen
        
        back_txt = self.font.render("Zurück", True, WHITE)
        self.screen.blit(back_txt, (self.back_btn_rect.centerx - back_txt.get_width() // 2, 
                                    self.back_btn_rect.centery - back_txt.get_height() // 2))

    def handle_click(self, mouse_pos):
        # NEU: Erst prüfen, ob der Zurück-Knopf angeklickt wurde
        if self.back_btn_rect.collidepoint(mouse_pos):
            return "BACK"
            
        # Danach die Level-Buttons prüfen
        for rect, level_num, is_unlocked in self.buttons:
            if rect.collidepoint(mouse_pos) and is_unlocked:
                return level_num
        return None