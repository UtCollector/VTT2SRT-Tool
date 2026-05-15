import tkinter as tk
from tkinter import filedialog, messagebox, ttk, StringVar
from pathlib import Path
from datetime import datetime
import threading
import os
import sys
import re
import time

from deep_translator import GoogleTranslator

APP_TITLE = "VTT2SRT-Tool"

# Hide console window on Windows
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
        self.root.geometry("900x720")

        self.selected_files = []
        self.base_dir = Path(__file__).parent

        self.build_ui()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="VTT2SRT-Tool",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=10)

        description = tk.Label(
            self.root,
            text=(
                "Convert WebVTT (.vtt) subtitle files into clean SRT subtitles.\n"
                "Supports TXT export and subtitle translation."
            ),
            justify="center"
        )
        description.pack(pady=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Select .vtt Files",
            command=self.select_files,
            width=24,
            height=2
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            button_frame,
            text="Select Folder",
            command=self.select_folder,
            width=20,
            height=2
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            button_frame,
            text="Convert",
            command=self.start_conversion,
            width=22,
            height=2
        ).grid(row=0, column=2, padx=5)

        options_frame = tk.LabelFrame(
            self.root,
            text="Extra Options"
        )
        options_frame.pack(fill="x", padx=15, pady=10)

        self.delete_vtt_var = tk.BooleanVar(value=False)
        self.open_folder_var = tk.BooleanVar(value=True)
        self.export_txt_var = tk.BooleanVar(value=True)

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
            text="Export transcript as .txt",
            variable=self.export_txt_var
        ).pack(anchor="w", padx=10, pady=2)

        self.result_label = tk.Label(
            options_frame,
            text="Successful: 0 | Failed: 0",
            font=("Segoe UI", 10, "bold")
        )
        self.result_label.pack(anchor="e", padx=10, pady=5)

        translation_frame = tk.LabelFrame(
            self.root,
            text="Subtitle Translation"
        )
        translation_frame.pack(fill="x", padx=15, pady=10)

        self.enable_translation_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            translation_frame,
            text="Enable subtitle translation",
            variable=self.enable_translation_var
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        tk.Label(
            translation_frame,
            text="Source Language:"
        ).grid(row=1, column=0, sticky="w", padx=10)

        self.source_language = StringVar(
            value="Auto Detect"
        )

        source_dropdown = ttk.Combobox(
            translation_frame,
            textvariable=self.source_language,
            state="readonly",
            width=25
        )

        source_dropdown["values"] = (
            "Auto Detect",
            "English",
            "Dutch",
            "German",
            "French",
            "Spanish",
            "Japanese"
        )

        source_dropdown.grid(
            row=1,
            column=1,
            padx=10,
            pady=5
        )

        tk.Label(
            translation_frame,
            text="Target Language:"
        ).grid(row=2, column=0, sticky="w", padx=10)

        self.target_language = StringVar(
            value="English"
        )

        target_dropdown = ttk.Combobox(
            translation_frame,
            textvariable=self.target_language,
            state="readonly",
            width=25
        )

        target_dropdown["values"] = (
            "English",
            "Dutch",
            "German",
            "French",
            "Spanish",
            "Japanese"
        )

        target_dropdown.grid(
            row=2,
            column=1,
            padx=10,
            pady=5
        )

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

        progress_frame = tk.Frame(self.root)
        progress_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )

        self.progress = ttk.Progressbar(
            progress_frame,
            mode="determinate"
        )
        self.progress.pack(fill="x")

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

    def log_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select VTT Files",
            initialdir=self.base_dir,
            filetypes=[("WebVTT Files", "*.vtt")]
        )

        if files:
            self.selected_files = list(files)
            self.refresh_file_list()

    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Select Folder",
            initialdir=self.base_dir
        )

        if not folder:
            return

        vtt_files = list(
            Path(folder).glob("*.vtt")
        )

        if not vtt_files:
            messagebox.showwarning(
                "No Files",
                "No .vtt files found in this folder."
            )
            return

        self.selected_files = [
            str(f) for f in vtt_files
        ]

        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.delete(0, tk.END)

        for file in self.selected_files:
            self.file_list.insert(tk.END, file)

        self.log_status(
            f"{len(self.selected_files)} file(s) loaded."
        )

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning(
                "No Files",
                "Please select at least one .vtt file."
            )
            return

        thread = threading.Thread(
            target=self.convert_files,
            daemon=True
        )
        thread.start()

    def convert_files(self):
        total = len(self.selected_files)

        converted = 0
        failed = 0

        self.progress["maximum"] = total
        self.progress["value"] = 0

        for index, file_path in enumerate(
            self.selected_files,
            start=1
        ):
            vtt_path = Path(file_path)
            srt_path = vtt_path.with_suffix(".srt")
            txt_path = vtt_path.with_suffix(".txt")

            self.log_status(
                f"Converting: {vtt_path.name}"
            )

            success = self.convert_manually(
                vtt_path,
                srt_path
            )

            if success:
                converted += 1

                if self.export_txt_var.get():
                    self.export_txt(
                        vtt_path,
                        txt_path
                    )

                if self.enable_translation_var.get():
                    self.translate_srt(
                        srt_path
                    )

                if self.delete_vtt_var.get():
                    try:
                        vtt_path.unlink(
                            missing_ok=True
                        )
                    except Exception:
                        pass

            else:
                failed += 1

            self.progress["value"] = index
            self.root.update_idletasks()

        self.result_label.config(
            text=f"Successful: {converted} | Failed: {failed}"
        )

        self.log_status(
            f"Done. {converted} successful, {failed} failed."
        )

        if (
            self.open_folder_var.get()
            and self.selected_files
        ):
            try:
                os.startfile(
                    str(
                        Path(
                            self.selected_files[0]
                        ).parent
                    )
                )
            except Exception:
                pass

    def subtitle_duration_ms(
        self,
        start,
        end
    ):
        fmt = "%H:%M:%S,%f"

        start_dt = datetime.strptime(
            start,
            fmt
        )

        end_dt = datetime.strptime(
            end,
            fmt
        )

        return (
            end_dt - start_dt
        ).total_seconds() * 1000

    def convert_manually(
        self,
        vtt_path,
        srt_path
    ):
        try:
            with open(
                vtt_path,
                "r",
                encoding="utf-8"
            ) as f:
                lines = f.readlines()

            output_lines = []

            counter = 1
            skip_next_text = False

            for line in lines:
                line = line.rstrip("\n")

                if skip_next_text:
                    if line.strip() == "":
                        skip_next_text = False
                    continue

                if line.strip() == "WEBVTT":
                    continue

                if line.startswith("NOTE"):
                    continue

                if "-->" in line:
                    line = line.split(
                        " align:"
                    )[0]

                    line = line.replace(
                        ".",
                        ","
                    )

                    try:
                        parts = line.split(
                            " --> "
                        )

                        start = parts[0].strip()
                        end = parts[1].strip()

                        duration = (
                            self.subtitle_duration_ms(
                                start,
                                end
                            )
                        )

                        # Remove ultra-short rolling captions
                        if duration < 120:
                            skip_next_text = True
                            continue

                    except Exception:
                        pass

                    output_lines.append(
                        str(counter)
                    )

                    counter += 1

                    output_lines.append(line)

                    continue

                line = re.sub(
                    r"<\d{2}:\d{2}:\d{2}\.\d{3}>",
                    "",
                    line
                )

                line = re.sub(
                    r"</?c>",
                    "",
                    line
                )

                line = re.sub(
                    r"<[^>]+>",
                    "",
                    line
                )

                line = line.strip()

                if line == "":
                    output_lines.append("")
                    continue

                output_lines.append(line)

            # Remove duplicate empty lines
            cleaned_output = []

            previous_empty = False

            for line in output_lines:
                if line == "":
                    if previous_empty:
                        continue
                    previous_empty = True
                else:
                    previous_empty = False

                cleaned_output.append(line)

            # Cleanup rolling captions
            final_output = []

            previous_last_line = ""

            i = 0

            while i < len(cleaned_output):
                line = cleaned_output[i]

                if line.isdigit():
                    final_output.append(line)

                    if i + 1 < len(cleaned_output):
                        final_output.append(
                            cleaned_output[i + 1]
                        )

                    subtitle_lines = []

                    j = i + 2

                    while j < len(cleaned_output):
                        current = cleaned_output[j]

                        if current == "":
                            break

                        subtitle_lines.append(
                            current
                        )

                        j += 1

                    if (
                        subtitle_lines
                        and previous_last_line
                        and subtitle_lines[0]
                        == previous_last_line
                    ):
                        subtitle_lines.pop(0)

                    if subtitle_lines:
                        previous_last_line = (
                            subtitle_lines[-1]
                        )

                    final_output.extend(
                        subtitle_lines
                    )

                    final_output.append("")

                    i = j

                i += 1

            with open(
                srt_path,
                "w",
                encoding="utf-8-sig"
            ) as f:
                f.write(
                    "\n".join(final_output)
                )

            return True

        except Exception as e:
            print(
                f"Conversion error: {e}"
            )
            return False

    def export_txt(
        self,
        vtt_path,
        txt_path
    ):
        try:
            with open(
                vtt_path,
                "r",
                encoding="utf-8"
            ) as f:
                lines = f.readlines()

            cleaned_lines = []

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                if line == "WEBVTT":
                    continue

                if "-->" in line:
                    continue

                if re.match(
                    r"^\d+$",
                    line
                ):
                    continue

                cleaned_lines.append(line)

            with open(
                txt_path,
                "w",
                encoding="utf-8-sig"
            ) as f:
                f.write(
                    "\n".join(cleaned_lines)
                )

        except Exception:
            pass

    def translate_srt(
        self,
        srt_path
    ):
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
                    translated_text = (
                        translator.translate(
                            stripped
                        )
                    )

                    time.sleep(0.15)

                    translated_lines.append(
                        translated_text + "\n"
                    )

                except Exception:
                    translated_lines.append(line)

            with open(
                translated_path,
                "w",
                encoding="utf-8-sig"
            ) as f:
                f.writelines(
                    translated_lines
                )

            return True

        except Exception:
            return False


if __name__ == "__main__":
    root = tk.Tk()

    app = VTTConverterApp(root)

    root.mainloop()