# YouTube 视频下载器

基于 yt-dlp 和 FFmpeg 9.0 的 Windows 图形界面下载器。

## 使用方式

从 Releases 下载 `YouTube_downloader_1.2.exe` 后直接运行。程序已内置 FFmpeg 9.0、ffprobe 和 yt-dlp；当前构建支持 Windows 10 或更高版本。

## 从源码构建

将 `ffmpeg.exe`、`ffprobe.exe`、`yt-dlp.exe` 和 `my.ico` 放在项目目录，然后运行：

```powershell
pyinstaller yt_pro.spec
```

FFmpeg 9.0 Windows essentials build 来自 [GyanD/codexffmpeg](https://github.com/GyanD/codexffmpeg/releases/tag/9.0)，对应 FFmpeg 源码提交 [`d32b387f2b`](https://github.com/FFmpeg/FFmpeg/commit/d32b387f2b)。
