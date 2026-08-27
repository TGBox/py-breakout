# editor.py
from typing import Any
import pygame
import os
from settings import *

class LevelEditor:
    def __init__(self, screen: pygame.Surface | None = None):
        # Erkennen, ob der Editor im Spiel eingebettet ist oder alleine läuft
        self.embedded = screen is not None
        
        if self.embedded:
            self.screen: pygame.Surface = screen # type: ignore
        else:
            pygame.init()
            self.screen = pygame.display.set_mode((DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT), pygame.RESIZABLE)
            pygame.display.set_caption("Breakout - Level Editor")
            self.clock = pygame.time.Clock()
        
        # Grid-Einstellungen
        self.cols = 15
        self.rows = 12
        self.grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Aktuell ausgewählter Block-Typ zum Platzieren
        self.current_type = "1"
        self.editing_filename: str | None = None
        self.available_levels: list[str] = []
        self.selected_level_idx: int = 0
        self.refresh_level_list()
        
        self.types: dict[str, dict[str, tuple[int, int, int] | str]] = {
            "0": {"color": BLUE, "label": "Radiergummi (0)"},
            "1": {"color": YELLOW, "label": "Normal 1 HP (1)"},
            "2": {"color": ORANGE_YELLOW, "label": "Stark 2 HP (2)"},
            "3": {"color": ORANGE, "label": "Stark 3 HP (3)"},
            "4": {"color": REDDISH_ORANGE, "label": "Stark 4 HP (4)"},
            "5": {"color": RED, "label": "Stark 5 HP (5)"},
            "P": {"color": GREEN, "label": "PowerUp (P)"},
            "D": {"color": DARK_PURPLE, "label": "PowerDown (D)"},
            "B": {"color": (220, 40, 40), "label": "Bombe (B)"},
            "X": {"color": (100, 100, 115), "label": "Stahl (X)"},
            "T": {"color": (140, 30, 210), "label": "Portal (T)"},
            "M": {"color": (255, 170, 0), "label": "Beweglich (M)"},
            "K": {"color": (255, 215, 0), "label": "Boss (K)"}
        }
        
        self.font = pygame.font.SysFont(None, 20)
        self.btn_font = pygame.font.SysFont(None, 20, bold=True)
        self.running = True
        
        # Statusmeldung für Feedback
        self.status_msg = "Level-Editor bereit. Wähle Werkzeuge oder lade ein vorhandenes Level."
        self.status_timer = 0

    def set_status(self, msg: str):
        self.status_msg = msg
        self.status_timer = pygame.time.get_ticks()

    def refresh_level_list(self):
        if os.path.exists('levels'):
            files = [f for f in os.listdir('levels') if f.startswith('Level') and f.endswith('.txt')]
            files.sort()
            self.available_levels = files
            if files and self.selected_level_idx >= len(files):
                self.selected_level_idx = 0
        else:
            self.available_levels = []

    @property
    def grid_top(self) -> int:
        return 82

    @property
    def block_width(self) -> int:
        return self.screen.get_width() // max(1, self.cols)

    @property
    def block_height(self) -> int:
        max_h = int((self.screen.get_height() - self.grid_top - 45) * 0.95)
        return max(12, max_h // max(1, self.rows))

    def set_grid_size(self, new_cols: int, new_rows: int, center: bool = True):
        new_cols = max(5, min(40, new_cols))
        new_rows = max(5, min(30, new_rows))
        
        active_blocks = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != "0":
                    active_blocks.append((r, c, self.grid[r][c]))

        if center and active_blocks:
            min_r = min(r for r, c, _ in active_blocks)
            max_r = max(r for r, c, _ in active_blocks)
            min_c = min(c for r, c, _ in active_blocks)
            max_c = max(c for r, c, _ in active_blocks)
            
            h = max_r - min_r + 1
            w = max_c - min_c + 1
            
            target_r = max(0, (new_rows - h) // 2)
            target_c = max(0, (new_cols - w) // 2)
            
            new_grid = [["0" for _ in range(new_cols)] for _ in range(new_rows)]
            for r, c, val in active_blocks:
                new_r = target_r + (r - min_r)
                new_c = target_c + (c - min_c)
                if 0 <= new_r < new_rows and 0 <= new_c < new_cols:
                    new_grid[new_r][new_c] = val
                    
            self.cols = new_cols
            self.rows = new_rows
            self.grid = new_grid
            self.set_status(f"Rastergröße angepasst: {self.cols}x{self.rows} (Inhalt zentriert)")
            return

        new_grid = [["0" for _ in range(new_cols)] for _ in range(new_rows)]
        for r in range(min(self.rows, new_rows)):
            for c in range(min(self.cols, new_cols)):
                new_grid[r][c] = self.grid[r][c]
                
        self.cols = new_cols
        self.rows = new_rows
        self.grid = new_grid
        self.set_status(f"Rastergröße angepasst: {self.cols}x{self.rows}")

    def center_grid(self):
        """Zentriert alle vorhandenen Blöcke genau in der Mitte des aktuellen Rasters."""
        active_coords = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] != "0"]
        if not active_coords:
            self.set_status("Raster ist leer – nichts zu zentrieren.")
            return
            
        min_r = min(r for r, c in active_coords)
        max_r = max(r for r, c in active_coords)
        min_c = min(c for r, c in active_coords)
        max_c = max(c for r, c in active_coords)
        
        h = max_r - min_r + 1
        w = max_c - min_c + 1
        
        target_r = max(0, (self.rows - h) // 2)
        target_c = max(0, (self.cols - w) // 2)
        
        new_grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        for r, c in active_coords:
            new_r = target_r + (r - min_r)
            new_c = target_c + (c - min_c)
            if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
                new_grid[new_r][new_c] = self.grid[r][c]
                
        self.grid = new_grid
        self.set_status("Blöcke erfolgreich in der Mitte zentriert!")

    def load_selected_level(self):
        self.refresh_level_list()
        if not self.available_levels:
            self.set_status("Keine Level-Dateien im Ordner 'levels' vorhanden.")
            return
            
        filename = self.available_levels[self.selected_level_idx]
        filepath = os.path.join('levels', filename)
        
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            
        if not lines:
            self.set_status(f"Datei '{filename}' ist leer.")
            return
            
        orig_cols = max(len(l) for l in lines)
        orig_rows = len(lines)
        
        # Mindestens 15 Spalten und 12 Zeilen für Erweiterungen bieten
        self.cols = max(15, orig_cols)
        self.rows = max(12, orig_rows)
        self.grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Karte zentriert in das erweiterte Raster einfügen
        target_r = (self.rows - orig_rows) // 2
        target_c = (self.cols - orig_cols) // 2
        
        for r, line in enumerate(lines):
            for c, char in enumerate(line):
                if target_r + r < self.rows and target_c + c < self.cols:
                    self.grid[target_r + r][target_c + c] = char
                    
        self.editing_filename = filename
        self.set_status(f"Level '{filename}' geladen & zentriert ({self.cols}x{self.rows} Raster).")

    def create_new_level(self):
        self.grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        self.editing_filename = None
        self.set_status("Neues leeres Level erstellt.")

    def save_level(self):
        if not os.path.exists('levels'):
            os.makedirs('levels')
            
        if self.editing_filename:
            filepath = os.path.join('levels', self.editing_filename)
        else:
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
            self.editing_filename = filename

        with open(filepath, 'w') as f:
            for row in self.grid:
                f.write("".join(row) + "\n")
                
        self.refresh_level_list()
        self.set_status(f"Erfolgreich gespeichert unter: {filepath}")
        print(f"[Editor] Level gespeichert: {filepath}")

    def run(self):
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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if my < self.grid_top:
                # Klick auf UI-Buttons in der oberen Leiste
                if self.btn_col_minus.collidepoint((mx, my)):
                    self.set_grid_size(self.cols - 1, self.rows)
                elif self.btn_col_plus.collidepoint((mx, my)):
                    self.set_grid_size(self.cols + 1, self.rows)
                elif self.btn_row_minus.collidepoint((mx, my)):
                    self.set_grid_size(self.cols, self.rows - 1)
                elif self.btn_row_plus.collidepoint((mx, my)):
                    self.set_grid_size(self.cols, self.rows + 1)
                elif self.btn_center.collidepoint((mx, my)):
                    self.center_grid()
                elif self.btn_prev_lvl.collidepoint((mx, my)):
                    if self.available_levels:
                        self.selected_level_idx = (self.selected_level_idx - 1) % len(self.available_levels)
                elif self.btn_next_lvl.collidepoint((mx, my)):
                    if self.available_levels:
                        self.selected_level_idx = (self.selected_level_idx + 1) % len(self.available_levels)
                elif self.btn_load_lvl.collidepoint((mx, my)):
                    self.load_selected_level()
                elif self.btn_new_lvl.collidepoint((mx, my)):
                    self.create_new_level()
                elif self.btn_save_lvl.collidepoint((mx, my)):
                    self.save_level()

        if event.type == pygame.KEYDOWN:
            # Typen-Auswahl per Tastatur
            if event.key == pygame.K_1: self.current_type = "1"
            if event.key == pygame.K_2: self.current_type = "2"
            if event.key == pygame.K_3: self.current_type = "3"
            if event.key == pygame.K_4: self.current_type = "4"
            if event.key == pygame.K_5: self.current_type = "5"
            if event.key == pygame.K_p: self.current_type = "P"
            if event.key == pygame.K_d: self.current_type = "D"
            if event.key == pygame.K_b: self.current_type = "B"
            if event.key == pygame.K_x: self.current_type = "X"
            if event.key == pygame.K_t: self.current_type = "T"
            if event.key == pygame.K_m: self.current_type = "M"
            if event.key == pygame.K_k: self.current_type = "K"
            if event.key == pygame.K_0: self.current_type = "0"
            
            # Hotkeys für Editor-Funktionen
            if event.key == pygame.K_c:
                self.center_grid()
            if event.key == pygame.K_l:
                self.load_selected_level()
            if event.key == pygame.K_n:
                self.create_new_level()
            if event.key == pygame.K_s:
                self.save_level()
            
            # Grid-Größe ändern per Pfeiltasten
            if event.key == pygame.K_RIGHT:
                self.set_grid_size(self.cols + 1, self.rows)
            if event.key == pygame.K_LEFT:
                self.set_grid_size(self.cols - 1, self.rows)
            if event.key == pygame.K_UP:
                self.set_grid_size(self.cols, self.rows - 1)
            if event.key == pygame.K_DOWN:
                self.set_grid_size(self.cols, self.rows + 1)

    def update(self):
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] or mouse_buttons[2]:
            mx, my = pygame.mouse.get_pos()
            if my >= self.grid_top:
                col = mx // max(1, self.block_width)
                row = (my - self.grid_top) // max(1, self.block_height)
                
                if 0 <= col < self.cols and 0 <= row < self.rows:
                    if mouse_buttons[0]:
                        self.grid[row][col] = self.current_type
                    elif mouse_buttons[2]:
                        self.grid[row][col] = "0"

    def draw_button(self, rect: pygame.Rect, text: str, bg_color: tuple[int, int, int] = (60, 60, 70), text_color: tuple[int, int, int] = WHITE):
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
        pygame.draw.rect(self.screen, WHITE, rect, width=1, border_radius=4)
        txt_surf = self.btn_font.render(text, True, text_color)
        self.screen.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2, rect.centery - txt_surf.get_height() // 2))

    def draw(self):
        self.screen.fill(DARK_GREY)
        sw, sh = self.screen.get_width(), self.screen.get_height()
        
        # --- UI RECTS (Leiste oben) ---
        self.btn_col_minus = pygame.Rect(10, 10, 24, 24)
        self.btn_col_plus = pygame.Rect(38, 10, 24, 24)
        self.btn_row_minus = pygame.Rect(110, 10, 24, 24)
        self.btn_row_plus = pygame.Rect(138, 10, 24, 24)
        
        self.btn_center = pygame.Rect(190, 10, 85, 24)
        
        self.btn_prev_lvl = pygame.Rect(290, 10, 24, 24)
        self.btn_next_lvl = pygame.Rect(415, 10, 24, 24)
        self.btn_load_lvl = pygame.Rect(445, 10, 60, 24)
        self.btn_new_lvl = pygame.Rect(515, 10, 50, 24)
        self.btn_save_lvl = pygame.Rect(575, 10, 85, 24)
        
        # Top-Bar Hintergrund
        pygame.draw.rect(self.screen, (30, 30, 35), (0, 0, sw, self.grid_top))
        
        # Spalten & Zeilen Buttons zeichnen
        self.draw_button(self.btn_col_minus, "-")
        self.draw_button(self.btn_col_plus, "+")
        col_label = self.font.render(f"Spalten: {self.cols}", True, WHITE)
        self.screen.blit(col_label, (66, 15))

        self.draw_button(self.btn_row_minus, "-")
        self.draw_button(self.btn_row_plus, "+")
        row_label = self.font.render(f"Zeilen: {self.rows}", True, WHITE)
        self.screen.blit(row_label, (166, 15))

        self.draw_button(self.btn_center, "Zentrieren", bg_color=(50, 100, 150))

        # Level-Auswahl Buttons zeichnen
        self.draw_button(self.btn_prev_lvl, "<")
        lvl_name = self.available_levels[self.selected_level_idx] if self.available_levels else "Keine Level"
        lvl_label = self.font.render(lvl_name, True, YELLOW)
        self.screen.blit(lvl_label, (320, 15))
        self.draw_button(self.btn_next_lvl, ">")
        self.draw_button(self.btn_load_lvl, "Laden", bg_color=(40, 120, 40))
        self.draw_button(self.btn_new_lvl, "Neu")
        self.draw_button(self.btn_save_lvl, "Speichern", bg_color=(150, 50, 50))

        # Zeile 2 im Header: Aktuelles Werkzeug & Bearbeitungsstatus
        editing_str = f"Bearbeite: {self.editing_filename}" if self.editing_filename else "Neues Level"
        tool_str = f"Werkzeug: {self.types.get(self.current_type, {}).get('label', 'Unbekannt')}"
        info_surf = self.font.render(f"{tool_str}  |  {editing_str}", True, GREEN)
        self.screen.blit(info_surf, (10, 48))

        # Grid zeichnen
        for r in range(self.rows):
            for c in range(self.cols):
                b_type = self.grid[r][c]
                rect = pygame.Rect(c * self.block_width, self.grid_top + r * self.block_height, self.block_width, self.block_height)
                
                if b_type != "0":
                    color = self.types.get(b_type, {}).get("color", WHITE) # type: ignore
                    pygame.draw.rect(self.screen, color, rect) # type: ignore
                    pygame.draw.rect(self.screen, BLACK, rect, 1)
                else:
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                    
        # Untere Statusleiste & Anleitung
        pygame.draw.rect(self.screen, (25, 25, 30), (0, sh - 35, sw, 35))
        status_surf = self.font.render(self.status_msg, True, CYAN)
        self.screen.blit(status_surf, (10, sh - 28))
        
        help_text = "Hotkeys: 1-5, P, D, B, X, T, M, K | 0=Löschen | C=Zentrieren | L=Laden | S=Speichern | ESC=Hauptmenü"
        help_surf = self.font.render(help_text, True, (180, 180, 180))
        self.screen.blit(help_surf, (sw - help_surf.get_width() - 10, sh - 28))

if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()