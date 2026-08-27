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
        
        # Virtueller Controller-Cursor
        self.cursor_col = 0
        self.cursor_row = 0
        self.cursor_active = True
        
        # Undo / Redo Stacks
        self.undo_stack: list[list[list[str]]] = []
        self.redo_stack: list[list[list[str]]] = []
        
        # Templates
        self.templates = ["PYRAMID", "CHECKERBOARD", "FORTRESS", "DIAMOND"]
        self.current_template_idx = 0
        
        # Aktuell ausgewählter Block-Typ zum Platzieren
        self.current_type = "1"
        self.editing_filename: str | None = None
        self.available_levels: list[str] = []
        self.selected_level_idx: int = 0
        self.refresh_level_list()
        
        # Box-Fill Mode (Rechteck-Füllen)
        self.box_fill_mode = False
        self.drag_start: tuple[int, int] | None = None
        self.drag_current: tuple[int, int] | None = None
        self.drag_button: int = 1
        
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
        self.status_msg = "Level-Editor bereit. Strg+Z = Undo | Strg+Y = Redo | T = Template | F = Box-Fill."
        self.status_timer = 0

    def save_snapshot(self):
        snapshot = [row[:] for row in self.grid]
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 30:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            self.set_status("Nichts mehr zum Rückgängig machen.")
            return
        self.redo_stack.append([row[:] for row in self.grid])
        self.grid = self.undo_stack.pop()
        self.set_status("Änderung rückgängig gemacht (Undo).")

    def redo(self):
        if not self.redo_stack:
            self.set_status("Nichts mehr zum Wiederholen.")
            return
        self.undo_stack.append([row[:] for row in self.grid])
        self.grid = self.redo_stack.pop()
        self.set_status("Änderung wiederholt (Redo).")

    def apply_template(self):
        self.save_snapshot()
        t_name = self.templates[self.current_template_idx]
        self.current_template_idx = (self.current_template_idx + 1) % len(self.templates)
        
        self.grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        mid_c = self.cols // 2
        
        if t_name == "PYRAMID":
            for r in range(min(self.rows, 8)):
                start = max(0, mid_c - r)
                end = min(self.cols, mid_c + r + 1)
                b_type = str(min(5, r % 5 + 1))
                for c in range(start, end):
                    if 1 + r < self.rows and c < self.cols:
                        self.grid[1 + r][c] = b_type
                    
        elif t_name == "CHECKERBOARD":
            for r in range(1, min(self.rows - 1, 9)):
                for c in range(1, self.cols - 1):
                    if (r + c) % 2 == 0:
                        self.grid[r][c] = str((r % 5) + 1)
                        
        elif t_name == "FORTRESS":
            for r in range(1, min(self.rows - 1, 9)):
                for c in range(1, self.cols - 1):
                    if r in (1, 8) or c in (1, self.cols - 2):
                        self.grid[r][c] = "X"
                    elif r in (3, 6) or c in (3, self.cols - 4):
                        self.grid[r][c] = "B"
                    else:
                        self.grid[r][c] = "P"
                        
        elif t_name == "DIAMOND":
            mid_r = min(self.rows // 2, 5)
            for r in range(1, min(self.rows - 1, 10)):
                dist = abs(r - mid_r)
                width = max(1, mid_r - dist + 2)
                for c in range(max(0, mid_c - width), min(self.cols, mid_c + width + 1)):
                    self.grid[r][c] = "P" if dist == 0 else str(min(5, dist + 1))

        self.set_status(f"Template '{t_name}' angewendet!")

    def move_cursor(self, d_col: int, d_row: int):
        self.cursor_col = max(0, min(self.cols - 1, self.cursor_col + d_col))
        self.cursor_row = max(0, min(self.rows - 1, self.cursor_row + d_row))
        self.cursor_active = True

    def place_at_cursor(self):
        if 0 <= self.cursor_col < self.cols and 0 <= self.cursor_row < self.rows:
            self.save_snapshot()
            self.grid[self.cursor_row][self.cursor_col] = self.current_type
            self.set_status(f"Block '{self.current_type}' bei ({self.cursor_col},{self.cursor_row}) platziert.")

    def erase_at_cursor(self):
        if 0 <= self.cursor_col < self.cols and 0 <= self.cursor_row < self.rows:
            self.save_snapshot()
            self.grid[self.cursor_row][self.cursor_col] = "0"
            self.set_status(f"Block bei ({self.cursor_col},{self.cursor_row}) gelöscht.")

    def cycle_type(self, direction: int = 1):
        type_keys = list(self.types.keys())
        try:
            curr_idx = type_keys.index(self.current_type)
            next_idx = (curr_idx + direction) % len(type_keys)
            self.current_type = type_keys[next_idx]
            self.set_status(f"Werkzeug gewählt: {self.types[self.current_type]['label']}")
        except ValueError:
            self.current_type = "1"

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
        self.save_snapshot()
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
        self.save_snapshot()
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
        self.save_snapshot()
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
        
        self.cols = max(15, orig_cols)
        self.rows = max(12, orig_rows)
        self.grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        
        target_r = (self.rows - orig_rows) // 2
        target_c = (self.cols - orig_cols) // 2
        
        for r, line in enumerate(lines):
            for c, char in enumerate(line):
                if target_r + r < self.rows and target_c + c < self.cols:
                    self.grid[target_r + r][target_c + c] = char
                    
        self.editing_filename = filename
        self.set_status(f"Level '{filename}' geladen & zentriert ({self.cols}x{self.rows} Raster).")

    def create_new_level(self):
        self.save_snapshot()
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
        mx, my = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (1, 3):
                if my < self.grid_top:
                    # Klick auf UI-Buttons in der oberen Leiste
                    if event.button == 1:
                        if self.btn_col_minus.collidepoint((mx, my)):
                            self.set_grid_size(self.cols - 1, self.rows)
                        elif self.btn_col_plus.collidepoint((mx, my)):
                            self.set_grid_size(self.cols + 1, self.rows)
                        elif self.btn_row_minus.collidepoint((mx, my)):
                            self.set_grid_size(self.cols, self.rows - 1)
                        elif self.btn_row_plus.collidepoint((mx, my)):
                            self.set_grid_size(self.cols, self.rows + 1)
                        elif self.btn_box_fill.collidepoint((mx, my)):
                            self.box_fill_mode = not self.box_fill_mode
                            self.set_status(f"Box-Füllen Modus: {'AN' if self.box_fill_mode else 'AUS'}")
                        elif self.btn_center.collidepoint((mx, my)):
                            self.center_grid()
                        elif self.btn_template.collidepoint((mx, my)):
                            self.apply_template()
                        elif self.btn_undo.collidepoint((mx, my)):
                            self.undo()
                        elif self.btn_redo.collidepoint((mx, my)):
                            self.redo()
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
                else:
                    # Klick im Spielfeld -> Drag-Start für Einzelstift oder Box-Fill
                    col = mx // max(1, self.block_width)
                    row = (my - self.grid_top) // max(1, self.block_height)
                    if 0 <= col < self.cols and 0 <= row < self.rows:
                        self.save_snapshot()
                        self.cursor_col = col
                        self.cursor_row = row
                        self.drag_start = (col, row)
                        self.drag_current = (col, row)
                        self.drag_button = event.button

        elif event.type == pygame.MOUSEMOTION and self.drag_start:
            col = mx // max(1, self.block_width)
            row = (my - self.grid_top) // max(1, self.block_height)
            col = max(0, min(self.cols - 1, col))
            row = max(0, min(self.rows - 1, row))
            self.cursor_col = col
            self.cursor_row = row
            self.drag_current = (col, row)

        elif event.type == pygame.MOUSEBUTTONUP and self.drag_start:
            if self.drag_current:
                col = mx // max(1, self.block_width)
                row = (my - self.grid_top) // max(1, self.block_height)
                col = max(0, min(self.cols - 1, col))
                row = max(0, min(self.rows - 1, row))
                
                is_shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                if self.box_fill_mode or is_shift:
                    min_c = min(self.drag_start[0], col)
                    max_c = max(self.drag_start[0], col)
                    min_r = min(self.drag_start[1], row)
                    max_r = max(self.drag_start[1], row)
                    
                    target_type = self.current_type if self.drag_button == 1 else "0"
                    for r in range(min_r, max_r + 1):
                        for c in range(min_c, max_c + 1):
                            self.grid[r][c] = target_type
                            
                    w_count = max_c - min_c + 1
                    h_count = max_r - min_r + 1
                    self.set_status(f"Rechteck befüllt: {w_count}x{h_count} Blöcke mit '{target_type}'.")
                    
            self.drag_start = None
            self.drag_current = None

        if event.type == pygame.KEYDOWN:
            ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
            
            if ctrl and event.key == pygame.K_z:
                self.undo()
                return
            elif ctrl and event.key == pygame.K_y:
                self.redo()
                return

            if event.key == pygame.K_1: self.current_type = "1"
            if event.key == pygame.K_2: self.current_type = "2"
            if event.key == pygame.K_3: self.current_type = "3"
            if event.key == pygame.K_4: self.current_type = "4"
            if event.key == pygame.K_5: self.current_type = "5"
            if event.key == pygame.K_p: self.current_type = "P"
            if event.key == pygame.K_d: self.current_type = "D"
            if event.key == pygame.K_b: self.current_type = "B"
            if event.key == pygame.K_x: self.current_type = "X"
            if event.key == pygame.K_t: self.apply_template()
            if event.key == pygame.K_m: self.current_type = "M"
            if event.key == pygame.K_k: self.current_type = "K"
            if event.key == pygame.K_0: self.current_type = "0"
            
            if event.key == pygame.K_f:
                self.box_fill_mode = not self.box_fill_mode
                self.set_status(f"Box-Füllen Modus: {'AN' if self.box_fill_mode else 'AUS'}")
            if event.key == pygame.K_c:
                self.center_grid()
            if event.key == pygame.K_l:
                self.load_selected_level()
            if event.key == pygame.K_n:
                self.create_new_level()
            if event.key == pygame.K_s:
                self.save_level()
            
            if event.key == pygame.K_RIGHT:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.set_grid_size(self.cols + 1, self.rows)
                else:
                    self.move_cursor(1, 0)
            if event.key == pygame.K_LEFT:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.set_grid_size(self.cols - 1, self.rows)
                else:
                    self.move_cursor(-1, 0)
            if event.key == pygame.K_UP:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.set_grid_size(self.cols, self.rows - 1)
                else:
                    self.move_cursor(0, -1)
            if event.key == pygame.K_DOWN:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.set_grid_size(self.cols, self.rows + 1)
                else:
                    self.move_cursor(0, 1)

            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.place_at_cursor()
            if event.key == pygame.K_DELETE:
                self.erase_at_cursor()

    def update(self):
        is_shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        if not self.box_fill_mode and not is_shift:
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0] or mouse_buttons[2]:
                mx, my = pygame.mouse.get_pos()
                if my >= self.grid_top:
                    col = mx // max(1, self.block_width)
                    row = (my - self.grid_top) // max(1, self.block_height)
                    
                    if 0 <= col < self.cols and 0 <= row < self.rows:
                        self.cursor_col = col
                        self.cursor_row = row
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
        
        # --- UI RECTS ---
        self.btn_col_minus = pygame.Rect(10, 10, 22, 24)
        self.btn_col_plus = pygame.Rect(34, 10, 22, 24)
        self.btn_row_minus = pygame.Rect(105, 10, 22, 24)
        self.btn_row_plus = pygame.Rect(129, 10, 22, 24)
        
        self.btn_box_fill = pygame.Rect(178, 10, 58, 24)
        self.btn_center = pygame.Rect(238, 10, 68, 24)
        self.btn_template = pygame.Rect(308, 10, 68, 24)
        self.btn_undo = pygame.Rect(378, 10, 42, 24)
        self.btn_redo = pygame.Rect(422, 10, 42, 24)
        
        self.btn_prev_lvl = pygame.Rect(470, 10, 22, 24)
        self.btn_next_lvl = pygame.Rect(580, 10, 22, 24)
        self.btn_load_lvl = pygame.Rect(604, 10, 48, 24)
        self.btn_new_lvl = pygame.Rect(654, 10, 38, 24)
        self.btn_save_lvl = pygame.Rect(694, 10, 72, 24)
        
        pygame.draw.rect(self.screen, (30, 30, 35), (0, 0, sw, self.grid_top))
        
        self.draw_button(self.btn_col_minus, "-")
        self.draw_button(self.btn_col_plus, "+")
        col_label = self.font.render(f"C:{self.cols}", True, WHITE)
        self.screen.blit(col_label, (58, 15))

        self.draw_button(self.btn_row_minus, "-")
        self.draw_button(self.btn_row_plus, "+")
        row_label = self.font.render(f"R:{self.rows}", True, WHITE)
        self.screen.blit(row_label, (153, 15))

        box_bg = (0, 160, 160) if self.box_fill_mode else (60, 60, 70)
        self.draw_button(self.btn_box_fill, "Box(F)", bg_color=box_bg)
        self.draw_button(self.btn_center, "Zentrieren", bg_color=(50, 100, 150))
        self.draw_button(self.btn_template, "Muster(T)", bg_color=(140, 60, 160))
        self.draw_button(self.btn_undo, "Undo", bg_color=(80, 80, 90))
        self.draw_button(self.btn_redo, "Redo", bg_color=(80, 80, 90))

        self.draw_button(self.btn_prev_lvl, "<")
        lvl_name = self.available_levels[self.selected_level_idx] if self.available_levels else "Keine Level"
        lvl_label = self.font.render(lvl_name, True, YELLOW)
        self.screen.blit(lvl_label, (495, 15))
        self.draw_button(self.btn_next_lvl, ">")
        self.draw_button(self.btn_load_lvl, "Laden", bg_color=(40, 120, 40))
        self.draw_button(self.btn_new_lvl, "Neu")
        self.draw_button(self.btn_save_lvl, "Speichern", bg_color=(150, 50, 50))

        editing_str = f"Bearbeite: {self.editing_filename}" if self.editing_filename else "Neues Level"
        tool_str = f"Werkzeug: {self.types.get(self.current_type, {}).get('label', 'Unbekannt')}"
        mode_str = "MODUS: RECHTECK-BOX" if (self.box_fill_mode or (pygame.key.get_mods() & pygame.KMOD_SHIFT)) else "MODUS: EINZEL-STIFT"
        info_surf = self.font.render(f"{tool_str}  |  {mode_str}  |  {editing_str}", True, GREEN)
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

        if self.cursor_active and 0 <= self.cursor_col < self.cols and 0 <= self.cursor_row < self.rows:
            cx = self.cursor_col * self.block_width
            cy = self.grid_top + self.cursor_row * self.block_height
            pygame.draw.rect(self.screen, YELLOW, (cx, cy, self.block_width, self.block_height), 3)

        is_shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        if self.drag_start and self.drag_current and (self.box_fill_mode or is_shift):
            min_c = min(self.drag_start[0], self.drag_current[0])
            max_c = max(self.drag_start[0], self.drag_current[0])
            min_r = min(self.drag_start[1], self.drag_current[1])
            max_r = max(self.drag_start[1], self.drag_current[1])
            
            preview_x = min_c * self.block_width
            preview_y = self.grid_top + min_r * self.block_height
            preview_w = (max_c - min_c + 1) * self.block_width
            preview_h = (max_r - min_r + 1) * self.block_height
            
            overlay = pygame.Surface((preview_w, preview_h), pygame.SRCALPHA)
            overlay.fill((0, 255, 255, 60))
            self.screen.blit(overlay, (preview_x, preview_y))
            pygame.draw.rect(self.screen, CYAN, (preview_x, preview_y, preview_w, preview_h), 2)

        pygame.draw.rect(self.screen, (25, 25, 30), (0, sh - 35, sw, 35))
        status_surf = self.font.render(self.status_msg, True, CYAN)
        self.screen.blit(status_surf, (10, sh - 28))
        
        help_text = "Strg+Z=Undo | Strg+Y=Redo | T=Muster | SHIFT/F=Box-Fill | ESC=Menü"
        help_surf = self.font.render(help_text, True, (180, 180, 180))
        self.screen.blit(help_surf, (sw - help_surf.get_width() - 10, sh - 28))

if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()