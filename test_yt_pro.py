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

    def test_recognizes_only_the_youtube_login_callback(self):
        valid = [{"url": "https://www.youtube.com/robots.txt", "id": "1"}]
        lookalike = [{"url": "https://www.youtube.com.example/robots.txt", "id": "2"}]
        self.assertEqual(yt_pro.find_completed_login_page(valid)["id"], "1")
        self.assertIsNone(yt_pro.find_completed_login_page(lookalike))

    def test_closes_browser_after_login_callback(self):
        process = MagicMock()
        process.poll.return_value = None
        pages = [
            {
                "url": "https://www.youtube.com/robots.txt",
                "id": "login-page",
                "type": "page",
            }
        ]
        with (
            patch.object(yt_pro, "get_devtools_pages", return_value=(9222, pages)),
            patch.object(yt_pro, "close_devtools_pages", return_value=True) as close,
        ):
            self.assertTrue(yt_pro.wait_for_youtube_login(process, "profile"))
        close.assert_called_once_with(9222, pages)
        process.wait.assert_called_once_with(timeout=10)


if __name__ == "__main__":
    unittest.main()
