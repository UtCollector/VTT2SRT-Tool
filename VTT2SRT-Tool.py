# =========================================================
# VTT2SRT-Tool.py
# FULL STABLE VERSION
# =========================================================
# FEATURES
# ✅ VTT -> SRT conversion
# ✅ Standalone SRT translation
# ✅ Subtitle cleanup
# ✅ Smart duplicate removal
# ✅ Merge subtitle lines
# ✅ Subtitle sync offset
# ✅ TXT export
# ✅ Open output folder
# ✅ UTF-8 BOM support
# ✅ Google Translate support
# =========================================================

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import StringVar
from pathlib import Path
from datetime import datetime, timedelta
import threading
import re
import time
import sys
import os

from deep_translator import GoogleTranslator

APP_TITLE = "VTT2SRT-Tool"

# Hide console window
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(),
            0
        )
    except Exception:
        pass


class VTTConverterApp:

    def __init__(self, root):

        self.root = root

        self.root.title(APP_TITLE)

        self.root.geometry("980x980")

        self.selected_files = []

        self.selected_translation_files = []

        self.base_dir = Path(__file__).parent

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        title = tk.Label(
            self.root,
            text="VTT2SRT-Tool",
            font=("Segoe UI", 22, "bold")
        )

        title.pack(pady=10)

        description = tk.Label(
            self.root,
            text=(
                "Convert WebVTT (.vtt) subtitles into clean SRT subtitles.\n"
                "Supports translation, cleanup, sync and TXT export."
            ),
            justify="center"
        )

        description.pack(pady=5)

        # BUTTONS
        button_frame = tk.Frame(self.root)

        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Select .vtt Files",
            command=self.select_files,
            width=22,
            height=2
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            button_frame,
            text="Select Folder",
            command=self.select_folder,
            width=18,
            height=2
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            button_frame,
            text="Convert",
            command=self.start_conversion,
            width=18,
            height=2
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            button_frame,
            text="Translate Existing .srt",
            command=self.translate_existing_srt,
            width=24,
            height=2
        ).grid(row=0, column=3, padx=5)

        # OPTIONS
        options_frame = tk.LabelFrame(
            self.root,
            text="Extra Options"
        )

        options_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )

        self.export_txt_var = tk.BooleanVar(value=True)

        self.enable_cleanup_var = tk.BooleanVar(value=True)

        self.enable_sync_var = tk.BooleanVar(value=False)

        self.open_folder_var = tk.BooleanVar(value=True)

        self.enable_merge_var = tk.BooleanVar(value=False)

        self.merge_length_var = tk.StringVar(value="42")

        tk.Checkbutton(
            options_frame,
            text="Export transcript as .txt",
            variable=self.export_txt_var
        ).pack(anchor="w", padx=10, pady=2)

        tk.Checkbutton(
            options_frame,
            text="Remove subtitle noise",
            variable=self.enable_cleanup_var
        ).pack(anchor="w", padx=10, pady=2)

        tk.Checkbutton(
            options_frame,
            text="Enable subtitle sync offset",
            variable=self.enable_sync_var
        ).pack(anchor="w", padx=10, pady=2)

        tk.Label(
            options_frame,
            text="Sync Offset (seconds):"
        ).pack(anchor="w", padx=10)

        self.sync_offset_var = tk.StringVar(value="0.0")

        tk.Entry(
            options_frame,
            textvariable=self.sync_offset_var,
            width=12
        ).pack(anchor="w", padx=10, pady=4)

        tk.Checkbutton(
            options_frame,
            text="Enable subtitle line merge",
            variable=self.enable_merge_var
        ).pack(anchor="w", padx=10, pady=2)

        tk.Label(
            options_frame,
            text="Maximum merged line length:"
        ).pack(anchor="w", padx=10)

        tk.Entry(
            options_frame,
            textvariable=self.merge_length_var,
            width=10
        ).pack(anchor="w", padx=10, pady=4)

        tk.Checkbutton(
            options_frame,
            text="Open folder after conversion",
            variable=self.open_folder_var
        ).pack(anchor="w", padx=10, pady=2)

        self.result_label = tk.Label(
            options_frame,
            text="Successful: 0 | Failed: 0",
            font=("Segoe UI", 10, "bold")
        )

        self.result_label.pack(
            anchor="e",
            padx=10,
            pady=5
        )

        # TRANSLATION
        translation_frame = tk.LabelFrame(
            self.root,
            text="Translation"
        )

        translation_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )

        self.enable_translation_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            translation_frame,
            text="Enable translation during conversion",
            variable=self.enable_translation_var
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=5
        )

        tk.Label(
            translation_frame,
            text="Target Language:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=10
        )

        self.target_language = StringVar(
            value="English"
        )

        language_dropdown = ttk.Combobox(
            translation_frame,
            textvariable=self.target_language,
            state="readonly",
            width=25
        )

        language_dropdown["values"] = (
            "English",
            "Dutch",
            "German",
            "French",
            "Spanish",
            "Japanese"
        )

        language_dropdown.grid(
            row=1,
            column=1,
            padx=10,
            pady=5
        )

        # FILE LIST
        list_frame = tk.LabelFrame(
            self.root,
            text="Selected Files"
        )

        list_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        self.file_list = tk.Listbox(list_frame)

        self.file_list.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # PROGRESS
        self.progress = ttk.Progressbar(
            self.root,
            mode="determinate"
        )

        self.progress.pack(
            fill="x",
            padx=15,
            pady=10
        )

        self.status_label = tk.Label(
            self.root,
            text="Ready.",
            anchor="w"
        )

        self.status_label.pack(
            fill="x",
            padx=15,
            pady=(0, 10)
        )

    # =====================================================
    # STATUS
    # =====================================================

    def log_status(self, text):

        self.status_label.config(text=text)

        self.root.update_idletasks()

    # =====================================================
    # FILE SELECTION
    # =====================================================

    def select_files(self):

        files = filedialog.askopenfilenames(
            title="Select VTT Files",
            initialdir=self.base_dir,
            filetypes=[("WebVTT Files", "*.vtt")]
        )

        if files:

            self.selected_translation_files = []

            self.selected_files = list(files)

            self.refresh_file_list()

    def select_folder(self):

        folder = filedialog.askdirectory(
            title="Select Folder",
            initialdir=self.base_dir
        )

        if not folder:
            return

        self.selected_translation_files = []

        vtt_files = list(
            Path(folder).glob("*.vtt")
        )

        self.selected_files = [
            str(f) for f in vtt_files
        ]

        self.refresh_file_list()

    def translate_existing_srt(self):

        files = filedialog.askopenfilenames(
            title="Select Existing SRT Files",
            initialdir=self.base_dir,
            filetypes=[("Subtitle Files", "*.srt")]
        )

        if not files:
            return

        self.selected_files = []

        self.selected_translation_files = list(files)

        self.refresh_file_list()

        self.log_status(
            "SRT files loaded. Press Convert."
        )

    def refresh_file_list(self):

        self.file_list.delete(0, tk.END)

        for file in self.selected_files:
            self.file_list.insert(tk.END, file)

        for file in self.selected_translation_files:
            self.file_list.insert(tk.END, file)

    # =====================================================
    # START
    # =====================================================

    def start_conversion(self):

        has_vtt = len(self.selected_files) > 0

        has_srt = len(self.selected_translation_files) > 0

        # VTT -> SRT
        if has_vtt:

            thread = threading.Thread(
                target=self.convert_files,
                daemon=True
            )

            thread.start()

            return

        # Existing SRT translation
        if has_srt:

            thread = threading.Thread(
                target=self.translate_existing_srt_worker,
                daemon=True
            )

            thread.start()

            return

        messagebox.showwarning(
            "No Files",
            "Please select at least one .vtt or .srt file."
        )

    # =====================================================
    # CLEANUP
    # =====================================================

    def cleanup_subtitle_text(self, text):

        if not self.enable_cleanup_var.get():
            return text

        stripped = text.strip()

        if re.match(r"^\[.*\]$", stripped):
            return ""

        if re.match(r"^\(.*\)$", stripped):
            return ""

        if "♪" in stripped:
            return ""

        return stripped

    # =====================================================
    # DUPLICATES
    # =====================================================

    def remove_duplicate_subtitles(self, subtitles):

        cleaned = []

        previous_text = ""

        for timestamp, text_lines in subtitles:

            current_text = " ".join(text_lines).strip()

            if not current_text:
                continue

            if current_text == previous_text:
                continue

            cleaned.append(
                (
                    timestamp,
                    text_lines
                )
            )

            previous_text = current_text

        return cleaned

    # =====================================================
    # CONVERT
    # =====================================================

    def convert_files(self):

        total = len(self.selected_files)

        successful = 0
        failed = 0

        self.progress["maximum"] = total
        self.progress["value"] = 0

        for index, file_path in enumerate(
            self.selected_files,
            start=1
        ):

            vtt_path = Path(file_path)

            srt_path = vtt_path.with_suffix(".srt")

            self.log_status(
                f"Converting: {vtt_path.name}"
            )

            success = self.convert_manually(
                vtt_path,
                srt_path
            )

            if success:

                successful += 1

                if self.export_txt_var.get():
                    self.export_txt(vtt_path)

                if self.enable_sync_var.get():
                    self.create_synced_srt(srt_path)

                if self.enable_merge_var.get():
                    self.create_merged_srt(srt_path)

                if self.enable_translation_var.get():
                    self.translate_srt(srt_path)

            else:
                failed += 1

            self.progress["value"] = index

            self.root.update_idletasks()

        self.finish_process(successful, failed)

    def convert_manually(self, vtt_path, srt_path):

        try:

            with open(
                vtt_path,
                "r",
                encoding="utf-8"
            ) as f:

                lines = f.readlines()

            subtitles = []

            current_timestamp = None

            current_text_lines = []

            for line in lines:

                line = line.rstrip("\n")

                if line.strip() == "WEBVTT":
                    continue

                if line.startswith("NOTE"):
                    continue

                if "-->" in line:

                    if current_timestamp and current_text_lines:

                        subtitles.append(
                            (
                                current_timestamp,
                                current_text_lines
                            )
                        )

                    line = line.split(" align:")[0]

                    line = line.replace(".", ",")

                    current_timestamp = line

                    current_text_lines = []

                    continue

                line = re.sub(
                    r"<[^>]+>",
                    "",
                    line
                )

                line = self.cleanup_subtitle_text(
                    line.strip()
                )

                if line:
                    current_text_lines.append(line)

            if current_timestamp and current_text_lines:

                subtitles.append(
                    (
                        current_timestamp,
                        current_text_lines
                    )
                )

            subtitles = self.remove_duplicate_subtitles(
                subtitles
            )

            with open(
                srt_path,
                "w",
                encoding="utf-8-sig"
            ) as f:

                for index, (
                    timestamp,
                    text_lines
                ) in enumerate(subtitles, start=1):

                    f.write(f"{index}\n")

                    f.write(f"{timestamp}\n")

                    for text in text_lines:
                        f.write(text + "\n")

                    f.write("\n")

            return True

        except Exception:
            return False

    # =====================================================
    # MERGE
    # =====================================================

    def create_merged_srt(self, srt_path):

        try:

            max_length = int(
                self.merge_length_var.get()
            )

            merged_path = srt_path.with_name(
                f"{srt_path.stem}.merged.srt"
            )

            with open(
                srt_path,
                "r",
                encoding="utf-8-sig"
            ) as f:

                lines = f.readlines()

            merged_lines = []

            for line in lines:

                if (
                    "-->" not in line
                    and not line.strip().isdigit()
                    and len(line.strip()) > max_length
                ):

                    words = line.strip().split()

                    midpoint = len(words) // 2

                    line = (
                        " ".join(words[:midpoint])
                        + "\n"
                        + " ".join(words[midpoint:])
                        + "\n"
                    )

                merged_lines.append(line)

            with open(
                merged_path,
                "w",
                encoding="utf-8-sig"
            ) as f:

                f.writelines(merged_lines)

        except Exception:
            pass

    # =====================================================
    # SYNC
    # =====================================================

    def create_synced_srt(self, srt_path):

        try:

            offset = float(
                self.sync_offset_var.get()
            )

            synced_path = srt_path.with_name(
                f"{srt_path.stem}.synced.srt"
            )

            with open(
                srt_path,
                "r",
                encoding="utf-8-sig"
            ) as f:

                lines = f.readlines()

            synced_lines = []

            for line in lines:

                if "-->" in line:

                    start, end = line.strip().split(
                        " --> "
                    )

                    start = self.shift_timestamp(
                        start,
                        offset
                    )

                    end = self.shift_timestamp(
                        end,
                        offset
                    )

                    synced_lines.append(
                        f"{start} --> {end}\n"
                    )

                else:
                    synced_lines.append(line)

            with open(
                synced_path,
                "w",
                encoding="utf-8-sig"
            ) as f:

                f.writelines(synced_lines)

        except Exception:
            pass

    def shift_timestamp(self, timestamp, offset_seconds):

        try:

            dt = datetime.strptime(
                timestamp,
                "%H:%M:%S,%f"
            )

            delta = timedelta(
                seconds=offset_seconds
            )

            shifted = dt + delta

            return shifted.strftime(
                "%H:%M:%S,%f"
            )[:-3]

        except Exception:
            return timestamp

    # =====================================================
    # TXT EXPORT
    # =====================================================

    def export_txt(self, vtt_path):

        try:

            txt_path = vtt_path.with_suffix(".txt")

            with open(
                vtt_path,
                "r",
                encoding="utf-8"
            ) as f:

                lines = f.readlines()

            cleaned = []

            for line in lines:

                line = line.strip()

                if not line:
                    continue

                if line == "WEBVTT":
                    continue

                if "-->" in line:
                    continue

                cleaned.append(line)

            with open(
                txt_path,
                "w",
                encoding="utf-8-sig"
            ) as f:

                f.write("\n".join(cleaned))

        except Exception:
            pass

    # =====================================================
    # TRANSLATE EXISTING SRT
    # =====================================================

    def translate_existing_srt_worker(self):

        files = self.selected_translation_files

        total = len(files)

        successful = 0
        failed = 0

        self.progress["maximum"] = total
        self.progress["value"] = 0

        for index, file_path in enumerate(
            files,
            start=1
        ):

            srt_path = Path(file_path)

            self.log_status(
                f"Translating: {srt_path.name}"
            )

            success = self.translate_srt(srt_path)

            if success:
                successful += 1
            else:
                failed += 1

            self.progress["value"] = index

            self.root.update_idletasks()

        self.finish_process(successful, failed)

    # =====================================================
    # TRANSLATION
    # =====================================================

    def translate_srt(self, srt_path):

        try:

            language_map = {
                "English": "en",
                "Dutch": "nl",
                "German": "de",
                "French": "fr",
                "Spanish": "es",
                "Japanese": "ja"
            }

            target_lang = language_map.get(
                self.target_language.get(),
                "en"
            )

            translated_path = srt_path.with_name(
                f"{srt_path.stem}.{target_lang}.srt"
            )

            with open(
                srt_path,
                "r",
                encoding="utf-8-sig"
            ) as f:

                lines = f.readlines()

            translated_lines = []

            translator = GoogleTranslator(
                source="auto",
                target=target_lang
            )

            for line in lines:

                stripped = line.strip()

                if stripped.isdigit():
                    translated_lines.append(line)
                    continue

                if "-->" in line:
                    translated_lines.append(line)
                    continue

                if not stripped:
                    translated_lines.append(line)
                    continue

                try:

                    translated_text = translator.translate(
                        stripped
                    )

                    translated_lines.append(
                        translated_text + "\n"
                    )

                    time.sleep(0.15)

                except Exception:

                    translated_lines.append(line)

            with open(
                translated_path,
                "w",
                encoding="utf-8-sig"
            ) as f:

                f.writelines(translated_lines)

            return True

        except Exception:
            return False

    # =====================================================
    # FINISH
    # =====================================================

    def finish_process(self, successful, failed):

        self.result_label.config(
            text=f"Successful: {successful} | Failed: {failed}"
        )

        if self.open_folder_var.get():

            try:

                target_path = None

                if self.selected_files:
                    target_path = Path(
                        self.selected_files[0]
                    ).parent

                elif self.selected_translation_files:
                    target_path = Path(
                        self.selected_translation_files[0]
                    ).parent

                if target_path:
                    os.startfile(target_path)

            except Exception:
                pass

        self.log_status("Completed.")


# =========================================================
# START APP
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = VTTConverterApp(root)

    root.mainloop()