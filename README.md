# YouTube 视频下载器

基于 yt-dlp 和 FFmpeg 9.0 的 Windows 图形界面下载器。

## 使用方式

从 Releases 下载 `YouTube_downloader_1.2.2.exe` 后直接运行。程序已内置 FFmpeg 9.0、ffprobe 和 yt-dlp；当前构建支持 Windows 10 或更高版本。

年龄限制或需要登录的视频，请点击“登录 YouTube（年龄限制视频）”，在程序打开的独立浏览器窗口中完成 YouTube 登录和年龄验证。Chrome、Edge、Firefox 或 Brave 登录成功后窗口会自动关闭；按钮显示“YouTube 已登录”后即可下载。程序会自动识别 Windows 默认浏览器；Cookie 只保存在本机的独立浏览器配置中，不会上传。

每次开始或重试下载时，程序都会重新读取当前 Windows 系统代理；关闭系统代理时自动直连，切换代理端口后无需重启程序。

## 从源码构建

将 `ffmpeg.exe`、`ffprobe.exe`、`yt-dlp.exe` 和 `my.ico` 放在项目目录，然后运行：

```powershell
pyinstaller yt_pro.spec
```

FFmpeg 9.0 Windows essentials build 来自 [GyanD/codexffmpeg](https://github.com/GyanD/codexffmpeg/releases/tag/9.0)，对应 FFmpeg 源码提交 [`d32b387f2b`](https://github.com/FFmpeg/FFmpeg/commit/d32b387f2b)。
