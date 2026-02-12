# YouTube视频下载器
使用了ffmpeg+ffplay+ffprobe+yt-dlp
# 使用方式 
保证ffmpeg.exe、ffplay.exe、ffprobe+yt、yt-dlp.exe和yt_pro.py在同一文件夹下
# 在该文件夹中打开终端
## 使用命令 ##
pyinstaller --noconsole --onefile --name "YouTube 下载器" --icon="my.ico" --add-data "my.ico;." --add-data "yt-dlp.exe;." --add-data "ffmpeg.exe;." --add-data "ffprobe.exe;." yt_pro.py
# 
