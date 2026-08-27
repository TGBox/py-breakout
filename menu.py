# menu.py
from pygame import Rect, Surface
import pygame
import os
import random
import math
from settings import *

class Button:
    """Universelle Button-Klasse für das Hauptmenü"""
    def __init__(self, x: int, y: int, width: int, height: int, text: str, base_color: tuple[int, int, int], hover_color: tuple[int, int, int], text_color: tuple[int, int, int] = WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = base_color
        self.font = pygame.font.SysFont(None, 28, bold=True)

    def draw(self, screen: Surface):
        # Zeichnet ein abgerundetes Rechteck mit weißem Rahmen
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, width=2, border_radius=8)
        
        # Text rendern und zentrieren
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos: tuple[float, float]):
        if self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
            return True
        self.current_color = self.base_color
        return False


class MainMenu:
    """Das interaktive Hauptmenü mit dynamischer Layoutanpassung"""
    def __init__(self):
        b_width, b_height = 280, 38
        
        # Alle Buttons mit ihren Farbstilen anlegen
        self.buttons = {
            "PLAY":         Button(0, 0, b_width, b_height, "Spiel Starten", (50, 150, 50), (70, 200, 70)),
            "LEVEL_SELECT": Button(0, 0, b_width, b_height, "Level Auswählen", (40, 100, 180), (60, 130, 230)),
            "DIFFICULTY":   Button(0, 0, b_width, b_height, "Schwierigkeit: Normal", (200, 140, 40), (230, 170, 60)),
            "EDITOR":       Button(0, 0, b_width, b_height, "Level Editor", (120, 50, 150), (160, 70, 200)),
            "FULLSCREEN":   Button(0, 0, b_width, b_height, "Vollbild: Aus", (0, 130, 140), (0, 180, 190)),
            "HIGHSCORE":    Button(0, 0, b_width, b_height, "Highscores", (33, 33, 33), (133, 133, 133)),
            "RESET":        Button(0, 0, b_width, b_height, "Fortschritt Löschen", (160, 50, 50), (210, 70, 70)),
            "QUIT":         Button(0, 0, b_width, b_height, "Beenden", (70, 70, 70), (100, 100, 100)),
        }
        
        self.title_font = pygame.font.SysFont(None, 54, bold=True)
        self.info_font = pygame.font.SysFont(None, 22)

    def set_difficulty_label(self, difficulty_name: str):
        label = DIFFICULTY_SETTINGS.get(difficulty_name, {}).get("label", "Normal")
        self.buttons["DIFFICULTY"].text = f"Schwierigkeit: {label}"

    def update_layout(self, screen_w: int, screen_h: int, is_fullscreen: bool):
        b_width, b_height = 280, 38
        spacing = 46
        start_y = max(140, screen_h // 2 - (len(self.buttons) * spacing) // 2 + 20)
        center_x = screen_w // 2 - b_width // 2

        order = ["PLAY", "LEVEL_SELECT", "DIFFICULTY", "EDITOR", "FULLSCREEN", "HIGHSCORE", "RESET", "QUIT"]
        for idx, key in enumerate(order):
            btn = self.buttons[key]
            btn.rect.x = center_x
            btn.rect.y = start_y + idx * spacing

        self.buttons["FULLSCREEN"].text = "Vollbild: An" if is_fullscreen else "Vollbild: Aus"

    def draw(self, screen: Surface, unlocked_level: int, is_fullscreen: bool = False):
        screen_w, screen_h = screen.get_width(), screen.get_height()
        self.update_layout(screen_w, screen_h, is_fullscreen)

        # Titel
        title_surf = self.title_font.render("BREAKOUT CHAMPION", True, YELLOW)
        title_rect = title_surf.get_rect(center=(screen_w // 2, max(35, screen_h // 2 - 220)))
        screen.blit(title_surf, title_rect)
        
        # Info über Fortschritt
        info_surf = self.info_font.render(f"Freigeschaltete Level: {unlocked_level}", True, (180, 180, 180))
        info_rect = info_surf.get_rect(center=(screen_w // 2, title_rect.bottom + 15))
        screen.blit(info_surf, info_rect)
        
        # Alle Buttons zeichnen
        for button in self.buttons.values():
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event):
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
    """Levelauswahl - dynamisch skaliert mit Zurück-Button"""
    def __init__(self, screen: Surface):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.title_font = pygame.font.SysFont(None, 54, bold=True)
        self.levels: list[str] = []
        self.detect_levels()
        self.buttons: list[tuple[Rect, int, bool]] = []
        self.back_btn_rect = pygame.Rect(0, 0, 200, 45)

    def detect_levels(self):
        if os.path.exists("levels"):
            files = os.listdir("levels")
            level_files = [f for f in files if f.startswith("Level") and f.endswith(".txt")]
            self.levels = sorted(level_files, key=lambda x: int(''.join(filter(str.isdigit, x))))
        
        if not self.levels:
            self.levels = ["level1.txt"]

    def draw(self, unlocked_level: int):
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        
        self.detect_levels()  
        self.buttons.clear()
        
        title_text = self.title_font.render("BREAKOUT - LEVELAUSWAHL", True, YELLOW)
        self.screen.blit(title_text, (screen_w // 2 - title_text.get_width() // 2, 40))
        
        btn_w, btn_h = 130, 80
        gap_x, gap_y = 30, 30
        cols = max(1, (screen_w - 60) // (btn_w + gap_x))
        
        total_grid_w = cols * btn_w + (cols - 1) * gap_x
        start_x = (screen_w - total_grid_w) // 2
        start_y = 120
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Level-Grid zeichnen
        for idx, _level_file in enumerate(self.levels):
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

        # --- ZURÜCK-BUTTON ZEICHNEN ---
        self.back_btn_rect = pygame.Rect(screen_w // 2 - 100, screen_h - 70, 200, 45)
        if self.back_btn_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, (100, 100, 100), self.back_btn_rect, border_radius=8)
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.back_btn_rect, border_radius=8)
            
        pygame.draw.rect(self.screen, WHITE, self.back_btn_rect, width=2, border_radius=8)
        
        back_txt = self.font.render("Zurück", True, WHITE)
        self.screen.blit(back_txt, (self.back_btn_rect.centerx - back_txt.get_width() // 2, 
                                    self.back_btn_rect.centery - back_txt.get_height() // 2))

    def handle_click(self, mouse_pos: tuple[float, float]):
        if self.back_btn_rect.collidepoint(mouse_pos):
            return "BACK"
            
        for rect, level_num, is_unlocked in self.buttons:
            if rect.collidepoint(mouse_pos) and is_unlocked:
                return level_num
        return None