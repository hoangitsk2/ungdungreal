"""
Tkinter + pygame music player for Raspberry Pi with 15-minute shutdown.
"""
from __future__ import annotations

import os
import platform
import random
import subprocess
import time
from pathlib import Path
from typing import List, Optional

import pygame
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


SESSION_LIMIT_SECONDS = 15 * 60
DEFAULT_VOLUME = 0.7
SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac"}
MUSIC_DIR = Path(__file__).parent / "music"


class MusicPlayer:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pi Music Player")
        self.root.geometry("520x360")
        self.root.configure(bg="#0f172a")
        self.root.resizable(False, False)

        self.session_start = time.monotonic()
        self.session_limit = SESSION_LIMIT_SECONDS

        self.playlist: List[Path] = self.load_playlist()
        self.current_index: Optional[int] = 0 if self.playlist else None
        self.playing = False
        self.paused = False
        self.track_started_at: Optional[float] = None
        self.shutdown_command = os.environ.get(
            "PLAYER_SHUTDOWN_COMMAND", self.default_shutdown_command()
        )
        self.dry_run_shutdown = os.environ.get("DRY_RUN_SHUTDOWN") == "1"

        pygame.mixer.init()

        self._build_ui()
        self.volume_var.set(DEFAULT_VOLUME * 100)
        self.set_volume(DEFAULT_VOLUME * 100)

        self.auto_start_playback()
        self.root.after(500, self._monitor_playback)
        self.root.after(500, self._update_time_labels)

    def load_playlist(self) -> List[Path]:
        playlist: List[Path] = []
        if MUSIC_DIR.exists():
            for path in sorted(MUSIC_DIR.iterdir()):
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    playlist.append(path)
        return playlist

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0f172a")
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")
        style.configure(
            "Primary.TButton",
            background="#2563eb",
            foreground="white",
            padding=8,
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#1d4ed8"), ("disabled", "#1e293b")],
        )
        style.configure(
            "Secondary.TButton",
            background="#1f2937",
            foreground="white",
            padding=8,
            borderwidth=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#374151"), ("disabled", "#1e293b")],
        )

        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(
            container,
            text="Raspberry Pi Music Player",
            font=("Segoe UI", 18, "bold"),
        )
        header.pack(pady=(0, 12))

        self.track_label = ttk.Label(
            container,
            text="No track loaded",
            font=("Segoe UI", 12),
        )
        self.track_label.pack(pady=(0, 8))

        self.progress_label = ttk.Label(
            container,
            text="00:00 elapsed",
            font=("Segoe UI", 10),
        )
        self.progress_label.pack(pady=(0, 8))

        self.session_label = ttk.Label(
            container,
            text="15:00 remaining",
            font=("Segoe UI", 10, "bold"),
        )
        self.session_label.pack(pady=(0, 8))

        slider_frame = ttk.Frame(container)
        slider_frame.pack(fill=tk.X, pady=8)
        ttk.Label(slider_frame, text="Volume").pack(anchor="w")
        self.volume_var = tk.DoubleVar(value=DEFAULT_VOLUME * 100)
        volume_slider = ttk.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            command=self.set_volume,
        )
        volume_slider.pack(fill=tk.X, pady=(4, 0))

        controls = ttk.Frame(container)
        controls.pack(pady=12)

        self.play_button = ttk.Button(
            controls, text="Play", style="Primary.TButton", command=self.play
        )
        self.play_button.grid(row=0, column=0, padx=5)

        self.pause_button = ttk.Button(
            controls,
            text="Pause",
            style="Secondary.TButton",
            command=self.toggle_pause,
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.stop_button = ttk.Button(
            controls, text="Stop", style="Secondary.TButton", command=self.stop
        )
        self.stop_button.grid(row=0, column=2, padx=5)

        self.next_button = ttk.Button(
            controls,
            text="Random",
            style="Secondary.TButton",
            command=self.play_random_track,
        )
        self.next_button.grid(row=0, column=3, padx=5)

        self.load_button = ttk.Button(
            container,
            text="Add or change track",
            style="Primary.TButton",
            command=self.load_track_from_dialog,
        )
        self.load_button.pack(pady=(6, 0))

    def set_volume(self, value: str | float) -> None:
        try:
            vol = float(value) / 100.0
        except (TypeError, ValueError):
            return
        vol = max(0.0, min(1.0, vol))
        pygame.mixer.music.set_volume(vol)

    def formatted_track_name(self, path: Path) -> str:
        return path.stem.replace("_", " ")

    def play(self) -> None:
        if self.current_index is None:
            messagebox.showinfo("No music", "Please add a music file to start playback.")
            return

        track = self.playlist[self.current_index]
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
            self.playing = True
            self.paused = False
            self.track_started_at = time.monotonic()
            self.track_label.config(text=f"Playing: {self.formatted_track_name(track)}")
            self.pause_button.config(text="Pause")
        except pygame.error as exc:
            messagebox.showerror("Playback error", f"Could not play {track}: {exc}")
            self.playing = False

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        self.track_started_at = None
        self.progress_label.config(text="Stopped")

    def toggle_pause(self) -> None:
        if not self.playing:
            return
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self.pause_button.config(text="Pause")
        else:
            pygame.mixer.music.pause()
            self.paused = True
            self.pause_button.config(text="Resume")

    def play_random_track(self) -> None:
        if not self.playlist:
            messagebox.showinfo("No music", "Please add music files first.")
            return
        if len(self.playlist) == 1:
            self.current_index = 0
        else:
            choices = list(range(len(self.playlist)))
            if self.current_index is not None:
                choices.remove(self.current_index)
            self.current_index = random.choice(choices)
        self.play()

    def load_track_from_dialog(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Choose a music file",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg *.flac"), ("All files", "*.*")],
        )
        if not file_path:
            return
        path = Path(file_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            messagebox.showerror("Unsupported", "Please choose an MP3, WAV, OGG, or FLAC file.")
            return
        if path not in self.playlist:
            self.playlist.append(path)
        self.current_index = self.playlist.index(path)
        self.play()

    def _monitor_playback(self) -> None:
        if self.playing and not self.paused and not pygame.mixer.music.get_busy():
            self._on_track_end()
        self.root.after(500, self._monitor_playback)

    def _on_track_end(self) -> None:
        elapsed = time.monotonic() - self.session_start
        remaining = self.session_limit - elapsed
        if remaining <= 0:
            self._shutdown()
            return
        # Continue with another random track if possible.
        if self.playlist:
            self.play_random_track()
        else:
            self.playing = False
            self.track_label.config(text="No track loaded")

    def _update_time_labels(self) -> None:
        # Track progress
        if self.playing and self.track_started_at is not None:
            elapsed_ms = pygame.mixer.music.get_pos()
            if elapsed_ms < 0:
                elapsed_ms = 0
            elapsed = int(elapsed_ms // 1000)
            minutes, seconds = divmod(elapsed, 60)
            self.progress_label.config(text=f"{minutes:02d}:{seconds:02d} elapsed")
        else:
            self.progress_label.config(text="Not playing")

        # Session remaining
        elapsed_session = time.monotonic() - self.session_start
        remaining = max(0, int(self.session_limit - elapsed_session))
        rem_minutes, rem_seconds = divmod(remaining, 60)
        self.session_label.config(
            text=f"{rem_minutes:02d}:{rem_seconds:02d} remaining (auto shutdown)",
        )
        if remaining <= 0:
            self._shutdown()
            return

        self.root.after(500, self._update_time_labels)

    def _shutdown(self) -> None:
        if self.playing:
            pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        if self.dry_run_shutdown:
            print("[DRY RUN] Shutdown command skipped.")
            messagebox.showinfo("Shutdown", "15 minutes elapsed. Shutdown suppressed (dry run).")
            return
        try:
            subprocess.Popen(self.shutdown_command.split())
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("Shutdown failed", f"Could not shutdown: {exc}")

    def default_shutdown_command(self) -> str:
        if platform.system().lower().startswith("win"):
            return "shutdown /s /t 0"
        return "sudo shutdown -h now"

    def auto_start_playback(self) -> None:
        if self.current_index is not None:
            self.play()
        else:
            self.track_label.config(
                text="Add a song to start playback automatically",
            )


def main() -> None:
    root = tk.Tk()
    MusicPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
