import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import csv, os, threading
from datetime import datetime
from pathlib import Path
from engine import KeywordEngine

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

THEME = {
    "bg": "#0d1117",
    "card": "#161b22",
    "card2": "#1c2333",
    "input_bg": "#0d1117",
    "border": "#30363d",
    "border_focus": "#58a6ff",
    "text": "#e6edf3",
    "text_sec": "#8b949e",
    "text_muted": "#484f58",
    "accent": "#00bc8c",
    "accent2": "#58a6ff",
    "success": "#3fb950",
    "warning": "#d29922",
    "danger": "#f85149",
    "accent_alpha": "rgba(0,188,140,0.15)"
}

class DiasinApp:
    def __init__(self):
        self.engine = KeywordEngine()
        self.window = tb.Window(themename="darkly")
        self.window.title("Diasin - File Manager & Auto Keyword Generator")
        self.window.geometry("1400@0")
        self.window.minsize(1200, 800)
        self.window.configure(bg=THEME["bg"])

        self.current_dir = None
        self.files_list = []
        self.selected_indices = set()
        self.generated_data_map = {}
        self.preview_analysis = None
        self.platform_var = tk.StringVar(value="Adobe Stock")

        self._build_ui()

    def _btn(self, parent, text, color, cmd, **kw):
        btn = tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                       fg="#fff", bg=color, cursor="hand2", padx=14, pady=5, **kw)
        btn.bind("<Button-1>", lambda e: cmd())
        btn.bind("<Enter>", lambda e: btn.config(bg=self._lighten(color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def _lighten(self, c):
        try:
            r = int(c[1:3], 16); g = int(c[3:5], 16); b = int(c[5:7], 16)
            return f"#{min(255,r+20):02x}{min(255,g+20):02x}{min(255,b+20):02x}"
        except:
            return c

    def _card(self, parent, title="", **kw):
        f = tk.Frame(parent, bg=THEME["card"], highlightbackground=THEME["border"],
                     highlightthickness=1, **kw)
        if title:
            tk.Label(f, text=title, font=("Segoe UI", 8, "bold"),
                     fg=THEME["text_muted"], bg=THEME["card"]).pack(anchor="w", padx=14, pady=(10, 4))
        return f

    def _build_ui(self):
        mc = tk.Frame(self.window, bg=THEME["bg"])
        mc.pack(fill="both", expand=True, padx=16, pady=8)

        # Header
        hdr = tk.Frame(mc, bg=THEME["card"], highlightbackground=THEME["border"], highlightthickness=1, height=64)
        hdr.pack(fill="x", pady=(0, 8))
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Diasin", font=("Segoe UI", 24, "bold"),
                 fg=THEME["accent"], bg=THEME["card"]).pack(side="left", padx=(20, 8))
        tk.Label(hdr, text="File Manager & Auto Metadata Generator", font=("Segoe UI", 10),
                 fg=THEME["text_sec"], bg=THEME["card"]).pack(side="left")
        tk.Label(hdr, text="v2.1", font=("Segoe UI", 10),
                 fg=THEME["text_muted"], bg=THEME["card"]).pack(side="right", padx=(0, 20))

        # ===== TOOLBAR =====
        toolbar = tk.Frame(mc, bg=THEME["card2"], highlightbackground=THEME["border"], highlightthickness=1)
        toolbar.pack(fill="x", pady=(0, 8))

        tbf = tk.Frame(toolbar, bg=THEME["card2"])
        tbf.pack(fill="x", padx=12, pady=6)

        self._btn(tbf, " Open Folder ", THEME["accent2"], self._open_folder).pack(side="left", padx=(0, 8))
        self._btn(tbf, " Process All ", THEME["accent"], self._process_selected).pack(side="left", padx=(0, 8))
        self._btn(tbf, " Select All ", THEME["text_sec"], self._select_all).pack(side="left", padx=(0, 4))
        self._btn(tbf, " Deselect ", THEME["text_muted"], self._deselect_all).pack(side="left", padx=(0, 12))

        sep = tk.Frame(tbf, bg=THEME["border"], width=1, height=24)
        sep.pack(side="left", padx=6)

        tk.Label(tbf, text="Platform:", font=("Segoe UI", 9), fg=THEME["text_sec"],
                 bg=THEME["card2"]).pack(side="left", padx=(10, 6))
        self.plat_combo = ttk.Combobox(tbf, textvariable=self.platform_var,
                                       values=["Adobe Stock", "Shutterstock"],
                                       state="readonly", width=16)
        self.plat_combo.pack(side="left", padx=(0, 12))

        self.folder_label = tk.Label(tbf, text="[no folder opened]", font=("Segoe UI", 9),
                                     fg=THEME["text_muted"], bg=THEME["card2"])
        self.folder_label.pack(side="right", padx=(0, 8))

        # ===== MAIN BODY =====
        body = tk.Frame(mc, bg=THEME["bg"])
        body.pack(fill="both", expand=True)

        paned_h = ttk.PanedWindow(body, orient=HORIZONTAL)
        paned_h.pack(fill="both", expand=True)

        # LEFT: File browser
        left_frame = tk.Frame(paned_h, bg=THEME["card"], highlightbackground=THEME["border"], highlightthickness=1)
        paned_h.add(left_frame, weight=1)

        tk.Label(left_frame, text="FILE BROWSER", font=("Segoe UI", 8, "bold"),
                 fg=THEME["text_muted"], bg=THEME["card"]).pack(anchor="w", padx=12, pady=(8, 2))
        self.file_count = tk.Label(left_frame, text="0 files", font=("Segoe UI", 9),
                                   fg=THEME["text_sec"], bg=THEME["card"])
        self.file_count.pack(anchor="w", padx=12, pady=(0, 4))

        list_header = tk.Frame(left_frame, bg=THEME["card2"])
        list_header.pack(fill="x", padx=6)
        for c, w in [("", 30), ("Name", 0), ("Type", 60), ("Size", 60)]:
            lbl = tk.Label(list_header, text=c, font=("Segoe UI", 8, "bold"),
                           fg=THEME["text_muted"], bg=THEME["card2"])
            lbl.pack(side="left", padx=2)
            if w:
                lbl.configure(width=w//7)

        self.list_canvas = tk.Canvas(left_frame, bg=THEME["input_bg"],
                                     highlightthickness=0, bd=0)
        scroll_y = tk.Scrollbar(left_frame, orient="vertical", command=self.list_canvas.yview)
        self.list_frame = tk.Frame(self.list_canvas, bg=THEME["input_bg"])
        self.list_frame.bind("<Configure>", lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")))
        self.list_canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_canvas.configure(yscrollcommand=scroll_y.set)
        self.list_canvas.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=(0, 6))
        scroll_y.pack(side="right", fill="y", pady=(0, 6))

        # RIGHT PANEL
        right_frame = tk.Frame(paned_h, bg=THEME["bg"])
        paned_h.add(right_frame, weight=2)

        paned_v = ttk.PanedWindow(right_frame, orient=VERTICAL)
        paned_v.pack(fill="both", expand=True)

        # TOP RIGHT: Preview & Analysis
        preview_frame = tk.Frame(paned_v, bg=THEME["card"], highlightbackground=THEME["border"], highlightthickness=1)
        paned_v.add(preview_frame, weight=1)

        ph = tk.Frame(preview_frame, bg=THEME["card"])
        ph.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(ph, text="PREVIEW & ANALYSIS", font=("Segoe UI", 8, "bold"),
                 fg=THEME["text_muted"], bg=THEME["card"]).pack(side="left")
        self.preview_name = tk.Label(ph, text="", font=("Segoe UI", 9, "bold"),
                                     fg=THEME["accent"], bg=THEME["card"])
        self.preview_name.pack(side="left", padx=(10, 0))

        preview_body = tk.Frame(preview_frame, bg=THEME["card"])
        preview_body.pack(fill="both", expand=True, padx=12, pady=(4, 8))

        self.preview_info = tk.Text(preview_body, wrap=tk.WORD, font=("Segoe UI", 9),
                                    bg="#0d1117", fg=THEME["text_sec"], relief="flat",
                                    bd=0, highlightthickness=0, height=6)
        preview_body.pack_propagate(False)
        self.preview_info.pack(fill="both", expand=True)
        self.preview_info.insert(tk.END, "Select a file or open a folder to begin.")

        # BOTTOM RIGHT: Generated metadata
        result_frame = tk.Frame(paned_v, bg=THEME["card"], highlightbackground=THEME["border"], highlightthickness=1)
        paned_v.add(result_frame, weight=2)

        rh = tk.Frame(result_frame, bg=THEME["card"])
        rh.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(rh, text="GENERATED METADATA", font=("Segoe UI", 8, "bold"),
                 fg=THEME["text_muted"], bg=THEME["card"]).pack(side="left")

        rpaned = ttk.PanedWindow(result_frame, orient=HORIZONTAL)
        rpaned.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # Keywords panel
        kw_frame = tk.Frame(rpaned, bg=THEME["card"])
        rpaned.add(kw_frame, weight=2)
        kh = tk.Frame(kw_frame, bg=THEME["card"])
        kh.pack(fill="x")
        tk.Label(kh, text="Keywords", font=("Segoe UI", 10, "bold"),
                 fg=THEME["text"], bg=THEME["card"]).pack(side="left", padx=6)
        self.kw_count = tk.Label(kh, text="0", font=("Segoe UI", 9),
                                 fg=THEME["text_sec"], bg=THEME["card"])
        self.kw_count.pack(side="left", padx=(4, 0))
        self.kw_text = tk.Text(kw_frame, wrap=tk.WORD, font=("Segoe UI", 9),
                               bg="#0d1117", fg=THEME["text"], relief="flat",
                               bd=0, highlightthickness=0)
        ks = tk.Scrollbar(kw_frame, orient="vertical", command=self.kw_text.yview)
        self.kw_text.configure(yscrollcommand=ks.set)
        self.kw_text.pack(side="left", fill="both", expand=True)
        ks.pack(side="right", fill="y")

        # Titles & Desc panel
        td_frame = tk.Frame(rpaned, bg=THEME["card"])
        rpaned.add(td_frame, weight=1)
        tdh = tk.Frame(td_frame, bg=THEME["card"])
        tdh.pack(fill="x")
        tk.Label(tdh, text="Titles & Descriptions", font=("Segoe UI", 10, "bold"),
                 fg=THEME["text"], bg=THEME["card"]).pack(side="left", padx=6)
        self._btn(tdh, "Copy", THEME["text_sec"], lambda: self._copy_text(self.td_text)).pack(side="right", padx=4)
        self.td_text = tk.Text(td_frame, wrap=tk.WORD, font=("Segoe UI", 9),
                               bg="#0d1117", fg=THEME["text"], relief="flat",
                               bd=0, highlightthickness=0)
        ts = tk.Scrollbar(td_frame, orient="vertical", command=self.td_text.yview)
        self.td_text.configure(yscrollcommand=ts.set)
        self.td_text.pack(side="left", fill="both", expand=True)
        ts.pack(side="right", fill="y")

        # ===== BOTTOM ACTION BAR =====
        action_bar = tk.Frame(mc, bg=THEME["card"], highlightbackground=THEME["border"], highlightthickness=1)
        action_bar.pack(fill="x", pady=(8, 0))

        abf = tk.Frame(action_bar, bg=THEME["card"])
        abf.pack(fill="x", padx=14, pady=8)

        self._btn(abf, " Export CSV ", THEME["accent2"], self._export_csv).pack(side="left", padx=(0, 8))

        self._btn(abf, " Move Files ", THEME["accent"], lambda: self._move_copy("move")).pack(side="left", padx=(0, 8))
        self._btn(abf, " Copy Files ", THEME["accent"], lambda: self._move_copy("copy")).pack(side="left", padx=(0, 12))

        sep2 = tk.Frame(abf, bg=THEME["border"], width=1, height=24)
        sep2.pack(side="left", padx=6)

        self.dest_label = tk.Label(abf, text="Dest: [not set]", font=("Segoe UI", 9),
                                   fg=THEME["text_muted"], bg=THEME["card"])
        self.dest_label.pack(side="left", padx=(6, 8))
        self._btn(abf, "Browse", THEME["text_sec"], self._set_destination).pack(side="left", padx=(0, 8))

        self.dest_dir = None

        sep3 = tk.Frame(abf, bg=THEME["border"], width=1, height=24)
        sep3.pack(side="left", padx=6)

        self._btn(abf, "Batch Mode", THEME["warning"], self._show_batch_dialog).pack(side="left")

        self.status_icon = tk.Label(abf, text="\u26a1", font=("Segoe UI", 11),
                                    fg=THEME["accent"], bg=THEME["card"])
        self.status_icon.pack(side="right", padx=(12, 4))
        self.status_label = tk.Label(abf, text="Ready.", font=("Segoe UI", 9),
                                     fg=THEME["text_sec"], bg=THEME["card"])
        self.status_label.pack(side="right")
        self.progress = ttk.Progressbar(abf, mode="indeterminate", length=100)

    # ==================== FILE BROWSER ====================
    def _open_folder(self):
        d = filedialog.askdirectory(title="Pilih folder berisi file")
        if not d:
            return
        self.current_dir = d
        self.files_list = self.engine.scan_directory(d)
        self.selected_indices.clear()
        self.generated_data_map.clear()
        self.folder_label.config(text=f" [{os.path.basename(d)}]  ({len(self.files_list)} files)")
        self._refresh_list()
        self._status(f"Loaded {len(self.files_list)} files from {d}", THEME["accent"])

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not self.files_list:
            tk.Label(self.list_frame, text="  No files found.", font=("Segoe UI", 9),
                     fg=THEME["text_muted"], bg=THEME["input_bg"]).pack(anchor="w", padx=8, pady=4)
            self.file_count.config(text="0 files")
            return

        self.file_count.config(text=f"{len(self.files_list)} files")

        for idx, f in enumerate(self.files_list):
            checked = idx in self.selected_indices
            row = tk.Frame(self.list_frame, bg=THEME["input_bg"], cursor="hand2")
            row.pack(fill="x")
            row.bind("<Button-1>", lambda e, i=idx: self._toggle_file(i))
            row.bind("<Double-Button-1>", lambda e, i=idx: self._preview_file(i))

            cb = tk.Label(row, text="\u2611" if checked else "\u2610", font=("Segoe UI", 12),
                          fg=THEME["accent"] if checked else THEME["text_muted"],
                          bg=THEME["input_bg"], width=2)
            cb.pack(side="left", padx=(4, 2))
            cb.bind("<Button-1>", lambda e, i=idx: self._toggle_file(i))

            has_data = f["stem"] in self.generated_data_map
            name_color = THEME["accent"] if has_data else THEME["text"]
            nm = tk.Label(row, text=f["name"], font=("Segoe UI", 9),
                          fg=name_color, bg=THEME["input_bg"], anchor="w")
            nm.pack(side="left", fill="x", expand=True, padx=(2, 4))
            nm.bind("<Button-1>", lambda e, i=idx: self._toggle_file(i))
            nm.bind("<Double-Button-1>", lambda e, i=idx: self._preview_file(i))

            tk.Label(row, text=f["type"], font=("Segoe UI", 8),
                     fg=THEME["text_muted"], bg=THEME["input_bg"], width=8).pack(side="right")
            tk.Label(row, text=f"{f['size_kb']}K", font=("Segoe UI", 8),
                     fg=THEME["text_muted"], bg=THEME["input_bg"], width=8).pack(side="right")

            if idx % 2 == 0:
                row.configure(bg="#0a0e17")
                for c in [cb, nm]:
                    if has_data:
                        pass

        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))

    def _toggle_file(self, idx):
        if idx in self.selected_indices:
            self.selected_indices.remove(idx)
        else:
            self.selected_indices.add(idx)
        self._refresh_list()

    def _select_all(self):
        self.selected_indices = set(range(len(self.files_list)))
        self._refresh_list()

    def _deselect_all(self):
        self.selected_indices.clear()
        self._refresh_list()

    def _preview_file(self, idx):
        f = self.files_list[idx]
        try:
            a = self.engine.analyze_file(f["path"])
            self.preview_analysis = a
            self.preview_name.config(text=f["name"])

            lines = []
            lines.append(f"Type: {a['file_type'].title()} | Size: {a['file_size_kb']} KB")
            if a["width"]:
                lines.append(f"Dimensions: {a['width']} x {a['height']}px ({a['orientation'].title()})")
                lines.append(f"Megapixels: {round(a['width']*a['height']/1e6, 2)}")
            lines.append(f"Brightness: {a['brightness'].title()}")
            if a["dominant_colors"]:
                colors_str = "  ".join([f"\u25cf {c['name']} ({c['ratio']}%)" for c in a["dominant_colors"][:4]])
                lines.append(f"Colors: {colors_str}")
            if a["has_transparency"]:
                lines.append("Transparency: Yes")
            if a["exif"]:
                exif_items = list(a["exif"].items())[:4]
                for k, v in exif_items:
                    if isinstance(v, str) and len(v) > 40:
                        v = v[:37] + "..."
                    lines.append(f"EXIF {k}: {v}")

            self.preview_info.delete(1.0, tk.END)
            self.preview_info.insert(tk.END, "\n".join(lines))
            self._status(f"Preview: {f['name']}", THEME["text_sec"])

            if f["stem"] in self.generated_data_map:
                self._display_generated(f["stem"])
        except Exception as e:
            self.preview_info.delete(1.0, tk.END)
            self.preview_info.insert(tk.END, f"Error: {str(e)}")

    # ==================== PROCESS ====================
    def _process_selected(self):
        if not self.selected_indices:
            messagebox.showwarning("", "Pilih file dulu (centang).")
            return
        self._show_progress(True)
        self.window.update()
        try:
            plat = self.platform_var.get()
            for idx in list(self.selected_indices):
                f = self.files_list[idx]
                try:
                    data, analysis = self.engine.generate_from_file(
                        f["path"], platform=plat, num_keywords=50, num_titles=3, num_desc=1)
                    self.generated_data_map[f["stem"]] = {"data": data, "analysis": analysis}
                except Exception as e:
                    print(f"Skip {f['name']}: {e}")

            self._refresh_list()
            if self.selected_indices:
                first_idx = min(self.selected_indices)
                self._preview_file(first_idx)
            self._status(f"Processed {len(self.generated_data_map)} files.", THEME["accent"])
        except Exception as e:
            self._status(f"Error: {str(e)}", THEME["danger"])
        finally:
            self._show_progress(False)

    def _display_generated(self, stem):
        if stem not in self.generated_data_map:
            return
        entry = self.generated_data_map[stem]
        data = entry["data"]
        analysis = entry["analysis"]

        self.kw_text.delete(1.0, tk.END)
        kws = [k.strip() for k in data[0]["keywords"].split(",")]
        for i, kw in enumerate(kws, 1):
            self.kw_text.insert(tk.END, f"{i:>3}. {kw}\n")
        self.kw_count.config(text=str(len(kws)))

        self.td_text.delete(1.0, tk.END)
        for i, row in enumerate(data):
            self.td_text.insert(tk.END, f"{'='*40}\n  SET {i+1}\n{'='*40}\n")
            self.td_text.insert(tk.END, f"  File: {row['filename']}\n")
            self.td_text.insert(tk.END, f"  [{row['category']}]\n\n")
            self.td_text.insert(tk.END, f"  Title:\n  {row['title']}\n\n")

    # ==================== MOVE / COPY ====================
    def _set_destination(self):
        d = filedialog.askdirectory(title="Pilih folder tujuan")
        if d:
            self.dest_dir = d
            self.dest_label.config(text=f"Dest: [{os.path.basename(d)}]")

    def _move_copy(self, mode):
        if not self.dest_dir:
            messagebox.showwarning("", "Set destination folder dulu.")
            return
        if not self.generated_data_map:
            messagebox.showwarning("", "Proses file dulu (Process All) sebelum move/copy.")
            return

        verb = "Moving" if mode == "move" else "Copying"
        done = 0
        errors = 0
        for stem, entry in self.generated_data_map.items():
            source = entry["analysis"]["filepath"]
            title = entry["data"][0]["title"]
            safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:60]

            try:
                if mode == "move":
                    self.engine.move_file_with_rename(source, self.dest_dir, safe_name)
                else:
                    self.engine.copy_file_with_rename(source, self.dest_dir, safe_name)
                done += 1
            except Exception as e:
                errors += 1
                print(f"{verb} error: {e}")

        msg = f"{verb} complete: {done} success"
        if errors:
            msg += f", {errors} errors"
        self._status(msg, THEME["accent"])
        messagebox.showinfo("Complete", msg)

    # ==================== EXPORT CSV ====================
    def _export_csv(self):
        if not self.generated_data_map:
            messagebox.showwarning("", "Tidak ada data. Process file dulu.")
            return

        plat = self.platform_var.get()
        headers = self.engine.get_platform_csv_headers(plat)

        default_name = f"diasin_{plat.replace(' ','_')}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], initialfile=default_name)
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                for stem, entry in self.generated_data_map.items():
                    for row in entry["data"]:
                        formatted = self.engine.get_platform_csv_row(row, plat)
                        w.writerow(formatted)

            self._status(f"\u2713 CSV saved: {os.path.basename(path)} ({plat})", THEME["accent"])
            messagebox.showinfo("Success", f"CSV exported successfully!\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== BATCH DIALOG ====================
    def _show_batch_dialog(self):
        d = tb.Toplevel(self.window)
        d.title("Batch Mode")
        d.geometry("550x500")
        d.transient(self.window)
        d.grab_set()
        f = tk.Frame(d, bg=THEME["card"], padx=20, pady=20)
        f.pack(fill="both", expand=True)
        tk.Label(f, text="BATCH CONCEPTS", font=("Segoe UI", 8, "bold"),
                 fg=THEME["text_muted"], bg=THEME["card"]).pack(anchor="w")
        tk.Label(f, text="Enter multiple concepts (one per line):", font=("Segoe UI", 10),
                 fg=THEME["text"], bg=THEME["card"]).pack(anchor="w", pady=(4, 10))
        txt = tk.Text(f, wrap=tk.WORD, font=("Consolas", 10), bg="#0d1117",
                      fg=THEME["text"], relief="flat", bd=0, highlightthickness=1,
                      highlightbackground=THEME["border"], height=10)
        txt.pack(fill="both", expand=True)
        txt.insert(tk.END, "sunset\nmountain beach\ncity skyline\nbusiness team\n")

        sr = tk.Frame(f, bg=THEME["card"])
        sr.pack(fill="x", pady=(10, 0))
        tk.Label(sr, text="Keywords/concept:", font=("Segoe UI", 9),
                 fg=THEME["text_sec"], bg=THEME["card"]).pack(side="left", padx=(0, 6))
        bkw = tk.Spinbox(sr, from_=10, to=100, font=("Segoe UI", 9), width=5,
                         bg=THEME["input_bg"], fg=THEME["text"], relief="flat",
                         highlightthickness=1, highlightbackground=THEME["border"])
        bkw.delete(0, tk.END); bkw.insert(0, "40")
        bkw.pack(side="left")

        tk.Label(sr, text=" Platform:", font=("Segoe UI", 9), fg=THEME["text_sec"],
                 bg=THEME["card"]).pack(side="left", padx=(12, 4))
        bplat = ttk.Combobox(sr, values=["Adobe Stock", "Shutterstock"],
                             state="readonly", width=14)
        bplat.set("Adobe Stock")
        bplat.pack(side="left")

        br = tk.Frame(f, bg=THEME["card"])
        br.pack(fill="x", pady=(10, 0))
        tk.Label(br, text="", bg=THEME["card"], width=6).pack(side="right")
        self._btn(br, "Cancel", THEME["text_muted"], d.destroy).pack(side="right", padx=(0, 6))
        self._btn(br, " Generate CSV ", THEME["accent"],
                  lambda: self._do_batch(txt, bkw, bplat, d)).pack(side="right")

    def _do_batch(self, txt, sp, plat_combo, d):
        concepts = [c.strip() for c in txt.get(1.0, tk.END).strip().split("\n") if c.strip()]
        if not concepts:
            return
        kw = int(sp.get())
        plat = plat_combo.get()
        headers = self.engine.get_platform_csv_headers(plat)

        default = f"diasin_batch_{plat.replace(' ','_')}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile=default, parent=d)
        if not path:
            return
        try:
            rows = []
            for c in concepts:
                data = self.engine.generate_csv_data(c, kw, 1, 1)
                for row in data:
                    rows.append(self.engine.get_platform_csv_row(row, plat))

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                w.writerows(rows)
            self._status(f"Batch: {len(concepts)} concepts -> {os.path.basename(path)} ({plat})", THEME["accent"])
            d.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=d)

    # ==================== HELPERS ====================
    def _status(self, msg, color=THEME["text_sec"]):
        self.status_label.config(text=msg, fg=color)

    def _show_progress(self, show):
        if show:
            self.progress.pack(side="right", padx=(8, 4))
            self.progress.start()
            self.status_icon.config(text="\u23f3", fg=THEME["warning"])
        else:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_icon.config(text="\u26a1", fg=THEME["accent"])

    def _copy_text(self, widget):
        c = widget.get(1.0, tk.END).strip()
        if c:
            self.window.clipboard_clear()
            self.window.clipboard_append(c)
            self._status("\u2713 Copied!", THEME["accent"])

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    DiasinApp().run()
