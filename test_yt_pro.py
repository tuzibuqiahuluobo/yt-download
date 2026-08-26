import unittest
from unittest.mock import MagicMock, patch

import yt_pro


class ProxyDetectionTests(unittest.TestCase):
    def read_proxy(self, enabled, server):
        key = MagicMock()
        key.__enter__.return_value = key
        values = {"ProxyEnable": enabled, "ProxyServer": server}
        with (
            patch.object(yt_pro.winreg, "OpenKey", return_value=key),
            patch.object(
                yt_pro.winreg,
                "QueryValueEx",
                side_effect=lambda _key, name: (values[name], None),
            ),
        ):
            return yt_pro.get_windows_proxy_url()

    def test_reads_plain_windows_proxy(self):
        self.assertEqual(
            self.read_proxy(1, "127.0.0.1:7897"),
            "http://127.0.0.1:7897",
        )

    def test_prefers_https_from_protocol_map(self):
        self.assertEqual(
            self.read_proxy(1, "http=127.0.0.1:8080;https=127.0.0.1:8443"),
            "http://127.0.0.1:8443",
        )

    def test_disabled_proxy_means_direct_connection(self):
        self.assertEqual(self.read_proxy(0, "127.0.0.1:7897"), "")

    def test_recognizes_socks_connection_errors(self):
        app = object.__new__(yt_pro.YtDownloaderApp)
        app.proxy_error_detected = False
        app.auth_error_detected = False
        app.cookie_lock_error_detected = False
        app.handle_download_line("WARNING: SocksHTTPSConnection failed")
        self.assertTrue(app.proxy_error_detected)

    def test_recognizes_only_completed_login_titles(self):
        self.assertTrue(
            yt_pro.is_completed_login_title("订阅 - YouTube - 个人 - Microsoft Edge")
        )
        self.assertTrue(yt_pro.is_completed_login_title("Subscriptions - YouTube"))
        self.assertFalse(yt_pro.is_completed_login_title("登录 - Google 账号"))
        self.assertFalse(yt_pro.is_completed_login_title("YouTube - 个人 - Microsoft Edge"))

    def test_closes_new_browser_window_after_login(self):
        user32 = yt_pro.ctypes.windll.user32
        with (
            patch.object(yt_pro, "get_browser_window_handles", return_value={1, 2}),
            patch.object(
                yt_pro,
                "get_window_title",
                return_value="订阅 - YouTube - 个人 - Microsoft Edge",
            ),
            patch.object(user32, "IsWindow", side_effect=[True, False, False]),
            patch.object(user32, "PostMessageW", return_value=True) as close,
            patch.object(yt_pro.time, "sleep"),
        ):
            self.assertTrue(yt_pro.wait_for_youtube_login("msedge.exe", {1}))
        close.assert_called_once_with(2, 0x0010, 0, 0)

    def test_login_browser_uses_no_remote_debugging(self):
        app = object.__new__(yt_pro.YtDownloaderApp)
        app.after = MagicMock()
        with (
            patch.object(yt_pro, "get_browser_window_handles", return_value=set()),
            patch.object(yt_pro.subprocess, "Popen") as launch,
            patch.object(yt_pro, "wait_for_youtube_login", return_value=False),
        ):
            app.run_login_browser("edge", "msedge.exe", "profile")
        command = launch.call_args.args[0]
        self.assertIn("--new-window", command)
        self.assertFalse(any("remote-debugging" in arg for arg in command))


if __name__ == "__main__":
    unittest.main()
