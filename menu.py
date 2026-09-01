# menu.py
from pygame import Rect, Surface
import pygame
import os
from settings import *

class Button:
    """Universelle Button-Klasse für das Hauptmenü mit Tastatur/Controller-Fokus"""
    def __init__(self, x: int, y: int, width: int, height: int, text: str, base_color: str | tuple[int, int, int], hover_color: str | tuple[int, int, int], text_color: str | tuple[int, int, int] = "WHITE"):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = base_color
        self.font = pygame.font.SysFont(None, 26, bold=True)

    def draw(self, screen: Surface, is_focused: bool = False):
        bg = self.hover_color if is_focused else self.current_color
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        
        if is_focused:
            pygame.draw.rect(screen, YELLOW, self.rect, width=3, border_radius=8)
        else:
            pygame.draw.rect(screen, WHITE, self.rect, width=2, border_radius=8)
        
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
    """Das interaktive Hauptmenü mit Tastatur- & Gamepad-Fokus"""
    def __init__(self):
        b_width, b_height = 280, 34
        
        self.order = ["PLAY", "LEVEL_SELECT", "SETTINGS", "DIFFICULTY", "EDITOR", "FULLSCREEN", "HIGHSCORE", "RESET", "QUIT"]
        self.selected_index = 0
        
        self.buttons = {
            "PLAY":         Button(0, 0, b_width, b_height, "Spiel Starten", (50, 150, 50), (70, 200, 70)),
            "LEVEL_SELECT": Button(0, 0, b_width, b_height, "Level Auswählen", (40, 100, 180), (60, 130, 230)),
            "SETTINGS":     Button(0, 0, b_width, b_height, "Einstellungen & Audio", (0, 150, 150), (0, 190, 190)),
            "DIFFICULTY":   Button(0, 0, b_width, b_height, "Schwierigkeit: Normal", (200, 140, 40), (230, 170, 60)),
            "EDITOR":       Button(0, 0, b_width, b_height, "Level Editor", (120, 50, 150), (160, 70, 200)),
            "FULLSCREEN":   Button(0, 0, b_width, b_height, "Vollbild: Aus", (0, 130, 140), (0, 180, 190)),
            "HIGHSCORE":    Button(0, 0, b_width, b_height, "Highscores", (33, 33, 33), (133, 133, 133)),
            "RESET":        Button(0, 0, b_width, b_height, "Fortschritt Löschen", (160, 50, 50), (210, 70, 70)),
            "QUIT":         Button(0, 0, b_width, b_height, "Beenden", (70, 70, 70), (100, 100, 100)),
        }
        
        self.title_font = pygame.font.SysFont(None, 52, bold=True)
        self.info_font = pygame.font.SysFont(None, 22)

    def navigate(self, delta: int):
        self.selected_index = (self.selected_index + delta) % len(self.order)

    def get_selected_action(self) -> str:
        return self.order[self.selected_index]

    def set_difficulty_label(self, difficulty_name: str):
        label = DIFFICULTY_SETTINGS.get(difficulty_name, {}).get("label", "Normal")
        self.buttons["DIFFICULTY"].text = f"Schwierigkeit: {label}"

    def update_layout(self, screen_w: int, screen_h: int, is_fullscreen: bool):
        b_width, b_height = 280, 34
        spacing = 41
        start_y = max(115, screen_h // 2 - (len(self.order) * spacing) // 2 + 25)
        center_x = screen_w // 2 - b_width // 2

        for idx, key in enumerate(self.order):
            btn = self.buttons[key]
            btn.rect.x = center_x
            btn.rect.y = start_y + idx * spacing

        self.buttons["FULLSCREEN"].text = "Vollbild: An" if is_fullscreen else "Vollbild: Aus"

    def draw(self, screen: Surface, unlocked_level: int, is_fullscreen: bool = False):
        screen_w, screen_h = screen.get_width(), screen.get_height()
        self.update_layout(screen_w, screen_h, is_fullscreen)

        # Titel
        title_surf = self.title_font.render("BREAKOUT CHAMPION", True, YELLOW)
        title_rect = title_surf.get_rect(center=(screen_w // 2, max(30, screen_h // 2 - 225)))
        screen.blit(title_surf, title_rect)
        
        # Info über Fortschritt
        info_surf = self.info_font.render(f"Freigeschaltete Level: {unlocked_level}", True, (180, 180, 180))
        info_rect = info_surf.get_rect(center=(screen_w // 2, title_rect.bottom + 10))
        screen.blit(info_surf, info_rect)
        
        # Alle Buttons zeichnen
        focused_key = self.order[self.selected_index]
        for key, button in self.buttons.items():
            button.draw(screen, is_focused=(key == focused_key))

    def handle_event(self, event: pygame.event.Event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEMOTION:
            for idx, key in enumerate(self.order):
                if self.buttons[key].rect.collidepoint(mouse_pos):
                    self.selected_index = idx
                self.buttons[key].check_hover(mouse_pos)
                
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action_name, button in self.buttons.items():
                if button.rect.collidepoint(mouse_pos):
                    return action_name

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.navigate(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.navigate(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.get_selected_action()
                    
        return None


class LevelSelectionMenu:
    """Levelauswahl - Controller/Gamepad & Tastatur-Steuerung"""
    def __init__(self, screen: Surface):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.title_font = pygame.font.SysFont(None, 54, bold=True)
        self.levels: list[str] = []
        self.selected_index = 0
        self.cols = 1
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

    def navigate(self, d_col: int, d_row: int, unlocked_level: int):
        total_items = len(self.levels) + 1  # Levels + Back Button
        if d_row != 0:
            if self.selected_index == len(self.levels):  # Currently on Back Button
                if d_row < 0:
                    self.selected_index = min(unlocked_level - 1, len(self.levels) - 1)
            else:
                new_idx = self.selected_index + d_row * self.cols
                if new_idx >= len(self.levels):
                    self.selected_index = len(self.levels)  # Go to Back Button
                elif 0 <= new_idx < len(self.levels):
                    self.selected_index = new_idx
        elif d_col != 0:
            if self.selected_index < len(self.levels):
                new_idx = self.selected_index + d_col
                if 0 <= new_idx < len(self.levels):
                    self.selected_index = new_idx

    def get_selected_action(self, unlocked_level: int):
        if self.selected_index == len(self.levels):
            return "BACK"
        level_num = self.selected_index + 1
        if level_num <= unlocked_level:
            return level_num
        return None

    def draw(self, unlocked_level: int):
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        
        self.detect_levels()  
        self.buttons.clear()
        
        title_text = self.title_font.render("BREAKOUT - LEVELAUSWAHL", True, YELLOW)
        self.screen.blit(title_text, (screen_w // 2 - title_text.get_width() // 2, 40))
        
        btn_w, btn_h = 130, 80
        gap_x, gap_y = 30, 30
        self.cols = max(1, (screen_w - 60) // (btn_w + gap_x))
        
        total_grid_w = self.cols * btn_w + (self.cols - 1) * gap_x
        start_x = (screen_w - total_grid_w) // 2
        start_y = 120
        
        mouse_pos = pygame.mouse.get_pos()
        
        for idx, _level_file in enumerate(self.levels):
            level_num = idx + 1
            is_unlocked = level_num <= unlocked_level
            
            col = idx % self.cols
            row = idx // self.cols
            x = start_x + col * (btn_w + gap_x)
            y = start_y + row * (btn_h + gap_y)
            
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.buttons.append((rect, level_num, is_unlocked))
            
            is_focused = (idx == self.selected_index)
            
            if is_unlocked:
                bg_color = (70, 200, 70) if is_focused else (BLUE if not rect.collidepoint(mouse_pos) else GREEN)
                pygame.draw.rect(self.screen, bg_color, rect, border_radius=8) 
                text_color = WHITE
            else:
                pygame.draw.rect(self.screen, (70, 70, 70), rect, border_radius=8) 
                text_color = (130, 130, 130)
            
            if is_focused:
                pygame.draw.rect(self.screen, YELLOW, rect, width=3, border_radius=8)
            else:
                pygame.draw.rect(self.screen, WHITE, rect, width=2, border_radius=8)
            
            txt = self.font.render(f"Level {level_num}", True, text_color)
            self.screen.blit(txt, (x + btn_w//2 - txt.get_width()//2, y + btn_h//2 - txt.get_height()//2))
            
            if not is_unlocked:
                lock_font = pygame.font.SysFont(None, 20)
                lock_txt = lock_font.render("X Gesperrt", True, RED)
                self.screen.blit(lock_txt, (x + btn_w//2 - lock_txt.get_width()//2, y + btn_h - 22))

        # --- ZURÜCK-BUTTON ZEICHNEN ---
        self.back_btn_rect = pygame.Rect(screen_w // 2 - 100, screen_h - 70, 200, 45)
        is_back_focused = (self.selected_index == len(self.levels))
        
        bg_back = (100, 100, 100) if is_back_focused or self.back_btn_rect.collidepoint(mouse_pos) else (50, 50, 50)
        pygame.draw.rect(self.screen, bg_back, self.back_btn_rect, border_radius=8)
        
        if is_back_focused:
            pygame.draw.rect(self.screen, YELLOW, self.back_btn_rect, width=3, border_radius=8)
        else:
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


class SettingsMenu:
    """Interaktives Einstellungen- & Audio-Menü mit Controller-Unterstützung"""
    def __init__(self, screen: Surface):
        self.screen = screen
        self.title_font = pygame.font.SysFont(None, 46, bold=True)
        self.label_font = pygame.font.SysFont(None, 24, bold=True)
        self.small_font = pygame.font.SysFont(None, 20)
        
        self.selected_row = 0  # 0: SFX Slider, 1: BGM Slider, 2: Sound Test, 3: Mute, 4: Fullscreen, 5: Back
        self.dragging_sfx = False
        self.dragging_music = False
        
        # Rects für Interaktion
        self.sfx_slider_rect = pygame.Rect(0, 0, 220, 16)
        self.music_slider_rect = pygame.Rect(0, 0, 220, 16)
        
        self.test_sound_btn = pygame.Rect(0, 0, 160, 36)
        self.mute_btn = pygame.Rect(0, 0, 160, 36)
        self.fullscreen_btn = pygame.Rect(0, 0, 160, 36)
        self.mouse_btn = pygame.Rect(0, 0, 160, 36)
        self.back_btn = pygame.Rect(0, 0, 200, 45)

    def navigate_row(self, delta: int):
        self.selected_row = (self.selected_row + delta) % 7

    def adjust_slider(self, delta: float, sound_manager: Any):
        if self.selected_row == 0:
            val = max(0.0, min(1.0, sound_manager.sfx_volume + delta))
            sound_manager.set_sfx_volume(val)
        elif self.selected_row == 1:
            val = max(0.0, min(1.0, sound_manager.music_volume + delta))
            sound_manager.set_music_volume(val)

    def trigger_selected_action(self, sound_manager: Any) -> str | None:
        if self.selected_row == 2:
            sound_manager.play_sound("powerup")
            return "TEST_SOUND"
        elif self.selected_row == 3:
            sound_manager.toggle_mute()
            return "TOGGLE_MUTE"
        elif self.selected_row == 4:
            return "TOGGLE_FULLSCREEN"
        elif self.selected_row == 5:
            return "TOGGLE_MOUSE_CONTROL"
        elif self.selected_row == 6:
            return "BACK"
        return None

    def draw(self, sound_manager: Any, difficulty: str, is_fullscreen: bool, mouse_control_enabled: bool = True):
        sw, sh = self.screen.get_width(), self.screen.get_height()
        center_x = sw // 2
        
        title_surf = self.title_font.render("EINSTELLUNGEN & AUDIO", True, YELLOW)
        self.screen.blit(title_surf, (center_x - title_surf.get_width() // 2, 30))
        
        start_y = 95
        spacing = 50
        slider_w = 240
        mouse_pos = pygame.mouse.get_pos()
        
        # --- 1. SFX LAUTSTÄRKE SLIDER ---
        self.sfx_slider_rect = pygame.Rect(center_x - 30, start_y, slider_w, 16)
        lbl_sfx = self.label_font.render("SFX Lautstärke:", True, YELLOW if self.selected_row == 0 else WHITE)
        val_sfx = self.label_font.render(f"{int(sound_manager.sfx_volume * 100)}%", True, CYAN)
        
        self.screen.blit(lbl_sfx, (center_x - 220, start_y - 2))
        self.screen.blit(val_sfx, (self.sfx_slider_rect.right + 15, start_y - 2))
        
        pygame.draw.rect(self.screen, (60, 60, 70), self.sfx_slider_rect, border_radius=6)
        fill_w = int(slider_w * sound_manager.sfx_volume)
        if fill_w > 0:
            pygame.draw.rect(self.screen, CYAN, (self.sfx_slider_rect.x, self.sfx_slider_rect.y, fill_w, 16), border_radius=6)
        border_col = YELLOW if self.selected_row == 0 else WHITE
        pygame.draw.rect(self.screen, border_col, self.sfx_slider_rect, width=3 if self.selected_row == 0 else 2, border_radius=6)
        
        knob_x = self.sfx_slider_rect.x + fill_w
        pygame.draw.circle(self.screen, border_col, (knob_x, self.sfx_slider_rect.centery), 11)

        # --- 2. BGM MUSIK LAUTSTÄRKE SLIDER ---
        start_y += spacing
        self.music_slider_rect = pygame.Rect(center_x - 30, start_y, slider_w, 16)
        lbl_mus = self.label_font.render("Musik (BGM):", True, YELLOW if self.selected_row == 1 else WHITE)
        val_mus = self.label_font.render(f"{int(sound_manager.music_volume * 100)}%", True, CYAN)
        
        self.screen.blit(lbl_mus, (center_x - 220, start_y - 2))
        self.screen.blit(val_mus, (self.music_slider_rect.right + 15, start_y - 2))
        
        pygame.draw.rect(self.screen, (60, 60, 70), self.music_slider_rect, border_radius=6)
        fill_m = int(slider_w * sound_manager.music_volume)
        if fill_m > 0:
            pygame.draw.rect(self.screen, GREEN, (self.music_slider_rect.x, self.music_slider_rect.y, fill_m, 16), border_radius=6)
        border_mcol = YELLOW if self.selected_row == 1 else WHITE
        pygame.draw.rect(self.screen, border_mcol, self.music_slider_rect, width=3 if self.selected_row == 1 else 2, border_radius=6)
        
        knob_mx = self.music_slider_rect.x + fill_m
        pygame.draw.circle(self.screen, border_mcol, (knob_mx, self.music_slider_rect.centery), 11)

        # --- 3. TOGGLE & TEST BUTTONS (Zeile 1: Sound Test, Mute) ---
        start_y += spacing + 5
        btn_w, btn_h = 160, 34
        
        # Sound Test Button
        self.test_sound_btn = pygame.Rect(center_x - 170, start_y, btn_w, btn_h)
        is_test_foc = (self.selected_row == 2)
        col_test = (60, 120, 180) if not is_test_foc and not self.test_sound_btn.collidepoint(mouse_pos) else (80, 150, 220)
        pygame.draw.rect(self.screen, col_test, self.test_sound_btn, border_radius=6)
        pygame.draw.rect(self.screen, YELLOW if is_test_foc else WHITE, self.test_sound_btn, width=3 if is_test_foc else 2, border_radius=6)
        txt_test = self.small_font.render("🔊 Sound Test", True, WHITE)
        self.screen.blit(txt_test, (self.test_sound_btn.centerx - txt_test.get_width() // 2, self.test_sound_btn.centery - txt_test.get_height() // 2))

        # Mute Toggle Button
        self.mute_btn = pygame.Rect(center_x + 10, start_y, btn_w, btn_h)
        is_mute_foc = (self.selected_row == 3)
        col_mute = (160, 50, 50) if sound_manager.muted else ((50, 140, 50) if not is_mute_foc and not self.mute_btn.collidepoint(mouse_pos) else (70, 180, 70))
        pygame.draw.rect(self.screen, col_mute, self.mute_btn, border_radius=6)
        pygame.draw.rect(self.screen, YELLOW if is_mute_foc else WHITE, self.mute_btn, width=3 if is_mute_foc else 2, border_radius=6)
        txt_mute = self.small_font.render("Ton: STUMM" if sound_manager.muted else "Ton: AKTIV", True, WHITE)
        self.screen.blit(txt_mute, (self.mute_btn.centerx - txt_mute.get_width() // 2, self.mute_btn.centery - txt_mute.get_height() // 2))

        # --- TOGGLE BUTTONS (Zeile 2: Vollbild, Maussteuerung) ---
        start_y += 42
        # Vollbild Toggle Button
        self.fullscreen_btn = pygame.Rect(center_x - 170, start_y, btn_w, btn_h)
        is_fs_foc = (self.selected_row == 4)
        col_fs = (0, 130, 140) if not is_fs_foc and not self.fullscreen_btn.collidepoint(mouse_pos) else (0, 170, 180)
        pygame.draw.rect(self.screen, col_fs, self.fullscreen_btn, border_radius=6)
        pygame.draw.rect(self.screen, YELLOW if is_fs_foc else WHITE, self.fullscreen_btn, width=3 if is_fs_foc else 2, border_radius=6)
        txt_fs = self.small_font.render("Vollbild: AN" if is_fullscreen else "Vollbild: AUS", True, WHITE)
        self.screen.blit(txt_fs, (self.fullscreen_btn.centerx - txt_fs.get_width() // 2, self.fullscreen_btn.centery - txt_fs.get_height() // 2))

        # Maussteuerung Toggle Button
        self.mouse_btn = pygame.Rect(center_x + 10, start_y, btn_w, btn_h)
        is_mouse_foc = (self.selected_row == 5)
        col_mouse = (140, 90, 0) if mouse_control_enabled else (70, 70, 80)
        if is_mouse_foc or self.mouse_btn.collidepoint(mouse_pos):
            col_mouse = (180, 120, 0) if mouse_control_enabled else (90, 90, 105)
        pygame.draw.rect(self.screen, col_mouse, self.mouse_btn, border_radius=6)
        pygame.draw.rect(self.screen, YELLOW if is_mouse_foc else WHITE, self.mouse_btn, width=3 if is_mouse_foc else 2, border_radius=6)
        txt_mouse = self.small_font.render("Maus: AN" if mouse_control_enabled else "Maus: AUS", True, WHITE)
        self.screen.blit(txt_mouse, (self.mouse_btn.centerx - txt_mouse.get_width() // 2, self.mouse_btn.centery - txt_mouse.get_height() // 2))

        # --- 4. TASTENBELEGUNG / CONTROLS CHEATSHEET BOX ---
        start_y += 48
        box_rect = pygame.Rect(center_x - 260, start_y, 520, 160)
        pygame.draw.rect(self.screen, (30, 30, 38), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), box_rect, width=2, border_radius=10)
        
        box_title = self.label_font.render("--- Steuerung & Tastenbelegung ---", True, ORANGE)
        self.screen.blit(box_title, (center_x - box_title.get_width() // 2, start_y + 8))
        
        controls = [
            "Maus / Pfeiltasten / Stick : Paddle bewegen / Menü navigieren",
            "Linksklick / Leertaste / A  : Ball starten / Laser-Kanonen feuern",
            "Rechtsklick                 : Homing Missiles (Raketen) feuern",
            "P / Button Start            : Pause umschalten",
            "M / Button LB/RB            : Audio stummschalten (Mute)",
            "F11 / Alt+Enter             : Vollbildmodus umschalten",
            "C, L, S (Editor)            : Raster zentrieren (C), Level laden (L), Speichern (S)"
        ]
        
        for idx, ctrl in enumerate(controls):
            txt = self.small_font.render(ctrl, True, (220, 220, 220))
            self.screen.blit(txt, (box_rect.x + 20, start_y + 32 + idx * 17))

        # --- 5. ZURÜCK BUTTON ---
        self.back_btn = pygame.Rect(center_x - 100, sh - 55, 200, 42)
        is_back_foc = (self.selected_row == 6)
        col_back = (100, 100, 100) if is_back_foc or self.back_btn.collidepoint(mouse_pos) else (60, 60, 60)
        pygame.draw.rect(self.screen, col_back, self.back_btn, border_radius=8)
        pygame.draw.rect(self.screen, YELLOW if is_back_foc else WHITE, self.back_btn, width=3 if is_back_foc else 2, border_radius=8)
        
        back_txt = self.label_font.render("Zurück", True, WHITE)
        self.screen.blit(back_txt, (self.back_btn.centerx - back_txt.get_width() // 2, self.back_btn.centery - back_txt.get_height() // 2))

    def handle_event(self, event: pygame.event.Event, sound_manager: Any) -> str | None:
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.sfx_slider_rect.collidepoint(mouse_pos):
                self.selected_row = 0
                self.dragging_sfx = True
                self.update_sfx(mouse_pos[0], sound_manager)
            elif self.music_slider_rect.collidepoint(mouse_pos):
                self.selected_row = 1
                self.dragging_music = True
                self.update_music(mouse_pos[0], sound_manager)
            elif self.test_sound_btn.collidepoint(mouse_pos):
                self.selected_row = 2
                sound_manager.play_sound("powerup")
                return "TEST_SOUND"
            elif self.mute_btn.collidepoint(mouse_pos):
                self.selected_row = 3
                sound_manager.toggle_mute()
                return "TOGGLE_MUTE"
            elif self.fullscreen_btn.collidepoint(mouse_pos):
                self.selected_row = 4
                return "TOGGLE_FULLSCREEN"
            elif self.mouse_btn.collidepoint(mouse_pos):
                self.selected_row = 5
                return "TOGGLE_MOUSE_CONTROL"
            elif self.back_btn.collidepoint(mouse_pos):
                self.selected_row = 6
                return "BACK"

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_sfx = False
            self.dragging_music = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_sfx:
                self.update_sfx(mouse_pos[0], sound_manager)
            elif self.dragging_music:
                self.update_music(mouse_pos[0], sound_manager)

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.navigate_row(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.navigate_row(1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.adjust_slider(-0.05, sound_manager)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.adjust_slider(0.05, sound_manager)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.trigger_selected_action(sound_manager)
            elif event.key == pygame.K_ESCAPE:
                return "BACK"

        return None

    def update_sfx(self, mouse_x: int, sound_manager: Any):
        rel = (mouse_x - self.sfx_slider_rect.x) / max(1, self.sfx_slider_rect.width)
        val = max(0.0, min(1.0, rel))
        sound_manager.set_sfx_volume(val)

    def update_music(self, mouse_x: int, sound_manager: Any):
        rel = (mouse_x - self.music_slider_rect.x) / max(1, self.music_slider_rect.width)
        val = max(0.0, min(1.0, rel))
        sound_manager.set_music_volume(val)