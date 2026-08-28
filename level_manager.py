from __future__ import annotations
from typing import Any
import pygame
import os
from sprites import Block, Boss
from settings import *

class LevelManager:
    def __init__(self):
        self.padding: int = 4       # Abstand zwischen den Blöcken
        self.offset_y: int = 60     # Abstand vom oberen Bildschirmrand

    def load_level(self, level_filename: str, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT, level_num: int = 0) -> tuple[pygame.sprite.Group[Any], Boss | None]:
        blocks: pygame.sprite.Group[Any] = pygame.sprite.Group()
        path: str = os.path.join('levels', level_filename)
        boss: Boss | None = None

        # Fehlerabfang, falls die Datei nicht existiert
        if not os.path.exists(path):
            print(f"FEHLER: Level-Datei '{path}' nicht gefunden!")
            return blocks, None

        # Datei einlesen
        with open(path, 'r') as file:
            lines: list[str] = [line.strip() for line in file.readlines() if line.strip()]

        if not lines:
            return blocks, None

        has_boss_tile = any('K' in line for line in lines)
        if (level_num > 0 and level_num % 5 == 0) or has_boss_tile:
            boss_hp = 25 + max(0, (level_num // 5) - 1) * 10
            boss = Boss(screen_width, health=boss_hp)

        # Maximale Spaltenanzahl und Zeilenanzahl ermitteln
        cols: int = max(len(line) for line in lines)
        rows: int = len(lines)

        padding: int = self.padding
        # Verfügbare Breite & Höhe auf dem Bildschirm berechnen
        avail_width: int = screen_width - 40
        block_width: int = max(15, (avail_width - (cols - 1) * padding) // cols)

        offset_y = self.offset_y + (50 if boss else 0)
        max_y_allowed = screen_height - 130  # Mindestens 100px Sicherheitsabstand über dem Paddle
        avail_height: int = max(40, max_y_allowed - offset_y)

        needed_padding = (rows - 1) * padding if rows > 1 else 0
        if avail_height - needed_padding < rows * 6 and padding > 1:
            padding = max(1, (avail_height - rows * 6) // max(1, rows - 1))
            needed_padding = (rows - 1) * padding if rows > 1 else 0

        block_height: int = max(4, (avail_height - needed_padding) // rows) if rows > 0 else 30

        total_width: int = cols * block_width + (cols - 1) * padding
        offset_x: int = (screen_width - total_width) // 2

        # Blöcke generieren
        for row_idx, row_str in enumerate(lines):
            for col_idx, char in enumerate(row_str):
                if char not in ('0', 'K'):
                    x: int = offset_x + col_idx * (block_width + padding)
                    y: int = offset_y + row_idx * (block_height + padding)

                    block: Block = Block(x, y, block_width, block_height, char)
                    block.grid_col = col_idx
                    block.grid_row = row_idx
                    block.grid_cols = cols
                    block.grid_rows = rows
                    blocks.add(block)

        return blocks, boss