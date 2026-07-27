from __future__ import annotations  # Verhindert Runtime-Fehler beim Typ-Subskriptieren

import os
from typing import Any
import pygame

from sprites import Block
from settings import *

class LevelManager:
    def __init__(self):
        # Wir holen uns die Maße eines temporären Blocks für die Berechnung
        temp_block: Block = Block(0, 0, 0, 0, '1')
        self.block_width: int = temp_block.width
        self.block_height: int = temp_block.height
        self.padding: int = 5       # Abstand zwischen den Blöcken
        self.offset_y: int = 60     # Abstand vom oberen Bildschirmrand

    def load_level(self, level_filename: str) -> pygame.sprite.Group[Any]:
        blocks: pygame.sprite.Group[Any] = pygame.sprite.Group()
        path: str = os.path.join('levels', level_filename)

        # Fehlerabfang, falls die Datei nicht existiert
        if not os.path.exists(path):
            print(f"FEHLER: Level-Datei '{path}' nicht gefunden!")
            return blocks

        # Datei einlesen
        with open(path, 'r') as file:
            lines: list[str] = [line.strip() for line in file.readlines()]

        # Breite des gesamten Grids berechnen
        if len(lines) > 0:
            cols: int = len(lines[0])
            total_width: int = (
                cols * self.block_width + (cols - 1) * self.padding
            )
            offset_x: int = (SCREEN_WIDTH - total_width) // 2
        else:
            offset_x: int = 0

        # Blöcke generieren
        for row_idx, row_str in enumerate(lines):
            for col_idx, char in enumerate(row_str):
                if char != '0':
                    x: int = offset_x + col_idx * (
                        self.block_width + self.padding
                    )
                    y: int = self.offset_y + row_idx * (
                        self.block_height + self.padding
                    )

                    block: Block = Block(
                        x, y, self.block_width, self.block_height, char
                    )
                    blocks.add(block)

        return blocks