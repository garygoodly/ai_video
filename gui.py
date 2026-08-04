import os
import sys
import threading
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


class VideoFactoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Knowledge Video Factory")
        self.geometry("1180x760")
        self.minsize(980, 650)

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
        ttk.Label(frame, text="Start New Session", style="Title.TLabel").pack(pady=(85, 18))
        ttk.Label(
            frame,
            text=("ChatGPT will identify today’s biggest finance stories.\n"
                  "The project name is only used to organize the workspace."),
            font=("Segoe UI", 11),
            justify="center",
        ).pack(pady=(0, 28))

        form = ttk.Frame(frame)
        form.pack()
        ttk.Label(form, text="Project name", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=8
        )
        project_entry = ttk.Entry(form, width=58, font=("Segoe UI", 12))
        project_entry.insert(0, f"{date.today().isoformat()} Finance Daily")
        project_entry.grid(row=1, column=0, pady=(0, 10))
        project_entry.select_range(0, "end")
        project_entry.focus_set()
        ttk.Label(
            form,
            text="Example: 2026-08-03 Finance Daily",
            foreground="#666666",
        ).grid(row=2, column=0, sticky="w", pady=(0, 24))

        def create_session():
            try:
                self.workspace = self.controller.sessions.create(project_entry.get())
                self.open_current_stage()
            except Exception as exc:
                messagebox.showerror("Cannot create session", str(exc))

        project_entry.bind("<Return>", lambda event: create_session())
        ttk.Button(
            form,
            text="Create Project",
            style="Primary.TButton",
            command=create_session,
        ).grid(row=3, column=0)

    def show_resume(self):
        self.clear()
        frame = ttk.Frame(self, padding=28)
        frame.pack(fill="both", expand=True)
        ttk.Button(frame, text="← Back", command=self.show_home).pack(anchor="w")
        ttk.Label(frame, text="Resume Session", style="Title.TLabel").pack(anchor="w", pady=(22, 20))

        columns = ("project", "stage", "progress", "updated")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        tree.heading("project", text="Project")
        tree.heading("stage", text="Continue From")
        tree.heading("progress", text="Progress")
        tree.heading("updated", text="Last Updated")
        tree.column("project", width=420)
        tree.column("stage", width=160)
        tree.column("progress", width=100, anchor="center")
        tree.column("updated", width=220)
        tree.pack(fill="both", expand=True)

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
                    session["current_stage"].replace("_", " ").title(),
                    f'{session["progress_percent"]}%',
                    updated,
                ),
            )

        def resume_selected(event=None):
            selection = tree.selection()
            if not selection:
                messagebox.showinfo("Select a session", "Choose a session to continue.")
                return
            self.workspace = workspace_by_id[selection[0]]
            self.open_current_stage()

        tree.bind("<Double-1>", resume_selected)
        ttk.Button(
            frame,
            text="Continue Selected Session",
            style="Primary.TButton",
            command=resume_selected,
        ).pack(pady=18)

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
        header = ttk.Frame(self, padding=(24, 18))
        header.pack(fill="x")
        ttk.Button(header, text="Sessions", command=self.show_home).pack(side="left")
        ttk.Label(header, text=metadata["name"], style="Heading.TLabel").pack(side="left", padx=20)
        ttk.Label(header, text=f"Step: {stage.title()}").pack(side="right")

        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        left = ttk.Frame(pane, padding=14)
        right = ttk.Frame(pane, padding=14)
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

        status_var = tk.StringVar(value="Waiting for JSON. It will be checked and saved automatically.")
        status_label = ttk.Label(self, textvariable=status_var, padding=(24, 4))
        status_label.pack(fill="x")
        footer = ttk.Frame(self, padding=(24, 10, 24, 18))
        footer.pack(fill="x")

        next_button = ttk.Button(
            footer,
            text="Next →",
            style="Primary.TButton",
            state="disabled",
        )
        next_button.pack(side="right")
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
                summary = str(exc).splitlines()[0] if str(exc) else "Invalid JSON or schema"
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

    def show_complete(self):
        self.clear()
        video = self.workspace / "video" / "video.mp4"
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Video Complete", style="Title.TLabel").pack(pady=(100, 18))
        ttk.Label(frame, text=str(video), font=("Segoe UI", 11)).pack(pady=10)

        def open_folder():
            folder = video.parent
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')

        ttk.Button(frame, text="Open Video Folder", style="Primary.TButton", command=open_folder).pack(pady=18)
        ttk.Button(frame, text="Back to Sessions", command=self.show_home).pack()


if __name__ == "__main__":
    VideoFactoryApp().mainloop()
