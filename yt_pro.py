import ctypes
import datetime as dt
import glob
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from tkinter import filedialog, messagebox

import customtkinter as ctk


APP_VERSION = "1.2"
APP_TITLE = f"YouTube Downloader {APP_VERSION}"
YTDLP_EXE_NAME = "yt-dlp.exe"
YTDLP_MAX_AGE_DAYS = 90
YTDLP_LATEST_RELEASE_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest"
YTDLP_DOWNLOAD_URL = (
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
)


def configure_process_encoding():
    """Make Python and child-process text streams prefer UTF-8 on Windows."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONLEGACYWINDOWSSTDIO", "0")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


configure_process_encoding()

# 全局美化设置
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class YtDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                f"Youtube Downloader {APP_VERSION}"
            )
        except Exception:
            pass

        if getattr(sys, "frozen", False):
            self.resource_path = sys._MEIPASS  # type: ignore[attr-defined]
            self.app_path = os.path.dirname(sys.executable)
        else:
            self.resource_path = os.path.dirname(os.path.abspath(__file__))
            self.app_path = self.resource_path

        self.title(APP_TITLE)
        self.geometry("840x690")
        self.minsize(760, 620)

        try:
            icon_path = os.path.join(self.resource_path, "my.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self.save_path = self.app_path
        self.process = None
        self.is_user_stopping = False
        self.is_updating = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.top_frame = ctk.CTkFrame(
            self, height=80, corner_radius=0, fg_color="#1a1a1a"
        )
        self.top_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        self.title_label = ctk.CTkLabel(
            self.top_frame,
            text="YOUTUBE DOWNLOADER",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#3b8ed0",
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")

        self.input_card = ctk.CTkFrame(
            self, fg_color="#2b2b2b", corner_radius=12
        )
        self.input_card.grid(row=1, column=0, padx=30, pady=10, sticky="nsew")

        self.url_entry = ctk.CTkEntry(
            self.input_card,
            placeholder_text="请粘贴视频链接 (URL)...",
            height=45,
            width=640,
            border_width=1,
            corner_radius=8,
            fg_color="#333333",
        )
        self.url_entry.pack(pady=(20, 10), padx=20)

        self.path_row = ctk.CTkFrame(self.input_card, fg_color="transparent")
        self.path_row.pack(fill="x", padx=25, pady=(0, 20))

        self.path_label = ctk.CTkLabel(
            self.path_row,
            text=f"存储位置: {self.save_path}",
            font=("Microsoft YaHei", 12),
            text_color="#aaaaaa",
            anchor="w",
        )
        self.path_label.pack(side="left", fill="x", expand=True)

        self.path_btn = ctk.CTkButton(
            self.path_row,
            text="更改目录",
            width=90,
            height=28,
            fg_color="#444444",
            hover_color="#555555",
            command=self.choose_save_path,
        )
        self.path_btn.pack(side="right", padx=(12, 0))

        self.control_card = ctk.CTkFrame(
            self, fg_color="#2b2b2b", corner_radius=12
        )
        self.control_card.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")

        self.progress_label = ctk.CTkLabel(
            self.control_card,
            text="STATUS: IDLE",
            font=("Consolas", 14, "bold"),
        )
        self.progress_label.pack(pady=(15, 5))

        self.progress_bar = ctk.CTkProgressBar(
            self.control_card,
            width=720,
            height=12,
            progress_color="#3b8ed0",
            fg_color="#1a1a1a",
        )
        self.progress_bar.pack(pady=10, padx=20)
        self.progress_bar.set(0)

        self.btn_group = ctk.CTkFrame(self.control_card, fg_color="transparent")
        self.btn_group.pack(pady=(10, 20))

        btn_style = {
            "width": 118,
            "height": 40,
            "corner_radius": 20,
            "font": ("Microsoft YaHei", 12, "bold"),
            "border_width": 0,
        }

        self.start_btn = ctk.CTkButton(
            self.btn_group,
            text="开始/继续",
            fg_color="#007AFF",
            hover_color="#58A6FF",
            command=self.start_task,
            **btn_style,
        )
        self.start_btn.grid(row=0, column=0, padx=6)

        self.pause_btn = ctk.CTkButton(
            self.btn_group,
            text="暂停",
            fg_color="#8E8E93",
            hover_color="#AEAEB2",
            text_color="white",
            command=self.pause_task,
            state="disabled",
            **btn_style,
        )
        self.pause_btn.grid(row=0, column=1, padx=6)

        self.stop_btn = ctk.CTkButton(
            self.btn_group,
            text="终止",
            fg_color="#FF3B30",
            hover_color="#FF6961",
            command=self.stop_task,
            state="disabled",
            **btn_style,
        )
        self.stop_btn.grid(row=0, column=2, padx=6)

        self.retry_btn = ctk.CTkButton(
            self.btn_group,
            text="重试",
            fg_color="#34C759",
            hover_color="#30D158",
            command=self.confirm_retry,
            **btn_style,
        )
        self.retry_btn.grid(row=0, column=3, padx=6)

        self.update_btn = ctk.CTkButton(
            self.btn_group,
            text="更新组件",
            fg_color="#AF52DE",
            hover_color="#BF5AF2",
            command=self.confirm_update_yt_dlp,
            **btn_style,
        )
        self.update_btn.grid(row=0, column=4, padx=6)

        self.log_textbox = ctk.CTkTextbox(
            self,
            fg_color="#1a1a1a",
            text_color="#78a1ff",
            font=("Consolas", 12),
            border_width=1,
            border_color="#333333",
        )
        self.log_textbox.grid(row=3, column=0, padx=30, pady=(10, 30), sticky="nsew")
        self.log_write(">> 作者: BiliBili@想取一个帅帅的名字\n")
        self.log_write(f">> 版本号: {APP_VERSION}\n")
        self.log_write(">> 软件已就绪，等待输入链接...\n")

        threading.Thread(target=self.check_yt_dlp_version, daemon=True).start()

    def log_write(self, text):
        self.log_textbox.insert("end", text)
        self.log_textbox.see("end")

    def choose_save_path(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path = folder
            self.path_label.configure(text=f"存储位置: {folder}")

    def start_task(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("缺少链接", "请先粘贴视频链接。")
            return
        if self.is_updating:
            messagebox.showinfo("正在更新", "yt-dlp 正在更新，请稍后再开始下载。")
            return

        outdated, version_text = self.is_yt_dlp_outdated()
        if outdated:
            msg = (
                f"当前 yt-dlp 版本 {version_text} 已超过 {YTDLP_MAX_AGE_DAYS} 天，"
                "请先点击“更新组件”。"
            )
            self.progress_label.configure(text="ERROR: 请先更新组件", text_color="#e74c3c")
            self.log_write(f">> {msg}\n")
            messagebox.showwarning("组件过期", msg)
            return

        self.is_user_stopping = False
        self.toggle_buttons("downloading")
        self.log_write(f">> 正在解析链接: {url}\n")
        threading.Thread(target=self.run_yt_dlp, args=(url,), daemon=True).start()

    def run_yt_dlp(self, url):
        yt_dlp_exe = self.get_yt_dlp_path()
        if not os.path.exists(yt_dlp_exe):
            self.after(
                0,
                self.on_finish,
                f"ERROR: 未找到 {YTDLP_EXE_NAME}",
                "#e74c3c",
            )
            return

        output_template = os.path.join(self.save_path, "%(title)s.%(ext)s")
        command = [
            yt_dlp_exe,
            "--encoding",
            "utf-8",
            "--compat-options",
            "no-youtube-unavailable-videos",
            "-f",
            "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "--ffmpeg-location",
            self.resource_path,
            "--newline",
            "--no-playlist",
            "-o",
            output_template,
            url,
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=self.get_hidden_si(),
                env=self.get_subprocess_env(),
            )
            for line in self.process.stdout:  # type: ignore[union-attr]
                if self.is_user_stopping:
                    break
                self.after(0, self.log_write, line)
                if self.handle_download_line(line):
                    self.is_user_stopping = True
                    self.force_kill_process()
                    self.after(
                        0,
                        self.on_finish,
                        "ERROR: 组件过期，请先更新组件",
                        "#e74c3c",
                    )
                    self.after(
                        0,
                        lambda: messagebox.showwarning(
                            "组件过期",
                            "当前 yt-dlp 组件已过期，请先点击“更新组件”后再下载。",
                        ),
                    )
                    return

            if not self.process:
                return
            self.process.wait()
            return_code = self.process.returncode
            self.process = None
            if not self.is_user_stopping:
                if return_code == 0:
                    self.after(0, self.on_finish, "SUCCESS: 下载完成", "#2ecc71")
                else:
                    self.after(
                        0,
                        self.on_finish,
                        "ERROR: 任务异常中断，可尝试更新组件后重试",
                        "#e74c3c",
                    )
        except Exception as e:
            self.process = None
            self.after(0, lambda: messagebox.showerror("Fatal Error", str(e)))
            self.after(0, self.toggle_buttons, "idle")

    def handle_download_line(self, line):
        match = re.search(r"(\d+(?:\.\d+)?)%", line)
        if match:
            self.after(0, self.update_ui_progress, float(match.group(1)))

        lowered = line.lower()
        if "older than 90 days" in lowered:
            self.after(0, self.log_write, ">> 组件已过期，任务已终止，请先更新组件。\n")
            return True

        if "merging formats" in lowered or "merging" in lowered:
            self.after(
                0,
                lambda: self.progress_label.configure(
                    text="STATUS: 正在合成高画质视频...",
                    text_color="#f1c40f",
                ),
            )
        if "update" in lowered and ("yt-dlp" in lowered or "outdated" in lowered):
            self.after(
                0,
                self.log_write,
                ">> 检测到组件可能过期，建议点击“更新组件”后重试。\n",
            )
        return False

    def pause_task(self):
        self.is_user_stopping = True
        self.force_kill_process()
        self.toggle_buttons("paused")
        self.progress_label.configure(text="PAUSED: 任务已暂停", text_color="#f1c40f")
        self.log_write(">> 任务已手动暂停。\n")

    def stop_task(self):
        if messagebox.askyesno("终止确认", "确定要终止下载并清理临时文件吗？"):
            self.is_user_stopping = True
            self.force_kill_process()
            self.clean_files()
            self.progress_bar.set(0)
            self.progress_label.configure(text="STOPPED: 任务已清空", text_color="#e74c3c")
            self.toggle_buttons("idle")
            self.log_write(">> 任务已终止，临时文件已清理。\n")
            self.after(5000, self.reset_status_label)

    def reset_status_label(self):
        if not self.process and self.start_btn.cget("state") == "normal":
            self.progress_label.configure(text="STATUS: IDLE", text_color="white")

    def confirm_retry(self):
        if messagebox.askyesno("重试确认", "是否要删除进度并从头开始重新下载？"):
            self.is_user_stopping = True
            self.force_kill_process()
            self.clean_files()
            self.progress_bar.set(0)
            self.start_task()

    def force_kill_process(self):
        if self.process:
            try:
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                    startupinfo=self.get_hidden_si(),
                )
            except Exception:
                pass
            self.process = None

    def clean_files(self):
        patterns = ["*.part", "*.ytdl", "*.temp", "*.tmp"]
        for pattern in patterns:
            for path in glob.glob(os.path.join(self.save_path, pattern)):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def toggle_buttons(self, state):
        if state == "downloading":
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
            self.update_btn.configure(state="disabled")
        elif state == "updating":
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
            self.update_btn.configure(state="disabled")
        elif state in ["paused", "idle"]:
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal" if state == "paused" else "disabled")
            self.update_btn.configure(state="normal")

    def update_ui_progress(self, val):
        if not self.is_user_stopping:
            self.progress_bar.set(val / 100)
            self.progress_label.configure(text=f"DOWNLOADING: {val:.1f}%", text_color="#3498db")

    def update_component_progress(self, downloaded, total):
        if total > 0:
            percent = min(downloaded / total * 100, 100)
            self.progress_bar.set(percent / 100)
            self.progress_label.configure(
                text=f"UPDATING: {percent:.1f}%",
                text_color="#f1c40f",
            )
        else:
            downloaded_mb = downloaded / 1024 / 1024
            self.progress_label.configure(
                text=f"UPDATING: {downloaded_mb:.1f} MB",
                text_color="#f1c40f",
            )

    def on_finish(self, msg, color):
        self.toggle_buttons("idle")
        self.progress_label.configure(text=msg, text_color=color)
        if msg.startswith("SUCCESS"):
            messagebox.showinfo("下载成功", "最高画质视频已保存。")

    def confirm_update_yt_dlp(self):
        if self.is_updating:
            return
        if messagebox.askyesno(
            "更新组件",
            "将联网更新 yt-dlp 组件，用于修复视频站点规则变化导致的下载失败。是否继续？",
        ):
            threading.Thread(target=self.update_yt_dlp, daemon=True).start()

    def check_yt_dlp_version(self):
        yt_dlp_exe = self.get_yt_dlp_path()
        if not os.path.exists(yt_dlp_exe):
            self.after(0, self.log_write, f">> 未找到 {YTDLP_EXE_NAME}，请点击“更新组件”。\n")
            return

        version_text = self.get_yt_dlp_version(yt_dlp_exe)
        if version_text:
            self.after(0, self.log_write, f">> yt-dlp 当前版本: {version_text}\n")
            if self.is_version_text_outdated(version_text):
                self.after(
                    0,
                    self.log_write,
                    f">> yt-dlp 已超过 {YTDLP_MAX_AGE_DAYS} 天，下载前需要先更新组件。\n",
                )
        else:
            self.after(0, self.log_write, ">> yt-dlp 版本读取失败，建议更新组件。\n")

    def update_yt_dlp(self):
        self.is_updating = True
        self.after(0, self.toggle_buttons, "updating")
        self.after(
            0,
            lambda: self.progress_label.configure(
                text="STATUS: 正在检查组件版本...",
                text_color="#f1c40f",
            ),
        )
        self.after(0, self.progress_bar.set, 0)
        self.after(0, self.log_write, ">> 正在检查 yt-dlp 最新版本...\n")

        try:
            yt_dlp_exe = self.prepare_writable_yt_dlp()
            local_version = self.get_yt_dlp_version(yt_dlp_exe)
            latest_version = self.get_latest_yt_dlp_version()

            if local_version:
                self.after(0, self.log_write, f">> 本地版本: {local_version}\n")
            self.after(0, self.log_write, f">> 最新版本: {latest_version}\n")

            if local_version and self.same_version(local_version, latest_version):
                self.finish_update_current(latest_version)
                return

            self.after(
                0,
                lambda: self.progress_label.configure(
                    text="STATUS: 正在下载新版组件...",
                    text_color="#f1c40f",
                ),
            )
            self.after(0, self.log_write, ">> 发现新版组件，开始下载...\n")
            self.download_latest_yt_dlp(yt_dlp_exe)
            self.finish_update_success(yt_dlp_exe)
        except Exception as e:
            error_text = str(e) or "未知错误"
            self.after(0, self.log_write, f">> 更新失败: {error_text}\n")
            self.after(
                0,
                lambda: self.progress_label.configure(
                    text="ERROR: 组件更新失败",
                    text_color="#e74c3c",
                ),
            )
            self.after(
                0,
                lambda: messagebox.showerror(
                    "组件更新失败",
                    f"yt-dlp 组件更新失败：\n{error_text}",
                ),
            )
        finally:
            self.is_updating = False
            self.after(0, self.toggle_buttons, "idle")

    def finish_update_current(self, version_text):
        self.after(0, self.progress_bar.set, 1)
        self.after(0, self.log_write, ">> yt-dlp 已是最新版本，无需更新。\n")
        self.after(
            0,
            lambda: self.progress_label.configure(
                text="SUCCESS: 已是最新版本",
                text_color="#2ecc71",
            ),
        )
        self.after(
            0,
            lambda: messagebox.showinfo(
                "无需更新",
                f"yt-dlp 已是最新版本：{version_text}",
            ),
        )

    def finish_update_success(self, yt_dlp_exe):
        version_text = self.get_yt_dlp_version(yt_dlp_exe) or "未知版本"
        self.after(0, self.progress_bar.set, 1)
        self.after(0, self.log_write, f">> yt-dlp 更新完成，当前版本: {version_text}\n")
        self.after(
            0,
            lambda: self.progress_label.configure(
                text="SUCCESS: 组件已更新",
                text_color="#2ecc71",
            ),
        )

    def download_latest_yt_dlp(self, target_path):
        temp_path = target_path + ".download.exe"
        request = urllib.request.Request(
            YTDLP_DOWNLOAD_URL,
            headers={
                "User-Agent": f"YouTube-Downloader/{APP_VERSION}",
                "Accept": "application/octet-stream",
            },
        )

        self.after(0, self.log_write, f">> 下载地址: {YTDLP_DOWNLOAD_URL}\n")
        self.after(0, self.progress_bar.set, 0)
        with urllib.request.urlopen(request, timeout=180) as response:
            total = self.get_response_length(response)
            downloaded = 0
            with open(temp_path, "wb") as temp_file:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    temp_file.write(chunk)
                    downloaded += len(chunk)
                    self.after(0, self.update_component_progress, downloaded, total)

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) < 1024 * 1024:
            raise RuntimeError("下载到的 yt-dlp.exe 文件异常。")

        version_text = self.get_yt_dlp_version(temp_path)
        if not version_text:
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise RuntimeError("新版 yt-dlp.exe 验证失败，已保留原组件。")

        os.replace(temp_path, target_path)

    def get_latest_yt_dlp_version(self):
        request = urllib.request.Request(
            YTDLP_LATEST_RELEASE_URL,
            headers={"User-Agent": f"YouTube-Downloader/{APP_VERSION}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                final_url = response.geturl()
        except Exception as e:
            raise RuntimeError(f"无法获取 yt-dlp 最新版本信息：{e}") from e

        match = re.search(r"/releases/tag/([^/?#]+)", final_url)
        if not match:
            raise RuntimeError("无法解析 yt-dlp 最新版本号。")
        return match.group(1).lstrip("v")

    def same_version(self, local_version, latest_version):
        return local_version.strip().lstrip("v") == latest_version.strip().lstrip("v")

    def get_response_length(self, response):
        try:
            return int(response.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            return 0

    def get_yt_dlp_version(self, yt_dlp_exe):
        version = self.run_command([yt_dlp_exe, "--version"], timeout=15)
        if version.returncode == 0 and version.output.strip():
            return version.output.strip().splitlines()[-1].strip()
        return ""

    def is_yt_dlp_outdated(self):
        yt_dlp_exe = self.get_yt_dlp_path()
        if not os.path.exists(yt_dlp_exe):
            return True, "未安装"
        version_text = self.get_yt_dlp_version(yt_dlp_exe)
        if not version_text:
            return True, "未知"
        return self.is_version_text_outdated(version_text), version_text

    def is_version_text_outdated(self, version_text):
        match = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", version_text)
        if not match:
            return False
        year, month, day = map(int, match.groups())
        try:
            version_date = dt.date(year, month, day)
        except ValueError:
            return False
        return (dt.date.today() - version_date).days > YTDLP_MAX_AGE_DAYS

    def prepare_writable_yt_dlp(self):
        writable_path = os.path.join(self.app_path, YTDLP_EXE_NAME)
        bundled_path = os.path.join(self.resource_path, YTDLP_EXE_NAME)

        if os.path.exists(writable_path):
            return writable_path
        if os.path.exists(bundled_path):
            shutil.copy2(bundled_path, writable_path)
            return writable_path
        raise FileNotFoundError(f"未找到 {YTDLP_EXE_NAME}")

    def get_yt_dlp_path(self):
        writable_path = os.path.join(self.app_path, YTDLP_EXE_NAME)
        if os.path.exists(writable_path):
            return writable_path
        return os.path.join(self.resource_path, YTDLP_EXE_NAME)

    def run_command(self, command, timeout=None):
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=self.get_hidden_si(),
                env=self.get_subprocess_env(),
                timeout=timeout,
            )
            return CommandResult(completed.returncode, completed.stdout or "")
        except subprocess.TimeoutExpired as e:
            output = e.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            return CommandResult(1, output + "\n命令执行超时。\n")

    def get_hidden_si(self):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si

    def get_subprocess_env(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["LC_ALL"] = "C.UTF-8"
        env["LANG"] = "C.UTF-8"
        return env


class CommandResult:
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output


if __name__ == "__main__":
    app = YtDownloaderApp()
    app.mainloop()
