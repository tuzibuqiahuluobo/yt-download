import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import ctypes
import re
import os
import sys
import glob

# 全局美化设置
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("blue")

class YtDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        myappid = 'Youtube Downloader 1.0' # 随便起个名字
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # --- 1. 必须先初始化路径变量，才能被后面调用 ---
        if getattr(sys, 'frozen', False):
            self.resource_path = sys._MEIPASS
            self.app_path = os.path.dirname(sys.executable)
        else:
            self.resource_path = os.path.dirname(os.path.abspath(__file__))
            self.app_path = self.resource_path

        # 窗口基础设置
        self.title("YouTube Downloader 1.0")
        self.geometry("800x650")
        
        # --- 2. 安全加载窗口图标 ---
        try:
            icon_path = os.path.join(self.resource_path, "my.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass # 如果图标格式不对或不存在，跳过，不影响主程序启动
        
        self.save_path = self.app_path
        self.process = None
        self.is_user_stopping = False 

        # --- 3. UI 布局 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 1. 顶部装饰条与标题
        self.top_frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#1a1a1a")
        self.top_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        self.title_label = ctk.CTkLabel(self.top_frame, text="YOUTUBE DOWNLOADER", 
                                        font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
                                        text_color="#3b8ed0")
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")

        # 2. 输入区域卡片
        self.input_card = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=12)
        self.input_card.grid(row=1, column=0, padx=30, pady=10, sticky="nsew")
        
        self.url_entry = ctk.CTkEntry(self.input_card, placeholder_text=" 请粘贴视频链接 (URL)...", 
                                      height=45, width=600, border_width=1, corner_radius=8,
                                      fg_color="#333333")
        self.url_entry.pack(pady=(20, 10), padx=20)

        self.path_label = ctk.CTkLabel(self.input_card, text=f"📍 存储位置: {self.save_path}", 
                                       font=("Microsoft YaHei", 12), text_color="#aaaaaa")
        self.path_label.pack(side="left", padx=25, pady=(0, 20))
        
        self.path_btn = ctk.CTkButton(self.input_card, text="更改目录", width=90, height=28,
                                      fg_color="#444444", hover_color="#555555", command=self.choose_save_path)
        self.path_btn.pack(side="right", padx=25, pady=(0, 20))

        # 3. 进度与控制卡片
        self.control_card = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=12)
        self.control_card.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")

        self.progress_label = ctk.CTkLabel(self.control_card, text="STATUS: IDLE", font=("Consolas", 14, "bold"))
        self.progress_label.pack(pady=(15, 5))

        self.progress_bar = ctk.CTkProgressBar(self.control_card, width=680, height=12, 
                                               progress_color="#3b8ed0", fg_color="#1a1a1a")
        self.progress_bar.pack(pady=10, padx=20)
        self.progress_bar.set(0)

        # 按钮组 - iOS 风格
        self.btn_group = ctk.CTkFrame(self.control_card, fg_color="transparent")
        self.btn_group.pack(pady=(10, 20))

        ios_btn_style = {
            "width": 120, 
            "height": 40, 
            "corner_radius": 20,
            "font": ("Microsoft YaHei", 12, "bold"),
            "border_width": 0
        }

        self.start_btn = ctk.CTkButton(self.btn_group, text="▶ 开始/继续", fg_color="#007AFF", hover_color="#58A6FF", **ios_btn_style, command=self.start_task)
        self.start_btn.grid(row=0, column=0, padx=8)

        self.pause_btn = ctk.CTkButton(self.btn_group, text="⏸ 暂停", fg_color="#8E8E93", hover_color="#AEAEB2", text_color="white", **ios_btn_style, command=self.pause_task, state="disabled")
        self.pause_btn.grid(row=0, column=1, padx=8)

        self.stop_btn = ctk.CTkButton(self.btn_group, text="⏹ 终止", fg_color="#FF3B30", hover_color="#FF6961", **ios_btn_style, command=self.stop_task, state="disabled")
        self.stop_btn.grid(row=0, column=2, padx=8)

        self.retry_btn = ctk.CTkButton(self.btn_group, text="🔄 重试", fg_color="#34C759", hover_color="#30D158", **ios_btn_style, command=self.confirm_retry)
        self.retry_btn.grid(row=0, column=3, padx=8)

        # 4. 实时日志区域
        self.log_textbox = ctk.CTkTextbox(self, fg_color="#1a1a1a", text_color="#5d8df5", 
                                          font=("Consolas", 12), border_width=1, border_color="#333333")
        self.log_textbox.grid(row=3, column=0, padx=30, pady=(10, 30), sticky="nsew")
        self.log_write(">> 作者：BiliBili@想取一个帅帅的名字\n")
        self.log_write(">> 版本号: 1.0.0\n")
        self.log_write(">> 软件已就绪，等待输入链接...\n")

    # --- 逻辑函数部分保持不变 ---
    def log_write(self, text):
        self.log_textbox.insert("end", text)
        self.log_textbox.see("end")

    def choose_save_path(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path = folder
            self.path_label.configure(text=f"📍 存储位置: {folder}")

    def start_task(self):
        url = self.url_entry.get().strip()
        if not url: return
        self.is_user_stopping = False
        self.toggle_buttons("downloading")
        self.log_write(f">> 正在解析链接: {url}\n")
        threading.Thread(target=self.run_yt_dlp, args=(url,), daemon=True).start()

    def run_yt_dlp(self, url):
        yt_dlp_exe = os.path.join(self.resource_path, "yt-dlp.exe")
        output_template = os.path.join(self.save_path, "%(title)s.%(ext)s")
        command = [yt_dlp_exe, '-f', 'bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]', '--ffmpeg-location', self.resource_path, '--newline', '--no-playlist', '-o', output_template, url]
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=si)
            for line in self.process.stdout:
                if self.is_user_stopping: break
                self.after(0, self.log_write, line)
                match = re.search(r'(\d+\.\d+)%', line)
                if match: self.after(0, self.update_ui_progress, float(match.group(1)))
                if "Merging" in line: self.after(0, lambda: self.progress_label.configure(text="状态: 正在合成高画质视频...", text_color="#f1c40f"))
            self.process.wait()
            if not self.is_user_stopping:
                if self.process.returncode == 0: self.after(0, self.on_finish, "SUCCESS: 下载完成", "#2ecc71")
                else: self.after(0, self.on_finish, "ERROR: 任务异常中断", "#e74c3c")
        except Exception as e: self.after(0, lambda: messagebox.showerror("Fatal Error", str(e)))

    def pause_task(self):
        self.is_user_stopping = True
        self.force_kill_process()
        self.toggle_buttons("paused")
        self.progress_label.configure(text="PAUSED: 任务已暂停", text_color="#f1c40f")
        self.log_write(">> 任务已手动暂停。\n")

    def stop_task(self):
        if messagebox.askyesno("终止确认", "确定要终止下载并清理所有碎片吗？"):
            self.is_user_stopping = True
            self.force_kill_process()
            self.clean_files()
            self.progress_bar.set(0)
            self.progress_label.configure(text="STOPPED: 任务已清空", text_color="#e74c3c")
            self.toggle_buttons("idle")
            self.log_write(">> 任务已终止，临时文件已清理。\n")
            
            # --- 新增：5秒后自动重置状态文字 ---
            # 5000 毫秒 = 5 秒
            self.after(5000, self.reset_status_label)

    # --- 新增：重置文字的函数 ---
    def reset_status_label(self):
        # 只有在当前确实是停止状态时才重置，避免覆盖正在下载的状态
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
            try: subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], startupinfo=self.get_hidden_si())
            except: pass
            self.process = None

    def get_hidden_si(self):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si

    def clean_files(self):
        patterns = ["*.part", "*.ytdl", "*.temp", "*.tmp"]
        for p in patterns:
            for f in glob.glob(os.path.join(self.save_path, p)):
                try: os.remove(f)
                except: pass

    def toggle_buttons(self, state):
        if state == "downloading":
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
        elif state in ["paused", "idle"]:
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal" if state == "paused" else "disabled")

    def update_ui_progress(self, val):
        if not self.is_user_stopping:
            self.progress_bar.set(val / 100)
            self.progress_label.configure(text=f"DOWNLOADING: {val}%", text_color="#3498db")

    def on_finish(self, msg, color):
        self.toggle_buttons("idle")
        self.progress_label.configure(text=msg, text_color=color)
        if "SUCCESS" in msg: messagebox.showinfo("下载成功", "最高画质视频已保存。")

if __name__ == "__main__":
    app = YtDownloaderApp()
    app.mainloop()