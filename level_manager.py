from __future__ import annotations
from typing import Any
import pygame
import os
from sprites import Block
from settings import *

class LevelManager:
    def __init__(self):
        self.padding: int = 4       # Abstand zwischen den Blöcken
        self.offset_y: int = 60     # Abstand vom oberen Bildschirmrand

    def load_level(self, level_filename: str, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT) -> pygame.sprite.Group[Any]:
        blocks: pygame.sprite.Group[Any] = pygame.sprite.Group()
        path: str = os.path.join('levels', level_filename)

        # Fehlerabfang, falls die Datei nicht existiert
        if not os.path.exists(path):
            print(f"FEHLER: Level-Datei '{path}' nicht gefunden!")
            return blocks

        # Datei einlesen
        with open(path, 'r') as file:
            lines: list[str] = [line.strip() for line in file.readlines() if line.strip()]

        if not lines:
            return blocks

        # Maximale Spaltenanzahl und Zeilenanzahl ermitteln
        cols: int = max(len(line) for line in lines)
        rows: int = len(lines)

        padding: int = self.padding
        # Verfügbare Breite & Höhe auf dem Bildschirm berechnen
        avail_width: int = screen_width - 40
        block_width: int = max(15, (avail_width - (cols - 1) * padding) // cols)

        # Das Raster soll ca. 45% der Bildschirmhöhe einnehmen
        avail_height: int = int(screen_height * 0.45) - self.offset_y
        block_height: int = max(12, (avail_height - (rows - 1) * padding) // rows) if rows > 0 else 30

        total_width: int = cols * block_width + (cols - 1) * padding
        offset_x: int = (screen_width - total_width) // 2

        # Blöcke generieren
        for row_idx, row_str in enumerate(lines):
            for col_idx, char in enumerate(row_str):
                if char != '0':
                    x: int = offset_x + col_idx * (block_width + padding)
                    y: int = self.offset_y + row_idx * (block_height + padding)

                    block: Block = Block(x, y, block_width, block_height, char)
                    blocks.add(block)

        return blocks