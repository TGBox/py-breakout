# editor.py
from typing import Any
import pygame
import os
from settings import *

class LevelEditor:
    def __init__(self, screen: pygame.Surface|None = None):
        # Erkennen, ob der Editor im Spiel eingebettet ist oder alleine läuft
        self.embedded = screen is not None
        
        if self.embedded:
            self.screen: pygame.Surface = screen # type: ignore
        else:
            # Nur ausführen, wenn die editor.py separat gestartet wird
            pygame.init()
            self.screen = pygame.display.set_mode((DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT), pygame.RESIZABLE)
            pygame.display.set_caption("Breakout - Level Editor")
            self.clock = pygame.time.Clock()
        
        # Grid-Einstellungen (Passend zur LevelManager-Logik)
        self.cols = 10
        self.rows = 10  # Maximale vertikale Reihen für Blöcke
        
        # Leeres Raster initialisieren (0 = Leer)
        self.grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Aktuell ausgewählter Block-Typ zum Platzieren
        self.current_type = "1"
        
        self.types: dict[str, dict[str, tuple[int, int, int] | str]] = {
            "0": {"color": BLUE, "label": "Radiergummi / Leer (Taste 0)"},
            "1": {"color": YELLOW, "label": "Normaler Block (Taste 1)"},
            "2": {"color": ORANGE_YELLOW, "label": "Starker Block (2 Leben) (Taste 2)"},
            "3": {"color": ORANGE, "label": "Starker Block (3 Leben) (Taste 3)"},
            "4": {"color": REDDISH_ORANGE, "label": "Starker Block (4 Leben) (Taste 4)"},
            "5": {"color": RED, "label": "Starker Block (5 Leben) (Taste 5)"},
            "P": {"color": GREEN, "label": "PowerUp-Block (Taste P)"},
            "B": {"color": (220, 40, 40), "label": "Bomben-Block (Taste B)"},
            "X": {"color": (100, 100, 115), "label": "Stahl-Block (Taste X)"},
            "T": {"color": (140, 30, 210), "label": "Portal-Block (Taste T)"},
            "M": {"color": (255, 170, 0), "label": "Beweglicher Block (Taste M)"},
            "K": {"color": (255, 215, 0), "label": "Boss / Endgegner (Taste K)"}
        }
        
        self.font = pygame.font.SysFont(None, 22)
        self.running = True

    @property
    def block_width(self) -> int:
        return self.screen.get_width() // max(1, self.cols)

    @property
    def block_height(self) -> int:
        max_h = int(self.screen.get_height() * 0.48)
        return max(12, max_h // max(1, self.rows))

    def set_grid_size(self, new_cols: int, new_rows: int):
        new_cols = max(5, min(35, new_cols))
        new_rows = max(5, min(30, new_rows))
        
        new_grid = [["0" for _ in range(new_cols)] for _ in range(new_rows)]
        for r in range(min(self.rows, new_rows)):
            for c in range(min(self.cols, new_cols)):
                new_grid[r][c] = self.grid[r][c]
                
        self.cols = new_cols
        self.rows = new_rows
        self.grid = new_grid

    def run(self):
        """Wird NUR genutzt, wenn die editor.py eigenständig gestartet wird!"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                self.handle_event(event)
                
            self.update()
            self.draw()
            self.clock.tick(60)

    def handle_event(self, event: pygame.event.Event):
        """Verarbeitet EINZELNE Events aus der Hauptschleife (wichtig fürs Hauptspiel)"""
        if event.type == pygame.KEYDOWN:
            # Typen-Auswahl per Tastatur
            if event.key == pygame.K_1: self.current_type = "1"
            if event.key == pygame.K_2: self.current_type = "2"
            if event.key == pygame.K_3: self.current_type = "3"
            if event.key == pygame.K_4: self.current_type = "4"
            if event.key == pygame.K_5: self.current_type = "5"
            if event.key == pygame.K_p: self.current_type = "P"
            if event.key == pygame.K_b: self.current_type = "B"
            if event.key == pygame.K_x: self.current_type = "X"
            if event.key == pygame.K_t: self.current_type = "T"
            if event.key == pygame.K_m: self.current_type = "M"
            if event.key == pygame.K_d: self.current_type = "D"
            if event.key == pygame.K_k: self.current_type = "K"
            if event.key in (pygame.K_b, pygame.K_e): self.current_type = "B"
            if event.key in (pygame.K_x, pygame.K_u): self.current_type = "X"
            if event.key == pygame.K_0: self.current_type = "0"
            
            # Grid-Größe ändern
            if event.key == pygame.K_RIGHT:
                self.set_grid_size(self.cols + 1, self.rows)
            if event.key == pygame.K_LEFT:
                self.set_grid_size(self.cols - 1, self.rows)
            if event.key == pygame.K_UP:
                self.set_grid_size(self.cols, self.rows - 1)
            if event.key == pygame.K_DOWN:
                self.set_grid_size(self.cols, self.rows + 1)
            
            # Speichern per S-Taste
            if event.key == pygame.K_s:
                self.save_level()

    def update(self):
        # Mausklicks kontinuierlich verarbeiten (für flüssiges Malen)
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] or mouse_buttons[2]:
            mx, my = pygame.mouse.get_pos()
            
            col = mx // self.block_width
            row = (my - 50) // self.block_height
            
            if 0 <= col < self.cols and 0 <= row < self.rows:
                if mouse_buttons[0]:
                    self.grid[row][col] = self.current_type
                elif mouse_buttons[2]:
                    self.grid[row][col] = "0"

    def save_level(self):
        if not os.path.exists('levels'):
            os.makedirs('levels')
            
        existing = [f for f in os.listdir('levels') if f.startswith('Level') and f.endswith('.txt')]
        max_num = 0
        for f in existing:
            try:
                num = int(f.replace('Level', '').replace('.txt', ''))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
                
        new_num = max_num + 1
        if new_num <= 9:
            filename = f"Level00{new_num}.txt"
        elif new_num <= 99:
            filename = f"Level0{new_num}.txt"
        else:
            filename = f"Level{new_num}.txt"
            
        filepath = os.path.join('levels', filename)
        with open(filepath, 'w') as f:
            for row in self.grid:
                f.write("".join(row) + "\n")
                
        print(f"[Editor] Level erfolgreich gespeichert unter: {filepath}")

    def draw(self):
        self.screen.fill(DARK_GREY)
        sw, sh = self.screen.get_width(), self.screen.get_height()
        
        # Grid zeichnen
        for r in range(self.rows):
            for c in range(self.cols):
                b_type = self.grid[r][c]
                rect = pygame.Rect(c * self.block_width, 50 + r * self.block_height, self.block_width, self.block_height)
                
                if b_type != "0":
                    color = self.types.get(b_type, {}).get("color", WHITE) # type: ignore
                    pygame.draw.rect(self.screen, color, rect) # type: ignore
                    pygame.draw.rect(self.screen, BLACK, rect, 1)
                else:
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                    
        # UI & Anleitung
        info_text = f"Werkzeug: {self.types.get(self.current_type, {}).get('label', 'Unbekannt')} | Grid: {self.cols}x{self.rows}"
        txt_surf = self.font.render(info_text, True, WHITE)
        self.screen.blit(txt_surf, (10, 15))
        
        help_text = "Tasten 1-5, P, B, X, T, M, K | 0=Löschen | Pfeile=Raster (+/-) | S=Speichern | ESC=Hauptmenü"
        help_surf = self.font.render(help_text, True, YELLOW)
        self.screen.blit(help_surf, (10, sh - 30))

if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()