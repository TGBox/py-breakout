# editor.py
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
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Breakout - Level Editor")
            self.clock = pygame.time.Clock()
        
        # Grid-Einstellungen (Passend zur LevelManager-Logik)
        self.cols = 10
        self.rows = 10  # Maximale vertikale Reihen für Blöcke
        self.block_width = SCREEN_WIDTH // self.cols
        self.block_height = 30
        
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
            "M": {"color": (255, 170, 0), "label": "Beweglicher Block (Taste M)"}
        }
        
        self.font = pygame.font.SysFont(None, 22)
        self.running = True

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
            if event.key == pygame.K_0: self.current_type = "0"
            
            # Speichern auslösen
            if event.key == pygame.K_s:
                self.save_level()

    def update(self):
        """Beobachtet kontinuierlich die Maus im Editor-Modus (läuft jeden Frame)"""
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        grid_limit_y = self.rows * self.block_height
        if mouse_pos[1] < grid_limit_y:
            col = mouse_pos[0] // self.block_width
            row = mouse_pos[1] // self.block_height
            
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
        
        # 1. Das Raster und die gesetzten Blöcke zeichnen
        for row in range(self.rows):
            for col in range(self.cols):
                block_type = self.grid[row][col]
                color = self.types[block_type]["color"]
                
                rect = pygame.Rect(col * self.block_width, row * self.block_height, 
                                   self.block_width - 2, self.block_height - 2)
                pygame.draw.rect(self.screen, color, rect)
                
                if block_type in ("P", "B", "X", "T", "M"):
                    lbl_txt = self.font.render(block_type, True, BLACK if block_type in ("P", "M") else WHITE)
                    self.screen.blit(lbl_txt, (rect.x + rect.width//2 - lbl_txt.get_width()//2, 
                                             rect.y + rect.height//2 - lbl_txt.get_height()//2))

        pygame.draw.line(self.screen, WHITE, (0, self.rows * self.block_height), 
                         (SCREEN_WIDTH, self.rows * self.block_height), 2)
        
        # 2. UI-Steuerung & Informationen unterhalb des Grids
        ui_y = self.rows * self.block_height + 10
        active_label = self.types[self.current_type]['label']
        sel_text = self.font.render(f"Ausgewaehltes Werkzeug: {active_label}", True, YELLOW)
        self.screen.blit(sel_text, (20, ui_y))
        
        instructions = [
            "BEDIENUNG:",
            "- Tasten [1]-[5], [P], [B], [X], [T], [M] oder [0] druecken, um Blocktyp zu wechseln",
            "- Linke Maustaste: Zeichnen | Rechte Maustaste: Radieren",
            "- Taste [S]: Als neues Level in /levels/ speichern | Taste [ESC]: Editor schliessen"
        ]
        
        for idx, text in enumerate(instructions):
            color = (50, 150, 255) if idx == 0 else WHITE
            txt_surf = self.font.render(text, True, color)
            self.screen.blit(txt_surf, (20, ui_y + 26 + idx * 20))
            
        pygame.display.flip()

if __name__ == "__main__":
    # Wenn man die Datei direkt ausführt, startet sie wie gewohnt autonom
    editor = LevelEditor()
    editor.run()
    pygame.quit()