import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import subprocess
import threading
import os
import sys

APP_TITLE = "VTT2SRT-Tool"

# Verberg consolevenster op Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass


class VTTConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x520")

        self.selected_files = []
        self.base_dir = Path(__file__).parent

        self.build_ui()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="VTT2SRT-Tool",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=12)

        description = tk.Label(
            self.root,
            text=(
                "Convert WebVTT (.vtt) transcript files automatically into SRT subtitles.\n"
                "Supports multiple files and folder conversion."
            ),
            justify="center"
        )
        description.pack(pady=4)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Select .vtt files",
            command=self.select_files,
            width=28,
            height=2
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            button_frame,
            text="Select folder",
            command=self.select_folder,
            width=20,
            height=2
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            button_frame,
            text="Convert to SRT",
            command=self.start_conversion,
            width=24,
            height=2
        ).grid(row=0, column=2, padx=5)

        options_frame = tk.LabelFrame(self.root, text="Extra options")
        options_frame.pack(fill="x", padx=15, pady=10)

        result_frame = tk.Frame(self.root)
        result_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.result_label = tk.Label(
            result_frame,
            text="Successful: 0 | Failed: 0",
            font=("Segoe UI", 10, "bold"),
            anchor="e"
        )

        self.result_label.pack(side="right", padx=10)

        self.delete_vtt_var = tk.BooleanVar(value=False)
        self.open_folder_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=True)

        tk.Checkbutton(
            options_frame,
            text="Delete original .vtt after conversion",
            variable=self.delete_vtt_var
        ).pack(anchor="w", padx=10, pady=2)

        tk.Checkbutton(
            options_frame,
            text="Open folder after conversion",
            variable=self.open_folder_var
        ).pack(anchor="w", padx=10, pady=2)

        tk.Checkbutton(
            options_frame,
            text="Overwrite existing .srt files",
            variable=self.overwrite_var
        ).pack(anchor="w", padx=10, pady=2)

        list_frame = tk.LabelFrame(self.root, text="Selected files")
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.file_list = tk.Listbox(list_frame, height=12)
        self.file_list.pack(fill="both", expand=True, padx=10, pady=10)

        progress_frame = tk.Frame(self.root)
        progress_frame.pack(fill="x", padx=15, pady=10)

        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(fill="x")

        self.status_label = tk.Label(
            self.root,
            text="Ready.",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=15, pady=(0, 10))

    def log_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select VTT files",
            initialdir=self.base_dir,
            filetypes=[("WebVTT", "*.vtt")]
        )

        if files:
            self.selected_files = list(files)
            self.refresh_file_list()

    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Select folder",
            initialdir=self.base_dir
        )

        if not folder:
            return

        vtt_files = list(Path(folder).glob("*.vtt"))

        if not vtt_files:
            messagebox.showwarning(
                "No files",
                "No .vtt files found in this folder."
            )
            return

        self.selected_files = [str(f) for f in vtt_files]
        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.delete(0, tk.END)

        for file in self.selected_files:
            self.file_list.insert(tk.END, file)

        self.log_status(f"{len(self.selected_files)} file(s) loaded.")

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning(
                "No files",
                "Please select at least one .vtt file first."
            )
            return

        thread = threading.Thread(target=self.convert_files, daemon=True)
        thread.start()

    def convert_files(self):
        total = len(self.selected_files)
        converted = 0
        failed = 0

        self.progress["maximum"] = total
        self.progress["value"] = 0

        for index, file_path in enumerate(self.selected_files, start=1):
            vtt_path = Path(file_path)
            srt_path = vtt_path.with_suffix(".srt")

            self.log_status(f"Converting: {vtt_path.name}")

            if srt_path.exists() and not self.overwrite_var.get():
                failed += 1
                continue

            success = self.convert_vtt_to_srt(vtt_path, srt_path)

            if success:
                converted += 1

                if self.delete_vtt_var.get():
                    try:
                        vtt_path.unlink(missing_ok=True)
                    except Exception:
                        pass
            else:
                failed += 1

            self.progress["value"] = index
            self.root.update_idletasks()

        self.log_status(
            f"Ready. {converted} succesvol, {failed} mislukt."
        )

        if self.open_folder_var.get() and self.selected_files:
            folder = str(Path(self.selected_files[0]).parent)
            try:
                os.startfile(folder)
            except Exception:
                pass

        self.result_label.config(text=f"Successful: {converted} | Failed: {failed}")

    def convert_vtt_to_srt(self, vtt_path, srt_path):
        ffmpeg_exists = self.check_ffmpeg()

        if ffmpeg_exists:
            return self.convert_with_ffmpeg(vtt_path, srt_path)

        return self.convert_manually(vtt_path, srt_path)

    def check_ffmpeg(self):
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return True
        except Exception:
            return False

    def convert_with_ffmpeg(self, vtt_path, srt_path):
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(vtt_path),
                    str(srt_path)
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True

        except Exception:
            return False

    def convert_manually(self, vtt_path, srt_path):
        try:
            with open(vtt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            output_lines = []
            counter = 1

            for line in lines:
                line = line.rstrip("\n")

                if line.strip() == "WEBVTT":
                    continue

                if "-->" in line:
                    output_lines.append(str(counter))
                    counter += 1
                    line = line.replace(".", ",")

                output_lines.append(line)

            with open(srt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines))

            return True

        except Exception:
            return False


if __name__ == "__main__":
    root = tk.Tk()
    app = VTTConverterApp(root)
    root.mainloop()