import pygame
import os
from sprites import Block
from settings import *

class LevelManager:
    def __init__(self):
        # Wir holen uns die Maße eines temporären Blocks für die Berechnung
        temp_block = Block(0, 0, 0, 0, '1')
        self.block_width = temp_block.width
        self.block_height = temp_block.height
        self.padding = 5       # Abstand zwischen den Blöcken
        self.offset_y = 60     # Abstand vom oberen Bildschirmrand

    def load_level(self, level_filename):
        blocks = pygame.sprite.Group()
        path = os.path.join("levels", level_filename)
        
        # Fehlerabfang, falls die Datei nicht existiert
        if not os.path.exists(path):
            print(f"FEHLER: Level-Datei '{path}' nicht gefunden!")
            return blocks

        # Datei einlesen
        with open(path, 'r') as file:
            lines = [line.strip() for line in file.readlines()]

        # Breite des gesamten Grids berechnen, um es mittig zu platzieren
        if len(lines) > 0:
            cols = len(lines[0])
            total_width = cols * self.block_width + (cols - 1) * self.padding
            offset_x = (SCREEN_WIDTH - total_width) // 2
        else:
            offset_x = 0

        # Blöcke generieren
        for row_idx, row_str in enumerate(lines):
            for col_idx, char in enumerate(row_str):
                if char != '0': # '0' bedeutet leerer Raum
                    # Koordinaten berechnen
                    x = offset_x + col_idx * (self.block_width + self.padding)
                    y = self.offset_y + row_idx * (self.block_height + self.padding)
                    
                    # Block erstellen und zur Gruppe hinzufügen
                    block = Block(x, y, self.block_width, self.block_height, char)
                    blocks.add(block)
                    
        return blocks