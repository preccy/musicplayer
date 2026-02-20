import math
import random
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

# Third-party dependencies:
#   pip install yt-dlp python-vlc
import vlc
import yt_dlp


class YouTubeAudioResolver:
    """Resolve direct audio stream URLs from YouTube links or IDs."""

    def __init__(self):
        self._ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
        }

    def resolve(self, query: str):
        query = query.strip()
        if not query:
            raise ValueError("Please provide a YouTube URL or video ID.")

        if "youtube.com" not in query and "youtu.be" not in query:
            query = f"https://www.youtube.com/watch?v={query}"

        with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)

        if not info or "url" not in info:
            raise RuntimeError("Could not resolve audio stream.")

        return {
            "title": info.get("title", "Unknown Track"),
            "channel": info.get("uploader", "Unknown Channel"),
            "duration": info.get("duration", 0),
            "stream_url": info["url"],
            "webpage_url": info.get("webpage_url", query),
        }


class NewJeansInspiredPlayer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NWJNS Pixel Player 💙")
        self.geometry("1040x700")
        self.configure(bg="#140c44")
        self.minsize(860, 560)

        self.palette = {
            "bg": "#140c44",
            "bg2": "#201269",
            "panel": "#3a35b8",
            "panel_deep": "#241b85",
            "ink": "#f6f7ff",
            "ink_soft": "#a9b8ff",
            "accent": "#ff68cc",
            "accent2": "#6d8cff",
            "highlight": "#ffffff",
            "mint": "#8ff8ff",
            "pink": "#ffb0ef",
            "gold": "#ffe27a",
        }

        self.resolver = YouTubeAudioResolver()
        self.instance = vlc.Instance("--no-video")
        self.player = self.instance.media_player_new()

        self.current_track = None
        self.is_playing = False
        self.visual_phase = 0.0
        self.eq_values = [0.2] * 20
        self.sparkles = []
        # Initialized before first animation tick; populated by _draw_static_scene.
        self.reel_spokes = []
        self.eq_rects = []

        self.queue = [
            {
                "title": "Hype Boy (Official)",
                "url": "https://www.youtube.com/watch?v=11cta61wi0g",
            },
            {
                "title": "Ditto (Official)",
                "url": "https://www.youtube.com/watch?v=Km71Rr9K-Bw",
            },
            {
                "title": "Super Shy (Official)",
                "url": "https://www.youtube.com/watch?v=ArmDp-zijuc",
            },
        ]

        self._build_styles()
        self._build_ui()
        self._start_animators()

    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Pixel.TFrame",
            background=self.palette["bg"],
            borderwidth=2,
            relief="solid",
        )
        style.configure(
            "Pixel.TLabel",
            background=self.palette["bg"],
            foreground=self.palette["ink"],
            font=("Courier New", 10, "bold"),
        )
        style.configure(
            "Title.TLabel",
            background=self.palette["bg"],
            foreground=self.palette["pink"],
            font=("Courier New", 18, "bold"),
        )
        style.configure(
            "Pixel.TButton",
            background=self.palette["panel"],
            foreground=self.palette["ink"],
            font=("Courier New", 10, "bold"),
            borderwidth=2,
            focusthickness=2,
            focuscolor=self.palette["pink"],
            padding=6,
        )
        style.map(
            "Pixel.TButton",
            background=[("active", self.palette["accent"]), ("pressed", self.palette["panel_deep"])],
            foreground=[("active", self.palette["highlight"])],
        )
        style.configure(
            "Pixel.Horizontal.TScale",
            background=self.palette["bg"],
            troughcolor=self.palette["panel"],
        )

    def _build_ui(self):
        root = ttk.Frame(self, style="Pixel.TFrame", padding=10)
        root.pack(fill="both", expand=True, padx=14, pady=14)

        header = ttk.Frame(root, style="Pixel.TFrame", padding=8)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(header, text="✦ BUNNY POP PLAYER ✦", style="Title.TLabel").pack(side="left")
        self.now_label = ttk.Label(header, text="Ready to sparkle ✨", style="Pixel.TLabel")
        self.now_label.pack(side="right")

        body = ttk.Frame(root, style="Pixel.TFrame", padding=8)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, style="Pixel.TFrame", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = ttk.Frame(body, style="Pixel.TFrame", padding=8)
        right.pack(side="right", fill="y")

        self.canvas = tk.Canvas(
            left,
            width=560,
            height=360,
            bg=self.palette["bg"],
            highlightthickness=2,
            highlightbackground=self.palette["accent"],
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        controls = ttk.Frame(left, style="Pixel.TFrame", padding=8)
        controls.pack(fill="x", pady=(8, 0))

        self.url_var = tk.StringVar()
        entry = ttk.Entry(
            controls,
            textvariable=self.url_var,
            font=("Courier New", 10, "bold"),
            foreground=self.palette["panel_deep"],
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        entry.insert(0, "Search dreamy song URL or video ID")

        ttk.Button(controls, text="💖 Play", style="Pixel.TButton", command=self.play_from_entry).pack(side="left")

        transport = ttk.Frame(left, style="Pixel.TFrame", padding=8)
        transport.pack(fill="x", pady=(8, 0))

        ttk.Button(transport, text="⏮ Bunny", style="Pixel.TButton", command=self.play_prev).pack(side="left", padx=4)
        ttk.Button(transport, text="▶ Love", style="Pixel.TButton", command=self.resume).pack(side="left", padx=4)
        ttk.Button(transport, text="⏸ Dream", style="Pixel.TButton", command=self.pause).pack(side="left", padx=4)
        ttk.Button(transport, text="⏭ Star", style="Pixel.TButton", command=self.play_next).pack(side="left", padx=4)

        self.volume_var = tk.DoubleVar(value=75)
        ttk.Label(transport, text="LOUDNESS", style="Pixel.TLabel").pack(side="left", padx=(12, 4))
        vol = ttk.Scale(
            transport,
            from_=0,
            to=100,
            variable=self.volume_var,
            style="Pixel.Horizontal.TScale",
            command=self._on_volume,
        )
        vol.pack(side="left", fill="x", expand=True)

        ttk.Label(right, text="KAWAII QUEUE", style="Title.TLabel").pack(anchor="w", pady=(0, 8))

        self.listbox = tk.Listbox(
            right,
            width=38,
            height=18,
            font=("Courier New", 10, "bold"),
            bg=self.palette["panel_deep"],
            fg=self.palette["ink"],
            selectbackground=self.palette["accent"],
            selectforeground=self.palette["highlight"],
            highlightthickness=2,
            highlightbackground=self.palette["accent2"],
        )
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_track)

        for item in self.queue:
            self.listbox.insert("end", item["title"])

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_scale = ttk.Scale(
            right,
            from_=0,
            to=100,
            variable=self.progress_var,
            style="Pixel.Horizontal.TScale",
            command=self._on_seek_drag,
        )
        self.progress_scale.pack(fill="x", pady=(8, 0))

        self.time_label = ttk.Label(right, text="00:00 / 00:00", style="Pixel.TLabel")
        self.time_label.pack(anchor="e", pady=(4, 0))

        self.after_idle(self._draw_static_scene)

    def _on_canvas_resize(self, _event=None):
        self.after_idle(self._draw_static_scene)

    def _draw_static_scene(self):
        self.canvas.delete("all")
        w = max(560, int(self.canvas.winfo_width()))
        h = max(360, int(self.canvas.winfo_height()))

        # Pixel candy-night backdrop
        px = 8
        for y in range(0, h, px):
            for x in range(0, w, px):
                c = self.palette["bg"] if (x // px + y // px) % 2 == 0 else self.palette["bg2"]
                self.canvas.create_rectangle(x, y, x + px, y + px, fill=c, outline=c)

        # Bubble clouds
        for cx in range(40, w, 88):
            self.canvas.create_oval(cx - 28, h - 100, cx + 28, h - 60, fill="#dce1ff", outline="#dce1ff")
            self.canvas.create_oval(cx - 10, h - 115, cx + 42, h - 60, fill="#f1f3ff", outline="#f1f3ff")

        # Scene base platform
        self.canvas.create_rectangle(40, h - 110, w - 40, h - 70, fill="#c6d0ff", outline="#edf0ff", width=2)

        # Bubble logo text (kept centered and scaled to avoid clipping)
        self.canvas.create_text(
            w // 2,
            72,
            text="NEWJEANS",
            fill=self.palette["pink"],
            font=("Courier New", 34, "bold"),
        )

        # Cute pixel hearts / charms
        for cx, cy, color in (
            (72, 74, self.palette["pink"]),
            (w - 74, 74, self.palette["pink"]),
            (w - 120, 126, self.palette["mint"]),
        ):
            self._draw_pixel_heart(cx, cy, 7, color)

        # NewJeans bunny mascot
        base_x = 82
        base_y = h - 198
        blocks = [
            (2, 0), (3, 0),
            (1, 1), (2, 1), (3, 1), (4, 1),
            (1, 2), (2, 2), (3, 2), (4, 2),
            (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
            (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
            (1, 5), (2, 5), (3, 5), (4, 5),
            (2, 6), (3, 6),
            (1, -1), (1, -2),
            (4, -1), (4, -2),
        ]
        for bx, by in blocks:
            x0 = base_x + bx * 12
            y0 = base_y + by * 12
            self.canvas.create_rectangle(x0, y0, x0 + 12, y0 + 12, fill="#fff4fd", outline="#ffb7ef")

        self.canvas.create_rectangle(base_x + 25, base_y + 44, base_x + 30, base_y + 49, fill="#4c45aa", outline="#4c45aa")
        self.canvas.create_rectangle(base_x + 42, base_y + 44, base_x + 47, base_y + 49, fill="#4c45aa", outline="#4c45aa")
        self.canvas.create_rectangle(base_x + 31, base_y + 58, base_x + 41, base_y + 61, fill="#ff89d8", outline="#ff89d8")

        # Bunny charm string
        self.canvas.create_line(base_x + 30, base_y - 28, base_x + 88, base_y - 50, fill=self.palette["ink_soft"], width=2)
        self._draw_pixel_heart(base_x + 92, base_y - 52, 5, self.palette["gold"])

        # Cassette player body
        self.deck_x = w // 2 - 140
        self.deck_y = h - 220
        self.canvas.create_rectangle(
            self.deck_x,
            self.deck_y,
            self.deck_x + 300,
            self.deck_y + 130,
            fill=self.palette["panel"],
            outline=self.palette["accent2"],
            width=3,
        )
        self.canvas.create_rectangle(
            self.deck_x + 20,
            self.deck_y + 20,
            self.deck_x + 280,
            self.deck_y + 85,
            fill="#697eff",
            outline="#9db0ff",
            width=2,
        )

        self.left_reel = self.canvas.create_oval(
            self.deck_x + 55,
            self.deck_y + 30,
            self.deck_x + 105,
            self.deck_y + 80,
            fill="#ff7cd3",
            outline="#ffd5f3",
            width=2,
        )
        self.right_reel = self.canvas.create_oval(
            self.deck_x + 195,
            self.deck_y + 30,
            self.deck_x + 245,
            self.deck_y + 80,
            fill="#ff7cd3",
            outline="#ffd5f3",
            width=2,
        )

        self.reel_spokes = []
        for center_x in (self.deck_x + 80, self.deck_x + 220):
            spokes = []
            for _ in range(4):
                spoke = self.canvas.create_line(center_x, self.deck_y + 55, center_x, self.deck_y + 35, fill="#fff4fd", width=2)
                spokes.append(spoke)
            self.reel_spokes.append((center_x, self.deck_y + 55, spokes))

        self.eq_rects = []
        eq_start_x = self.deck_x + 22
        for i in range(20):
            x0 = eq_start_x + i * 13
            rect = self.canvas.create_rectangle(x0, self.deck_y + 112, x0 + 8, self.deck_y + 112, fill="#ffe27a", outline="")
            self.eq_rects.append(rect)

        # Irregular frame tabs / ornaments to make the player shell less boxy
        tab_color = self.palette["panel_deep"]
        for points in (
            (8, 130, 38, 130, 38, 170, 8, 170),
            (w - 8, 190, w - 36, 190, w - 36, 230, w - 8, 230),
            (150, h - 8, 190, h - 8, 190, h - 36, 150, h - 36),
            (w - 230, h - 8, w - 178, h - 8, w - 178, h - 34, w - 230, h - 34),
        ):
            self.canvas.create_polygon(*points, fill=tab_color, outline=self.palette["ink_soft"], width=2)

    def _draw_pixel_heart(self, x, y, px, color):
        heart_pixels = {
            (1, 0), (3, 0),
            (0, 1), (2, 1), (4, 1),
            (0, 2), (1, 2), (3, 2), (4, 2),
            (1, 3), (2, 3), (3, 3),
            (2, 4),
        }
        for hx, hy in heart_pixels:
            x0 = x + hx * px
            y0 = y + hy * px
            self.canvas.create_rectangle(x0, y0, x0 + px, y0 + px, fill=color, outline=color)

    def _start_animators(self):
        self._update_visuals()
        self._update_progress()

    def _update_visuals(self):
        self.visual_phase += 0.12

        # Reel rotation animation
        speed = 0.4 if self.is_playing else 0.05
        theta = self.visual_phase * speed
        for center_x, center_y, spokes in self.reel_spokes:
            for idx, spoke in enumerate(spokes):
                ang = theta + (math.pi / 2) * idx
                x2 = center_x + math.cos(ang) * 18
                y2 = center_y + math.sin(ang) * 18
                self.canvas.coords(spoke, center_x, center_y, x2, y2)

        # Equalizer bounce
        for i, rect in enumerate(self.eq_rects):
            if self.is_playing:
                target = 0.15 + abs(math.sin(self.visual_phase * 0.8 + i * 0.5)) * (0.8 + random.random() * 0.2)
                self.eq_values[i] += (target - self.eq_values[i]) * 0.33
            else:
                self.eq_values[i] += (0.12 - self.eq_values[i]) * 0.2

            x0, _, x1, _ = self.canvas.coords(rect)
            y_base = self.deck_y + 122
            height = 48 * self.eq_values[i]
            self.canvas.coords(rect, x0, y_base - height, x1, y_base)

        # Sparkles
        if random.random() < 0.22:
            self.sparkles.append(
                {
                    "x": random.randint(20, int(self.canvas.winfo_width()) - 20),
                    "y": random.randint(20, 140),
                    "life": random.randint(15, 40),
                    "id": None,
                }
            )

        new_sparkles = []
        for sp in self.sparkles:
            sp["life"] -= 1
            if sp["id"]:
                self.canvas.delete(sp["id"])
            if sp["life"] > 0:
                size = 1 + (sp["life"] % 6)
                color = self.palette["highlight"] if sp["life"] % 2 else self.palette["accent2"]
                sp["id"] = self.canvas.create_text(sp["x"], sp["y"], text="✦", fill=color, font=("Courier New", 8 + size, "bold"))
                new_sparkles.append(sp)
        self.sparkles = new_sparkles

        self.after(40, self._update_visuals)

    def _update_progress(self):
        if self.player:
            length = self.player.get_length()
            current = self.player.get_time()
            if length and length > 0:
                pct = max(0, min(100, (current / length) * 100))
                self.progress_var.set(pct)
                self.time_label.config(text=f"{self._fmt_ms(current)} / {self._fmt_ms(length)}")

        self.after(300, self._update_progress)

    def _fmt_ms(self, value):
        sec = max(0, int(value // 1000))
        m, s = divmod(sec, 60)
        return f"{m:02d}:{s:02d}"

    def _on_volume(self, _=None):
        self.player.audio_set_volume(int(self.volume_var.get()))

    def _on_seek_drag(self, _=None):
        length = self.player.get_length()
        if length and length > 0:
            new_time = int((self.progress_var.get() / 100) * length)
            self.player.set_time(new_time)

    def on_select_track(self, _event=None):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        self.play_by_index(idx)

    def play_from_entry(self):
        query = self.url_var.get().strip()
        if not query:
            return

        threading.Thread(target=self._resolve_and_play, args=(query,), daemon=True).start()

    def _resolve_and_play(self, query):
        try:
            track = self.resolver.resolve(query)
            self.after(0, lambda: self._play_track(track))
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Playback Error", str(exc)))

    def _play_track(self, track):
        media = self.instance.media_new(track["stream_url"])
        self.player.set_media(media)
        self.player.play()
        self.player.audio_set_volume(int(self.volume_var.get()))

        self.current_track = track
        self.is_playing = True
        self.now_label.config(text=f"Now playing: {track['title']} — {track['channel']}")

    def play_by_index(self, idx):
        item = self.queue[idx]
        threading.Thread(target=self._resolve_and_play, args=(item["url"],), daemon=True).start()

    def play_next(self):
        if not self.listbox.size():
            return
        idx = self.listbox.curselection()[0] if self.listbox.curselection() else -1
        next_idx = (idx + 1) % self.listbox.size()
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(next_idx)
        self.listbox.activate(next_idx)
        self.play_by_index(next_idx)

    def play_prev(self):
        if not self.listbox.size():
            return
        idx = self.listbox.curselection()[0] if self.listbox.curselection() else 0
        prev_idx = (idx - 1) % self.listbox.size()
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(prev_idx)
        self.listbox.activate(prev_idx)
        self.play_by_index(prev_idx)

    def pause(self):
        self.player.pause()
        self.is_playing = False

    def resume(self):
        state = self.player.get_state()
        if state in (vlc.State.Paused, vlc.State.Stopped, vlc.State.NothingSpecial):
            self.player.play()
        self.is_playing = True


if __name__ == "__main__":
    app = NewJeansInspiredPlayer()
    app.mainloop()
