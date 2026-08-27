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
        
        self.types: dict[str, dict[str, Any]] = {
            "0": {"color": BLUE, "label": "Radiergummi / Leer (Taste 0)"},
            "1": {"color": YELLOW, "label": "Normaler Block (Taste 1)"},
            "2": {"color": ORANGE_YELLOW, "label": "Starker Block (2 Leben) (Taste 2)"},
            "3": {"color": ORANGE, "label": "Starker Block (3 Leben) (Taste 3)"},
            "4": {"color": REDDISH_ORANGE, "label": "Starker Block (4 Leben) (Taste 4)"},
            "5": {"color": RED, "label": "Starker Block (5 Leben) (Taste 5)"},
            "P": {"color": GREEN, "label": "PowerUp-Block (Taste P)"},
            "D": {"color": DARK_PURPLE, "label": "PowerDown-Block (Taste D)"},
            "B": {"color": (220, 40, 40), "label": "Bomben-Block (Taste B/E)"},
            "E": {"color": (220, 40, 40), "label": "Explosiver Block (Taste E)"},
            "X": {"color": (100, 100, 115), "label": "Stahl-Block (Taste X/U)"},
            "U": {"color": STEEL_GREY, "label": "Unzerstoerbar (Taste U)"},
            "T": {"color": (140, 30, 210), "label": "Portal-Block (Taste T)"},
            "M": {"color": (255, 170, 0), "label": "Beweglicher Block (Taste M)"}
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
            if event.key == pygame.K_d: self.current_type = "D"
            if event.key in (pygame.K_b, pygame.K_e): self.current_type = "B"
            if event.key in (pygame.K_x, pygame.K_u): self.current_type = "X"
            if event.key == pygame.K_t: self.current_type = "T"
            if event.key == pygame.K_m: self.current_type = "M"
            if event.key == pygame.K_0: self.current_type = "0"
            
            # Grid-Größenanpassung
            if event.key == pygame.K_UP:
                self.set_grid_size(self.cols, self.rows - 1)
            elif event.key == pygame.K_DOWN:
                self.set_grid_size(self.cols, self.rows + 1)
            elif event.key == pygame.K_RIGHT:
                self.set_grid_size(self.cols + 1, self.rows)
            elif event.key == pygame.K_LEFT:
                self.set_grid_size(self.cols - 1, self.rows)

            # Speichern auslösen
            if event.key == pygame.K_s:
                self.save_level()

    def update(self):
        """Beobachtet kontinuierlich die Maus im Editor-Modus (läuft jeden Frame)"""
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        bw = self.block_width
        bh = self.block_height
        grid_limit_y = self.rows * bh
        if mouse_pos[1] < grid_limit_y:
            col = mouse_pos[0] // bw
            row = mouse_pos[1] // bh
            
            if 0 <= col < self.cols and 0 <= row < self.rows:
                if mouse_buttons[0]:    # Linksklick -> Block platzieren
                    self.grid[row][col] = self.current_type
                elif mouse_buttons[2]:  # Rechtsklick -> Block löschen
                    self.grid[row][col] = "0"

    def save_level(self):
        # Lokaler Import verhindert den Absturz durch zirkuläre Importe!
        from game import get_level_name

        if not os.path.exists("levels"):
            os.makedirs("levels")
            
        level_num = 1
        while os.path.exists(os.path.join("levels", get_level_name(level_num))):
            level_num += 1
            
        filename = os.path.join("levels", get_level_name(level_num))
        
        try:
            with open(filename, "w") as file:
                for row in self.grid:
                    line = "".join(row) + "\n"
                    file.write(line)
            print(f"[Editor] Level erfolgreich gespeichert unter: {filename}")
            pygame.display.set_caption(f"GESPEICHERT ALS {get_level_name(level_num)}!")
        except Exception as e:
            print(f"[Editor-Fehler] Konnte Level nicht schreiben: {e}")

    def draw(self):
        self.screen.fill(DARK_GREY)
        
        bw = self.block_width
        bh = self.block_height
        
        # 1. Das Raster und die gesetzten Blöcke zeichnen
        for row in range(self.rows):
            for col in range(self.cols):
                block_type = self.grid[row][col]
                color = self.types.get(block_type, self.types["0"])["color"]
                
                rect = pygame.Rect(col * bw, row * bh, bw - 1, bh - 1)
                pygame.draw.rect(self.screen, color, rect)
                
                if block_type in ("P", "D", "B", "E", "X", "U", "T", "M"):
                    lbl_txt = self.font.render(block_type, True, WHITE if block_type not in ("P", "M") else BLACK)
                    self.screen.blit(lbl_txt, (rect.x + rect.width//2 - lbl_txt.get_width()//2, 
                                             rect.y + rect.height//2 - lbl_txt.get_height()//2))

        screen_w = self.screen.get_width()
        pygame.draw.line(self.screen, WHITE, (0, self.rows * bh), 
                         (screen_w, self.rows * bh), 2)
        
        # 2. UI-Steuerung & Informationen unterhalb des Grids
        ui_y = self.rows * bh + 10
        active_label = self.types.get(self.current_type, self.types["1"])['label']
        sel_text = self.font.render(f"Ausgewaehltes Werkzeug: {active_label} | Raster: {self.cols}x{self.rows}", True, YELLOW)
        self.screen.blit(sel_text, (20, ui_y))
        
        instructions = [
            "BEDIENUNG:",
            "- Tasten [1]-[5], [P], [D], [B/E], [X/U], [T], [M] oder [0]: Blocktyp wechseln",
            "- Pfeiltasten [LINKS]/[RECHTS]: Spalten +/- | [OBEN]/[UNTEN]: Zeilen +/-",
            "- Linksklick: Zeichnen | Rechtsklick: Radieren",
            "- Taste [S]: Als neues Level in /levels/ speichern | Taste [ESC]: Editor schliessen"
        ]

        for idx, text in enumerate(instructions):
            color = (50, 150, 255) if idx == 0 else WHITE
            txt_surf = self.font.render(text, True, color)
            self.screen.blit(txt_surf, (20, ui_y + 24 + idx * 18))
            
        pygame.display.flip()

if __name__ == "__main__":
    # Wenn man die Datei direkt ausführt, startet sie wie gewohnt autonom
    editor = LevelEditor()
    editor.run()
    pygame.quit()