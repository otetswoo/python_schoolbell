#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
from pathlib import Path


class MusicPlayer:
    def __init__(self, sound_player=None, logger=None):
        self.music_folders = []
        self.played_today = set()
        self.last_play_time = 0
        self.delay_minutes = 2
        self.sound_player = sound_player
        self.logger = logger
        self.is_music_playing_callback = None  # Callback для уведомления об окончании музыки
        
    @property
    def music_folder(self):
        return self.music_folders[0] if self.music_folders else None

    def set_music_folders(self, folders):
        valid_folders = []
        for folder in folders or []:
            p = Path(folder)
            if p.exists() and p.is_dir():
                valid_folders.append(p)
        if valid_folders:
            self.music_folders = valid_folders
            self.played_today.clear()
            return True
        return False

    def set_music_folder(self, folder):
        return self.set_music_folders([folder] if folder else [])
    
    def get_audio_files(self):
        if not self.music_folders:
            return []
        
        extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma"}
        files = []
        for folder in self.music_folders:
            if not folder.exists():
                continue
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in extensions:
                    files.append(f)
        return files
    
    def get_next_track(self):
        files = self.get_audio_files()
        if not files:
            return None
        
        available = [f for f in files if str(f) not in self.played_today]
        if not available:
            self.played_today.clear()
            available = files
        
        track = random.choice(available)
        self.played_today.add(str(track))
        return track
    
    def can_play(self):
        now = time.time()
        return now - self.last_play_time > self.delay_minutes * 60
    
    def mark_played(self):
        self.last_play_time = time.time()
    
    def reset_daily(self):
        self.played_today.clear()
    
    def play_random(self, folder=None):
        if folder:
            self.set_music_folder(folder)
        
        track = self.get_next_track()
        if track and self.sound_player:
            self.sound_player.play_music(str(track))
            self.mark_played()
            return True
        return False
    
    def stop(self):
        """Остановка музыки через общий SoundPlayer"""
        if self.sound_player:
            self.sound_player.stop_all()
    
    def check_music_finished(self):
        """Проверяет, закончилась ли музыка, и уведомляет через callback."""
        if self.sound_player and not self.sound_player.is_playing("music"):
            if self.is_music_playing_callback:
                self.is_music_playing_callback()
