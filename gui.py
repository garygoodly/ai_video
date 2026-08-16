import os
import sys
import threading
import subprocess
from datetime import date
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.chdir(PROJECT_ROOT)

from kvf.core.session_controller import SessionController
from kvf.services.session_service import SessionService
from kvf.utils.yaml_loader import load_yaml


class ScrollableFrame(ttk.Frame):
    """通用可滾動容器，解決表單過長擠壓底部按鈕的問題"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_content = ttk.Frame(self.canvas)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scrollable_content.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_content.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class VideoFactoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Knowledge Video Factory")
        self.geometry("1180x880")
        self.minsize(980, 720)

        # 1. 啟動時自動最大化視窗 (跨平台支援)
        try:
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                pass

        settings = load_yaml(str(PROJECT_ROOT / "config" / "settings.yaml"))
        self.controller = SessionController(settings, PROJECT_ROOT)
        self.workspace: Path | None = None
        self.stage: str | None = None

        self._configure_style()
        self.show_home()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=12)
        style.configure("TButton", padding=8)

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear()
        self.workspace = None
        self.stage = None

        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Knowledge Video Factory", style="Title.TLabel").pack(pady=(80, 12))
        ttk.Label(
            frame,
            text="Create a new video session or continue an unfinished one.",
            font=("Segoe UI", 12),
        ).pack(pady=(0, 36))

        buttons = ttk.Frame(frame)
        buttons.pack()
        ttk.Button(
            buttons,
            text="Resume Last Session",
            style="Primary.TButton",
            command=self.show_resume,
            width=24,
        ).grid(row=0, column=0, padx=10)
        ttk.Button(
            buttons,
            text="Start New Session",
            style="Primary.TButton",
            command=self.show_new_session,
            width=24,
        ).grid(row=0, column=1, padx=10)

    def show_new_session(self):
        self.clear()
        frame = ttk.Frame(self, padding=36)
        frame.pack(fill="both", expand=True)

        ttk.Button(frame, text="← Back", command=self.show_home).pack(anchor="w")

        scroll_area = ScrollableFrame(frame)
        scroll_area.pack(fill="both", expand=True, pady=10)
        content = scroll_area.scrollable_content

        ttk.Label(content, text="Start New Session", style="Title.TLabel").pack(pady=(20, 12))
        ttk.Label(
            content,
            text=("Choose the audience edition first. The research prompt, writing language, "
                  "narration voice, and subtitles will follow that regional profile."),
            font=("Segoe UI", 11), wraplength=760, justify="center",
        ).pack(pady=(0, 22))

        form = ttk.Frame(content)
        form.pack()
        editions = self.controller.editions.all()
        labels_by_key = {key: profile["label"] for key, profile in editions.items()}
        key_by_label = {label: key for key, label in labels_by_key.items()}

        ttk.Label(form, text="Audience edition", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=(8, 5)
        )
        edition_var = tk.StringVar(value=labels_by_key.get("taiwan", "Taiwan"))
        edition_box = ttk.Combobox(
            form, textvariable=edition_var,
            values=[labels_by_key[key] for key in ("taiwan", "japan", "global") if key in labels_by_key],
            state="readonly", width=34, font=("Segoe UI", 11),
        )
        edition_box.grid(row=1, column=0, sticky="w", pady=(0, 8))

        edition_description = tk.StringVar()
        ttk.Label(
            form, textvariable=edition_description, foreground="#555555",
            wraplength=650, justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(0, 18))

        ttk.Label(form, text="Project name", style="Heading.TLabel").grid(
            row=3, column=0, sticky="w", pady=8
        )
        project_entry = ttk.Entry(form, width=58, font=("Segoe UI", 12))
        project_entry.grid(row=4, column=0, pady=(0, 10))

        def update_edition(event=None):
            key = key_by_label.get(edition_var.get(), "global")
            profile = self.controller.editions.get(key)
            edition_description.set(
                f'{profile["output_language"]} • Default voice: {profile["default_voice"]}\n'
                f'{profile["audience_note"]}'
            )
            project_entry.delete(0, "end")
            project_entry.insert(0, f'{date.today().isoformat()} {profile["default_project_suffix"]}')
            project_entry.select_range(0, "end")

        edition_box.bind("<<ComboboxSelected>>", update_edition)
        update_edition()
        project_entry.focus_set()

        ttk.Label(
            form,
            text="The selected edition is saved with the session and can be resumed later.",
            foreground="#666666",
        ).grid(row=5, column=0, sticky="w", pady=(0, 24))

        def create_session():
            try:
                edition_key = key_by_label.get(edition_var.get(), "global")
                self.workspace = self.controller.create_session(project_entry.get(), edition_key)
                self.open_current_stage()
            except Exception as exc:
                messagebox.showerror("Cannot create session", str(exc))

        project_entry.bind("<Return>", lambda event: create_session())
        ttk.Button(
            form,
            text="Create Project",
            style="Primary.TButton",
            command=create_session,
        ).grid(row=6, column=0, pady=(0, 20))

    def show_resume(self):
        self.clear()
        frame = ttk.Frame(self, padding=28)
        frame.pack(fill="both", expand=True)

        header = ttk.Frame(frame)
        header.pack(side="top", fill="x")
        ttk.Button(header, text="← Back", command=self.show_home).pack(anchor="w")
        ttk.Label(header, text="Resume Session", style="Title.TLabel").pack(anchor="w", pady=(12, 16))

        footer = ttk.Frame(frame, padding=(0, 12, 0, 0))
        footer.pack(side="bottom", fill="x")

        def resume_selected(event=None):
            selection = tree.selection()
            if not selection:
                messagebox.showinfo("Select a session", "Choose a session to continue.")
                return
            self.workspace = workspace_by_id[selection[0]]
            self.open_current_stage()

        ttk.Button(
            footer,
            text="Continue Selected Session",
            style="Primary.TButton",
            command=resume_selected,
        ).pack(anchor="center")

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(side="top", fill="both", expand=True)

        columns = ("project", "edition", "stage", "progress", "updated")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        tree.heading("project", text="Project")
        tree.heading("edition", text="Edition")
        tree.heading("stage", text="Continue From")
        tree.heading("progress", text="Progress")
        tree.heading("updated", text="Last Updated")
        tree.column("project", width=350)
        tree.column("edition", width=110, anchor="center")
        tree.column("stage", width=160)
        tree.column("progress", width=100, anchor="center")
        tree.column("updated", width=220)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        sessions = self.controller.sessions.list_sessions()
        workspace_by_id = {}
        for index, session in enumerate(sessions):
            item_id = f"session-{index}"
            workspace_by_id[item_id] = session["workspace"]
            updated = session.get("updated_at", "").replace("T", " ")[:19]
            tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    session.get("name", session.get("id", "Unknown")),
                    session.get("edition_label", "Global"),
                    session["current_stage"].replace("_", " ").title(),
                    f'{session["progress_percent"]}%',
                    updated,
                ),
            )

        tree.bind("<Double-1>", resume_selected)

        if not sessions:
            ttk.Label(frame, text="No saved sessions were found.").pack(pady=16)

    def open_current_stage(self):
        if self.workspace is None:
            return
        inspection = self.controller.sessions.inspect(self.workspace)
        current = inspection["current_stage"]
        if current in SessionService.MANUAL_STAGES:
            self.show_manual_stage(current)
        elif current == "complete":
            self.show_complete()
        else:
            self.show_automatic_stage()

    def show_manual_stage(self, stage: str):
        self.clear()
        self.stage = stage
        try:
            prompt_path = self.controller.prepare_stage(self.workspace, stage)
            prompt = prompt_path.read_text(encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("Cannot prepare stage", str(exc))
            self.show_home()
            return

        metadata = SessionService._read_metadata(self.workspace)

        header = ttk.Frame(self, padding=(24, 14, 24, 10))
        header.pack(side="top", fill="x")
        ttk.Button(header, text="Sessions", command=self.show_home).pack(side="left")
        ttk.Label(header, text=metadata["name"], style="Heading.TLabel").pack(side="left", padx=20)
        ttk.Label(
            header,
            text=f'{metadata.get("edition_label", "Global")} • {metadata.get("output_language", "English")} • Step: {stage.title()}',
        ).pack(side="right")

        # 固定底部按鈕列
        footer = ttk.Frame(self, padding=(24, 8, 24, 14))
        footer.pack(side="bottom", fill="x")

        status_var = tk.StringVar(value="Waiting for JSON. It will be checked and saved automatically.")
        status_label = ttk.Label(footer, textvariable=status_var)
        status_label.pack(side="left", fill="x", expand=True)

        next_button = ttk.Button(
            footer,
            text="Next →",
            style="Primary.TButton",
            state="disabled",
        )
        next_button.pack(side="right")

        # 中間工作區
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(side="top", fill="both", expand=True, padx=24, pady=(0, 6))
        left = ttk.Frame(pane, padding=10)
        right = ttk.Frame(pane, padding=10)
        pane.add(left, weight=1)
        pane.add(right, weight=1)

        left_header = ttk.Frame(left)
        left_header.pack(fill="x", pady=(0, 8))
        ttk.Label(left_header, text="1. Copy prompt to ChatGPT", style="Heading.TLabel").pack(side="left")
        prompt_text = tk.Text(left, wrap="word", font=("Consolas", 10), padx=10, pady=10)
        prompt_text.insert("1.0", prompt)
        prompt_text.configure(state="disabled")
        prompt_text.pack(fill="both", expand=True)

        def copy_prompt():
            self.clipboard_clear()
            self.clipboard_append(prompt)
            self.update()
            copy_button.configure(text="Copied ✓")
            self.after(1600, lambda: copy_button.configure(text="Copy Prompt"))

        copy_button = ttk.Button(left_header, text="Copy Prompt", command=copy_prompt)
        copy_button.pack(side="right")

        ttk.Label(right, text="2. Paste ChatGPT JSON", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        result_text = tk.Text(right, wrap="none", font=("Consolas", 10), padx=10, pady=10, undo=True)
        existing = self.workspace / stage / f"{stage}.json"
        if existing.exists():
            result_text.insert("1.0", existing.read_text(encoding="utf-8"))
        result_text.pack(fill="both", expand=True)

        validation_job = None
        last_saved = {"content": None}

        def open_next():
            next_stage = self.controller.next_manual_stage(self.workspace)
            if next_stage:
                self.show_manual_stage(next_stage)
            else:
                self.show_automatic_stage()

        next_button.configure(command=open_next)

        def validate_and_save():
            nonlocal validation_job
            validation_job = None
            content = result_text.get("1.0", "end").strip()
            if not content:
                status_var.set("Waiting for JSON. It will be checked and saved automatically.")
                next_button.configure(state="disabled")
                return
            try:
                normalized = self.controller.normalize_and_validate(stage, content)
            except Exception as exc:
                details = str(exc).strip() or "Invalid JSON or schema"
                lines = [line.strip() for line in details.splitlines() if line.strip()]
                if len(lines) > 1:
                    summary = " | ".join(lines[:4])
                    if len(lines) > 4:
                        summary += " | ..."
                else:
                    summary = lines[0] if lines else "Invalid JSON or schema"
                status_var.set(f"Not valid yet: {summary}")
                next_button.configure(state="disabled")
                return
            if normalized != last_saved["content"]:
                try:
                    self.controller.save_and_validate(self.workspace, stage, normalized)
                    last_saved["content"] = normalized
                except Exception as exc:
                    status_var.set(f"Could not save: {exc}")
                    next_button.configure(state="disabled")
                    return
            status_var.set("✓ Valid JSON saved. The next stage is ready.")
            next_button.configure(state="normal")

        def schedule_validation(event=None):
            nonlocal validation_job
            next_button.configure(state="disabled")
            status_var.set("Checking JSON...")
            if validation_job is not None:
                self.after_cancel(validation_job)
            validation_job = self.after(650, validate_and_save)

        result_text.bind("<<Paste>>", schedule_validation)
        result_text.bind("<KeyRelease>", schedule_validation)
        if existing.exists():
            self.after(100, validate_and_save)

    def show_automatic_stage(self):
        self.clear()
        metadata = SessionService._read_metadata(self.workspace)
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Automatic Production", style="Title.TLabel").pack(pady=(90, 12))
        ttk.Label(frame, text=metadata["name"], style="Heading.TLabel").pack(pady=(0, 25))
        status_var = tk.StringVar(value="Preparing automatic stages...")
        ttk.Label(frame, textvariable=status_var, font=("Segoe UI", 12)).pack(pady=12)
        progress = ttk.Progressbar(frame, mode="indeterminate", length=520)
        progress.pack(pady=18)
        progress.start(12)

        def update_status(label):
            self.after(0, status_var.set, label)

        def worker():
            try:
                self.controller.run_automatic(self.workspace, update_status)
            except Exception as exc:
                self.after(0, progress.stop)
                self.after(0, messagebox.showerror, "Production stopped", str(exc))
                self.after(0, self.show_resume)
                return
            self.after(0, progress.stop)
            self.after(0, self.show_complete)

        threading.Thread(target=worker, daemon=True).start()

    def show_modify(self):
        self.clear()
        metadata = SessionService._read_metadata(self.workspace)
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        # 1. 頂部標題與說明
        header = ttk.Frame(frame)
        header.pack(side="top", fill="x")
        ttk.Button(header, text="← Back", command=self.show_complete).pack(anchor="w")
        ttk.Label(header, text="Modify Existing Video", style="Title.TLabel").pack(anchor="w", pady=(10, 4))
        ttk.Label(
            header,
            text=("Change voice, subtitle appearance, segmentation, or media behavior. "
                  "Only the required downstream stages are rebuilt."),
            wraplength=1050, font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 8))

        # 2. 底部固定動作列 (Fixed Footer) - 優先 Pack，確保永不被擠壓
        footer = ttk.Frame(frame, padding=(0, 10, 0, 0))
        footer.pack(side="bottom", fill="x")

        status_var = tk.StringVar(value="Ready.")
        ttk.Label(footer, textvariable=status_var, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 2))
        progress = ttk.Progressbar(footer, mode="indeterminate")
        progress.pack(anchor="w", fill="x", pady=(0, 6))

        rebuild_button = ttk.Button(
            footer, text="Regenerate Selected Outputs",
            style="Primary.TButton",
        )
        rebuild_button.pack(anchor="w")

        # 3. 中間滾動區域 (Scrollable Content)
        scroll_container = ScrollableFrame(frame)
        scroll_container.pack(side="top", fill="both", expand=True, pady=6)
        scroll_content = scroll_container.scrollable_content

        body = ttk.Panedwindow(scroll_content, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, padding=8)
        right = ttk.Frame(body, padding=8)
        body.add(left, weight=1)
        body.add(right, weight=1)

        options = ttk.LabelFrame(left, text="Outputs to regenerate", padding=12)
        options.pack(fill="x")
        labels = {
            "media": "Media images",
            "voice": "Narration voice",
            "subtitle": "Subtitles",
            "timeline": "Timeline",
            "video": "Final video only",
        }
        selected_vars = {}
        for row, (key, label) in enumerate(labels.items()):
            variable = tk.BooleanVar(value=False)
            selected_vars[key] = variable
            ttk.Checkbutton(options, text=label, variable=variable).grid(
                row=row, column=0, sticky="w", pady=3
            )

        edition_profile = self.controller.editions.get(metadata.get("edition", "global"))
        voice_frame = ttk.LabelFrame(left, text="Voice", padding=12)
        voice_frame.pack(fill="x", pady=10)

        engine_profiles = edition_profile.get("voice_engines", {})
        if not engine_profiles:
            engine_profiles = {
                "edge": {
                    "label": "Microsoft Edge TTS",
                    "voices": edition_profile.get("voices", [edition_profile.get("default_voice", "en-US-AndrewNeural")]),
                }
            }
        engine_labels = {key: value.get("label", key) for key, value in engine_profiles.items()}
        engine_by_label = {label: key for key, label in engine_labels.items()}
        current_engine = metadata.get("voice_engine", "edge")
        engine_var = tk.StringVar(value=engine_labels.get(current_engine, current_engine))
        voice_var = tk.StringVar(value=metadata.get("voice", edition_profile.get("default_voice", "en-US-AndrewNeural")))

        ttk.Label(voice_frame, text="Engine").grid(row=0, column=0, sticky="w")
        ttk.Label(voice_frame, text="Speaker").grid(row=0, column=1, sticky="w", padx=(12, 0))
        engine_box = ttk.Combobox(
            voice_frame, textvariable=engine_var, values=list(engine_by_label),
            width=24, state="readonly"
        )
        engine_box.grid(row=1, column=0, sticky="w", pady=(2, 8))
        voice_box = ttk.Combobox(voice_frame, textvariable=voice_var, width=30, state="readonly")
        voice_box.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(2, 8))

        def refresh_voice_choices(event=None):
            engine_key = engine_by_label.get(engine_var.get(), "edge")
            choices = engine_profiles.get(engine_key, {}).get("voices", [])
            voice_box.configure(values=choices)
            if voice_var.get() not in choices and choices:
                voice_var.set(choices[0])

        engine_box.bind("<<ComboboxSelected>>", refresh_voice_choices)
        refresh_voice_choices()

        rate_var = tk.StringVar(value=metadata.get("voice_rate", "+0%"))
        pitch_var = tk.StringVar(value=metadata.get("voice_pitch", "+0Hz"))
        ttk.Label(voice_frame, text="Speed").grid(row=2, column=0, sticky="w")
        ttk.Label(voice_frame, text="Pitch").grid(row=2, column=1, sticky="w", padx=(12, 0))
        ttk.Combobox(
            voice_frame, textvariable=rate_var,
            values=["-20%", "-10%", "+0%", "+10%", "+20%"],
            width=12, state="readonly"
        ).grid(row=3, column=0, sticky="w")
        ttk.Combobox(
            voice_frame, textvariable=pitch_var,
            values=["-10Hz", "-5Hz", "+0Hz", "+5Hz", "+10Hz"],
            width=12, state="readonly"
        ).grid(row=3, column=1, sticky="w", padx=(12, 0))

        preview_samples = {
            "zh-TW": "今天台股受到美國科技股走勢影響，加權指數盤中震盪。",
            "ja-JP": "本日の日経平均は米国市場の流れを受けて変動しました。",
            "en-US": "Today, global markets are reacting to rates, earnings, and currency moves.",
        }
        voice_preview_status = tk.StringVar(value="Preview uses the selected engine, speaker, speed, and pitch.")
        ttk.Label(voice_frame, textvariable=voice_preview_status, foreground="#555555", wraplength=470).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 4)
        )

        def play_voice_preview():
            preview_button.configure(state="disabled")
            voice_preview_status.set("Generating preview...")
            engine_key = engine_by_label.get(engine_var.get(), "edge")
            text = preview_samples.get(metadata.get("language_code", "en-US"), preview_samples["en-US"])

            def worker():
                try:
                    path = self.controller.generate_voice_preview(
                        self.workspace, engine=engine_key, voice=voice_var.get(),
                        rate=rate_var.get(), pitch=pitch_var.get(), text=text,
                    )
                    subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    self.after(0, voice_preview_status.set, "Playing voice preview.")
                except Exception as exc:
                    self.after(0, voice_preview_status.set, f"Preview failed: {exc}")
                finally:
                    self.after(0, preview_button.configure, {"state": "normal"})

            threading.Thread(target=worker, daemon=True).start()

        preview_button = ttk.Button(voice_frame, text="▶ Play Voice Preview", command=play_voice_preview)
        preview_button.grid(row=5, column=0, columnspan=2, sticky="w", pady=(3, 0))

        narration_frame = ttk.LabelFrame(left, text="Narration & subtitles", padding=12)
        narration_frame.pack(fill="x", pady=(0, 10))
        narration_mode_var = tk.StringVar(value=metadata.get("narration_mode", "continuous"))
        subtitles_enabled_var = tk.BooleanVar(value=bool(metadata.get("subtitles_enabled", False)))
        ttk.Radiobutton(
            narration_frame,
            text="Continuous narration — speak the approved article naturally",
            variable=narration_mode_var, value="continuous",
        ).pack(anchor="w")
        ttk.Radiobutton(
            narration_frame,
            text="Cue-synced narration — exact subtitle timing (legacy mode)",
            variable=narration_mode_var, value="cue_synced",
        ).pack(anchor="w", pady=(3, 0))
        ttk.Checkbutton(
            narration_frame, text="Enable burned-in subtitles",
            variable=subtitles_enabled_var,
        ).pack(anchor="w", pady=(8, 0))
        ttk.Label(
            narration_frame,
            text=("For the most natural speech, use Continuous narration with subtitles off. "
                  "If subtitles are enabled, choose Cue-synced narration for exact alignment."),
            foreground="#555555", wraplength=470,
        ).pack(anchor="w", pady=(5, 0))

        media_settings = metadata.get("media_settings", {})
        media_frame = ttk.LabelFrame(left, text="Visual behavior", padding=12)
        media_frame.pack(fill="x", pady=(0, 10))
        persistence_var = tk.StringVar(
            value=media_settings.get("visual_persistence", "topic")
        )
        ttk.Radiobutton(
            media_frame, text="One precise visual per topic/section",
            variable=persistence_var, value="topic"
        ).pack(anchor="w")
        ttk.Radiobutton(
            media_frame, text="Change visual for every storyboard scene",
            variable=persistence_var, value="scene"
        ).pack(anchor="w")
        prefer_charts_var = tk.BooleanVar(
            value=bool(media_settings.get("prefer_market_charts", True))
        )
        ttk.Checkbutton(
            media_frame,
            text="Prefer current historical charts for recognized market indices",
            variable=prefer_charts_var,
        ).pack(anchor="w", pady=(6, 0))

        subtitle_settings = metadata.get("subtitle_settings", {})
        subtitle_style = metadata.get("subtitle_style", {})
        subtitle_frame = ttk.LabelFrame(right, text="Subtitle format", padding=12)
        subtitle_frame.pack(fill="x")

        style_var = tk.StringVar(value=subtitle_style.get("preset", "Compact"))
        font_var = tk.StringVar(
            value=subtitle_style.get("font_name", edition_profile.get("default_subtitle_font", "Arial"))
        )
        ttk.Label(subtitle_frame, text="Size preset").grid(row=0, column=0, sticky="w")
        ttk.Label(subtitle_frame, text="Font").grid(row=0, column=1, sticky="w", padx=(12, 0))
        style_box = ttk.Combobox(
            subtitle_frame, textvariable=style_var,
            values=["Compact", "Standard", "Large"], width=14, state="readonly"
        )
        style_box.grid(row=1, column=0, sticky="w", pady=(2, 8))
        fonts = edition_profile.get("subtitle_fonts", [
            "Microsoft JhengHei", "Noto Sans CJK TC", "Yu Gothic", "Meiryo",
            "Arial", "Segoe UI", "Tahoma", "Verdana", "Times New Roman"
        ])
        font_box = ttk.Combobox(
            subtitle_frame, textvariable=font_var, values=fonts,
            width=24, state="readonly"
        )
        font_box.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(2, 8))

        is_cjk = metadata.get("language_code", "en-US") in {"zh-TW", "zh-CN", "ja-JP"}
        max_chars_var = tk.IntVar(
            value=int(subtitle_settings.get("max_characters", edition_profile.get("subtitle_max_characters", 18)))
        )
        min_chars_var = tk.IntVar(
            value=int(subtitle_settings.get("min_characters", edition_profile.get("subtitle_min_characters", 6)))
        )
        max_words_var = tk.IntVar(value=int(subtitle_settings.get("max_words", 10)))
        if is_cjk:
            ttk.Label(subtitle_frame, text="Target maximum characters").grid(row=2, column=0, sticky="w")
            ttk.Label(subtitle_frame, text="Minimum characters before merge").grid(row=2, column=1, sticky="w", padx=(12, 0))
            ttk.Spinbox(subtitle_frame, from_=8, to=30, textvariable=max_chars_var, width=8).grid(row=3, column=0, sticky="w")
            ttk.Spinbox(subtitle_frame, from_=2, to=15, textvariable=min_chars_var, width=8).grid(row=3, column=1, sticky="w", padx=(12, 0))
        else:
            ttk.Label(subtitle_frame, text="Maximum words per cue").grid(row=2, column=0, sticky="w")
            ttk.Spinbox(subtitle_frame, from_=4, to=18, textvariable=max_words_var, width=8).grid(row=3, column=0, sticky="w")

        preview = tk.Frame(right, bg="#182331", height=200)
        preview.pack(fill="x", pady=12)
        preview.pack_propagate(False)
        preview_text = tk.Label(
            preview, bg="#182331", fg="white", justify="center",
            wraplength=520, bd=0
        )
        preview_text.pack(side="bottom", fill="x", padx=24, pady=28)
        ttk.Label(right, text="Live subtitle preview (bottom-safe placement)").pack(anchor="w")

        samples = {
            "zh-TW": "台股今日上漲43682點，核心通膨為0.16%",
            "ja-JP": "日経平均は上昇し、ドル円は157.25円となりました",
            "en-US": "The S&P 500 rose 0.16% while yields moved lower",
        }
        preset_sizes = {"Compact": 22, "Standard": 28, "Large": 36}

        def update_preview(event=None):
            sample = samples.get(metadata.get("language_code", "en-US"), samples["en-US"])
            preview_text.configure(
                text=sample,
                font=(font_var.get(), preset_sizes.get(style_var.get(), 22), "bold"),
            )

        style_box.bind("<<ComboboxSelected>>", update_preview)
        font_box.bind("<<ComboboxSelected>>", update_preview)
        update_preview()

        tools = ttk.LabelFrame(right, text="Open generated files", padding=12)
        tools.pack(fill="x", pady=(8, 0))

        def open_path(path: Path):
            if not path.exists():
                messagebox.showinfo("File not found", str(path))
                return
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')

        ttk.Button(tools, text="Subtitle SRT", command=lambda: open_path(self.controller.sessions.project_dir_for(self.workspace) / "subtitle.srt")).pack(side="left", padx=(0, 6))
        ttk.Button(tools, text="Script JSON", command=lambda: open_path(self.controller.sessions.project_dir_for(self.workspace) / "script.json")).pack(side="left", padx=6)
        ttk.Button(tools, text="Media Folder", command=lambda: open_path(self.workspace / "assets" / "rendered")).pack(side="left", padx=6)

        def rebuild():
            selected = {key for key, variable in selected_vars.items() if variable.get()}
            requested_subtitle_settings = {
                "max_words": int(max_words_var.get()),
                "max_characters": int(max_chars_var.get()),
                "min_characters": int(min_chars_var.get()),
                "max_duration_seconds": 4.5,
                "source": "approved_script_exact",
            }
            requested_style = {"preset": style_var.get(), "font_name": font_var.get()}
            requested_media = {
                "visual_persistence": persistence_var.get(),
                "prefer_market_charts": bool(prefer_charts_var.get()),
                "strict_precision": True,
            }
            selected_engine = engine_by_label.get(engine_var.get(), "edge")
            voice_changed = (
                selected_engine != metadata.get("voice_engine", "edge") or
                voice_var.get() != metadata.get("voice") or
                rate_var.get() != metadata.get("voice_rate", "+0%") or
                pitch_var.get() != metadata.get("voice_pitch", "+0Hz")
            )
            narration_changed = narration_mode_var.get() != metadata.get("narration_mode", "continuous")
            subtitles_changed = bool(subtitles_enabled_var.get()) != bool(metadata.get("subtitles_enabled", False))
            if subtitles_enabled_var.get() and narration_mode_var.get() == "continuous":
                messagebox.showwarning(
                    "Choose narration mode",
                    "Continuous narration is intentionally independent of subtitle chunks. "
                    "Turn subtitles off, or select Cue-synced narration for exact subtitle alignment.",
                )
                return
            if voice_changed or narration_changed:
                selected.add("voice")
            if subtitles_changed:
                selected.add("subtitle")
            if requested_subtitle_settings != subtitle_settings and subtitles_enabled_var.get():
                selected.add("voice")
            if requested_style != subtitle_style:
                selected.add("video")
            if requested_media != media_settings:
                selected.add("media")
            if not selected:
                messagebox.showinfo("No changes selected", "Choose an output or change a setting.")
                return

            rebuild_button.configure(state="disabled")
            progress.start(12)

            def update_status(label):
                self.after(0, status_var.set, label)

            def worker():
                try:
                    self.controller.regenerate(
                        self.workspace, selected,
                        voice=voice_var.get(),
                        voice_engine=selected_engine,
                        voice_rate=rate_var.get(),
                        voice_pitch=pitch_var.get(),
                        subtitle_settings=requested_subtitle_settings,
                        subtitle_style=requested_style,
                        media_settings=requested_media,
                        narration_mode=narration_mode_var.get(),
                        subtitles_enabled=bool(subtitles_enabled_var.get()),
                        progress_callback=update_status,
                    )
                except Exception as exc:
                    self.after(0, progress.stop)
                    self.after(0, rebuild_button.configure, {"state": "normal"})
                    self.after(0, messagebox.showerror, "Regeneration stopped", str(exc))
                    return
                self.after(0, progress.stop)
                self.after(0, self.show_complete)

            threading.Thread(target=worker, daemon=True).start()

        rebuild_button.configure(command=rebuild)

    def show_complete(self):
        self.clear()
        video = self.workspace / "video" / "video.mp4"
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        metadata = SessionService._read_metadata(self.workspace)
        ttk.Label(frame, text="Video Complete", style="Title.TLabel").pack(pady=(100, 10))
        ttk.Label(
            frame,
            text=f'{metadata.get("edition_label", "Global")} edition • {metadata.get("output_language", "English")}',
            style="Heading.TLabel",
        ).pack(pady=(0, 12))
        ttk.Label(frame, text=str(video), font=("Segoe UI", 11)).pack(pady=10)

        def open_folder():
            folder = video.parent
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')

        ttk.Button(frame, text="Open Video Folder", style="Primary.TButton", command=open_folder).pack(pady=(18, 8))
        ttk.Button(frame, text="Modify Video Settings", command=self.show_modify).pack(pady=4)
        ttk.Button(frame, text="Back to Home", command=self.show_home).pack(pady=4)


if __name__ == "__main__":
    app = VideoFactoryApp()
    app.mainloop()