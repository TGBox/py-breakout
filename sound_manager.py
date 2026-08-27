# sound_manager.py
import os
import io
import math
import wave
import struct
import random
import pygame
from typing import Any

class SoundManager:
    """Hybrid Sound Manager for Py-Breakout:
    - Synthesizes 8-Bit Retro PCM Sounds in memory at startup (no external files required).
    - Checks 'sounds/' folder for custom WAV files to override synthesized sounds.
    - Generates and loops a Chiptune background music track.
    - Handles mute and volume controls.
    """
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.muted = False
        self.sfx_volume = 0.8
        self.music_volume = 0.5
        self.mixer_initialized = False
        
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.bgm_sound: pygame.mixer.Sound | None = None
        self.bgm_channel: pygame.mixer.Channel | None = None
        
        self._init_mixer()
        if self.mixer_initialized:
            self._load_or_generate_sounds()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self.mixer_initialized = True
        except Exception as e:
            print(f"[SoundManager] Mixer-Initialisierung fehlgeschlagen: {e}")
            self.mixer_initialized = False

    def _create_wav_bytes(self, samples: list[float]) -> bytes:
        """Konvertiert eine Liste von Audiosamples (-1.0 bis 1.0) in in-memory WAV-Bytes."""
        byte_io = io.BytesIO()
        with wave.open(byte_io, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-Bit PCM
            wav_file.setframerate(self.sample_rate)
            
            raw_data = bytearray()
            for sample in samples:
                clamped = max(-1.0, min(1.0, sample))
                int_sample = int(clamped * 32767)
                raw_data.extend(struct.pack('<h', int_sample))
                
            wav_file.writeframes(raw_data)
            
        byte_io.seek(0)
        return byte_io.read()

    def _generate_paddle_hit(self) -> pygame.mixer.Sound:
        """Kurzer tiefer Rechteckton (150Hz -> 80Hz)"""
        dur = 0.08
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 160 - 70 * (t / dur)
            env = (1.0 - t / dur) ** 2
            val = 0.4 if (t * freq) % 1.0 < 0.5 else -0.4
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_wall_hit(self) -> pygame.mixer.Sound:
        """Hoher kurzer Klick (350Hz)"""
        dur = 0.05
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            env = 1.0 - (t / dur)
            val = 0.3 * math.sin(2 * math.pi * 350 * t)
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_block_hit(self) -> pygame.mixer.Sound:
        """Chiptune Block-Treffer Ton (440Hz -> 660Hz)"""
        dur = 0.09
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 440 + 300 * (t / dur)
            env = 1.0 - (t / dur)
            val = 0.4 if (t * freq) % 1.0 < 0.5 else -0.4
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_explosion(self) -> pygame.mixer.Sound:
        """Tiefer Rausch-Knall für Explosionen"""
        dur = 0.35
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            env = (1.0 - t / dur) ** 2.5
            noise = random.uniform(-0.6, 0.6)
            low_pulse = 0.3 * math.sin(2 * math.pi * 60 * t)
            samples.append((noise + low_pulse) * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_powerup(self) -> pygame.mixer.Sound:
        """Aufsteigendes Arpeggio (C5 -> E5 -> G5 -> C6)"""
        dur = 0.2
        n_samples = int(self.sample_rate * dur)
        samples = []
        freqs = [523.25, 659.25, 783.99, 1046.50]
        for i in range(n_samples):
            t = i / self.sample_rate
            step = int((t / dur) * 4)
            freq = freqs[min(3, step)]
            env = 1.0 - (t / dur) * 0.5
            val = 0.35 if (t * freq) % 1.0 < 0.5 else -0.35
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_powerdown(self) -> pygame.mixer.Sound:
        """Abfallendes Arpeggio (G5 -> E5 -> C5 -> G4)"""
        dur = 0.22
        n_samples = int(self.sample_rate * dur)
        samples = []
        freqs = [783.99, 659.25, 523.25, 392.00]
        for i in range(n_samples):
            t = i / self.sample_rate
            step = int((t / dur) * 4)
            freq = freqs[min(3, step)]
            env = 1.0 - (t / dur) * 0.5
            val = 0.35 if (t * freq) % 1.0 < 0.5 else -0.35
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_laser(self) -> pygame.mixer.Sound:
        """Laser Pew-Pew (900Hz -> 200Hz)"""
        dur = 0.12
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 900 * math.exp(-8 * t)
            env = 1.0 - (t / dur)
            val = 0.35 if (t * freq) % 1.0 < 0.5 else -0.35
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_boss_hit(self) -> pygame.mixer.Sound:
        """Metallischer Boss-Treffer Clang"""
        dur = 0.15
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            env = (1.0 - t / dur) ** 2
            val = 0.3 * math.sin(2 * math.pi * 220 * t) + 0.2 * math.sin(2 * math.pi * 445 * t)
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_boss_shoot(self) -> pygame.mixer.Sound:
        """Tiefer Boss-Zap"""
        dur = 0.14
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 300 * math.exp(-5 * t)
            env = 1.0 - (t / dur)
            val = 0.4 if (t * freq) % 1.0 < 0.5 else -0.4
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_paddle_stun(self) -> pygame.mixer.Sound:
        """Elektrisches Surren / Stun"""
        dur = 0.25
        n_samples = int(self.sample_rate * dur)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 110 + (80 if (int(t * 40) % 2 == 0) else -40)
            env = 1.0 - (t / dur)
            val = 0.4 if (t * freq) % 1.0 < 0.5 else -0.4
            samples.append(val * env)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_level_win(self) -> pygame.mixer.Sound:
        """Sieges-Fanfare (C5 -> E5 -> G5 -> C6 Langes Finale)"""
        dur = 0.45
        n_samples = int(self.sample_rate * dur)
        samples = []
        notes = [(0.0, 0.1, 523.25), (0.1, 0.2, 659.25), (0.2, 0.3, 783.99), (0.3, 0.45, 1046.50)]
        for i in range(n_samples):
            t = i / self.sample_rate
            val = 0.0
            for start, end, freq in notes:
                if start <= t < end:
                    sub_t = t - start
                    sub_dur = end - start
                    env = 1.0 - (sub_t / sub_dur) * 0.3
                    val = 0.4 if (t * freq) % 1.0 < 0.5 else -0.4
                    val *= env
                    break
            samples.append(val)
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _generate_chiptune_bgm(self) -> pygame.mixer.Sound:
        """Generiert eine 4-taktige synthetische 8-Bit Chiptune Melodie als Looping-BGM."""
        bpm = 135
        beat_dur = 60.0 / bpm
        dur = beat_dur * 16  # 16 Beats (4 Takte)
        n_samples = int(self.sample_rate * dur)
        
        melody = [
            261.63, 329.63, 392.00, 523.25,
            349.23, 440.00, 523.25, 698.46,
            392.00, 493.88, 587.33, 783.99,
            523.25, 659.25, 783.99, 1046.50
        ]
        bassline = [
            130.81, 130.81, 174.61, 174.61,
            196.00, 196.00, 261.63, 261.63
        ]
        
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            beat_idx = int(t / beat_dur) % 16
            bass_idx = int(t / (beat_dur * 2)) % 8
            
            mel_freq = melody[beat_idx]
            bass_freq = bassline[bass_idx]
            
            # Melodie (Rechteckwelle)
            mel_val = 0.25 if (t * mel_freq) % 1.0 < 0.5 else -0.25
            # Bassline (Dreieckwelle)
            bass_t = (t * bass_freq) % 1.0
            bass_val = (4.0 * abs(bass_t - 0.5) - 1.0) * 0.2
            
            # Subtiler Rhythmus / Hihat
            hihat = (random.uniform(-0.15, 0.15) if (int(t * 16) % 2 == 1 and (t % 0.125) < 0.03) else 0.0)
            
            combined = mel_val + bass_val + hihat
            samples.append(combined)
            
        return pygame.mixer.Sound(io.BytesIO(self._create_wav_bytes(samples)))

    def _load_or_generate_sounds(self):
        sound_generators = {
            "paddle_hit": self._generate_paddle_hit,
            "wall_hit": self._generate_wall_hit,
            "block_hit": self._generate_block_hit,
            "explosion": self._generate_explosion,
            "powerup": self._generate_powerup,
            "powerdown": self._generate_powerdown,
            "laser": self._generate_laser,
            "boss_hit": self._generate_boss_hit,
            "boss_shoot": self._generate_boss_shoot,
            "paddle_stun": self._generate_paddle_stun,
            "level_win": self._generate_level_win,
        }
        
        sounds_dir = "sounds"
        os.makedirs(sounds_dir, exist_ok=True)
        
        for name, gen_func in sound_generators.items():
            wav_path = os.path.join(sounds_dir, f"{name}.wav")
            if os.path.exists(wav_path):
                try:
                    snd = pygame.mixer.Sound(wav_path)
                    self.sounds[name] = snd
                    print(f"[SoundManager] Custom WAV geladen: {wav_path}")
                    continue
                except Exception as e:
                    print(f"[SoundManager] Fehler beim Laden von {wav_path}: {e}")
                    
            # Fallback auf prozedurale Synthese im Speicher
            try:
                snd = gen_func()
                self.sounds[name] = snd
            except Exception as e:
                print(f"[SoundManager] Synthese-Fehler bei {name}: {e}")
                
        # Prozedurale Chiptune BGM generieren
        try:
            bgm_wav = os.path.join(sounds_dir, "bgm.wav")
            if os.path.exists(bgm_wav):
                self.bgm_sound = pygame.mixer.Sound(bgm_wav)
            else:
                self.bgm_sound = self._generate_chiptune_bgm()
        except Exception as e:
            print(f"[SoundManager] BGM-Synthese Fehler: {e}")
            self.bgm_sound = None

        self.update_volumes()

    def update_volumes(self):
        if not self.mixer_initialized:
            return
        effective_sfx = 0.0 if self.muted else self.sfx_volume
        effective_music = 0.0 if self.muted else self.music_volume
        
        for snd in self.sounds.values():
            snd.set_volume(effective_sfx)
            
        if self.bgm_sound:
            self.bgm_sound.set_volume(effective_music)

    def play_sound(self, sound_name: str):
        if not self.mixer_initialized or self.muted or self.sfx_volume <= 0:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            snd.play()

    def play_bgm(self):
        if not self.mixer_initialized or not self.bgm_sound:
            return
        if self.bgm_channel and self.bgm_channel.get_busy():
            return
        self.bgm_channel = self.bgm_sound.play(loops=-1)
        self.update_volumes()

    def stop_bgm(self):
        if self.bgm_channel:
            self.bgm_channel.stop()

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        self.update_volumes()
        return self.muted

    def set_sfx_volume(self, vol: float):
        self.sfx_volume = max(0.0, min(1.0, vol))
        self.update_volumes()

    def set_music_volume(self, vol: float):
        self.music_volume = max(0.0, min(1.0, vol))
        self.update_volumes()
