"""
Tests for convert.py — no external tools (LibreOffice, Chrome, pdf2docx) required.

Run from the project root:
  python -m pytest tests/
  # or without pytest:
  python tests/test_convert.py
"""
import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Load the module without executing main() ──────────────────────────────────
# convert.py lives in scripts/ (deployed copy at ~/.doc-converter/convert.py).
# We load the source directly so tests always run against the repo version.
_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "convert.py")
_SCRIPT = os.path.abspath(_SCRIPT)

spec = importlib.util.spec_from_file_location("convert", _SCRIPT)
convert = importlib.util.module_from_spec(spec)
sys.modules["convert"] = convert          # required by Python 3.14 dataclass machinery
spec.loader.exec_module(convert)  # type: ignore[union-attr]


# ── ConversionResult ──────────────────────────────────────────────────────────

class TestConversionResult(unittest.TestCase):
    def test_succeeded_when_no_error(self):
        r = convert.ConversionResult("/a/b.docx", output_path="/a/b.pdf")
        self.assertTrue(r.succeeded)

    def test_failed_when_error_set(self):
        r = convert.ConversionResult("/a/b.docx", error="something went wrong")
        self.assertFalse(r.succeeded)

    def test_default_output_is_none(self):
        r = convert.ConversionResult("/a/b.docx")
        self.assertIsNone(r.output_path)


# ── MESSAGES catalog completeness ─────────────────────────────────────────────

class TestMessageCatalog(unittest.TestCase):
    """All MESSAGES values must be (str, str) tuples with valid format fields."""

    def test_all_entries_are_two_tuples(self):
        for key, value in convert.MESSAGES.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, tuple)
                self.assertEqual(len(value), 2, f"{key}: expected (title, body) pair")
                self.assertIsInstance(value[0], str)
                self.assertIsInstance(value[1], str)

    def test_no_hardcoded_english_outside_catalog(self):
        """Regression guard: the catalog must contain every key dispatch_conversion references."""
        required_keys = {
            "converting_single", "converting_batch",
            "success_single", "success_batch",
            "partial_success", "failure",
            "no_converter", "textutil_failed", "chrome_failed",
            "package_missing", "nothing_to_convert",
        }
        missing = required_keys - set(convert.MESSAGES.keys())
        self.assertFalse(missing, f"Keys missing from MESSAGES catalog: {missing}")


# ── MODE_CONFIG ───────────────────────────────────────────────────────────────

class TestModeConfig(unittest.TestCase):
    def test_to_pdf_exts(self):
        exts = convert._MODE_CONFIG["to_pdf"]["exts"]
        self.assertIn(".docx", exts)
        self.assertIn(".doc", exts)

    def test_to_docx_exts(self):
        exts = convert._MODE_CONFIG["to_docx"]["exts"]
        self.assertIn(".pdf", exts)

    def test_to_pdf_pkg_is_none(self):
        """to_pdf no longer uses a pip package — pkg should be None."""
        self.assertIsNone(convert._MODE_CONFIG["to_pdf"]["pkg"])

    def test_to_docx_pkg(self):
        self.assertEqual(convert._MODE_CONFIG["to_docx"]["pkg"], "pdf2docx")


# ── dispatch_conversion — nothing_to_convert ──────────────────────────────────

class TestDispatchNothingToConvert(unittest.TestCase):
    def test_no_valid_files_sends_nothing_to_convert(self):
        notifications = []

        def fake_notify(key, *, sound=True, **fields):
            notifications.append((key, fields))

        with patch.object(convert, "post_notification", fake_notify):
            convert.dispatch_conversion("to_pdf", ["/a/b.pdf", "/c/d.txt"])

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0][0], "nothing_to_convert")

    def test_empty_file_list_sends_nothing_to_convert(self):
        notifications = []

        def fake_notify(key, *, sound=True, **fields):
            notifications.append((key, fields))

        with patch.object(convert, "post_notification", fake_notify):
            convert.dispatch_conversion("to_docx", [])

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0][0], "nothing_to_convert")


# ── dispatch_conversion — sentinel routing ────────────────────────────────────

class TestDispatchSentinels(unittest.TestCase):
    def _run(self, sentinel: str, mode: str = "to_pdf") -> list:
        notifications = []

        def fake_notify(key, *, sound=True, **fields):
            notifications.append((key, fields))

        def fake_convert(_path):
            return convert.ConversionResult(_path, error=sentinel)

        original = convert._MODE_CONFIG[mode]["converter"]
        convert._MODE_CONFIG[mode]["converter"] = fake_convert
        try:
            with patch.object(convert, "post_notification", fake_notify):
                ext = convert._MODE_CONFIG[mode]["exts"][0]
                convert.dispatch_conversion(mode, [f"/tmp/file{ext}"])
        finally:
            convert._MODE_CONFIG[mode]["converter"] = original

        return notifications

    def test_pkg_missing_sentinel(self):
        notes = self._run("__pkg_missing__", "to_docx")
        keys = [n[0] for n in notes]
        self.assertIn("package_missing", keys)

    def test_no_converter_sentinel(self):
        notes = self._run("__no_converter__", "to_pdf")
        keys = [n[0] for n in notes]
        self.assertIn("no_converter", keys)

    def test_textutil_failed_sentinel(self):
        notes = self._run("__textutil_failed__file not found", "to_pdf")
        keys = [n[0] for n in notes]
        self.assertIn("textutil_failed", keys)

    def test_chrome_failed_sentinel(self):
        notes = self._run("__chrome_failed__exit code 1", "to_pdf")
        keys = [n[0] for n in notes]
        self.assertIn("chrome_failed", keys)


# ── find_chrome ───────────────────────────────────────────────────────────────

class TestFindChrome(unittest.TestCase):
    def test_returns_none_when_no_chrome(self):
        with patch("os.path.exists", return_value=False):
            result = convert._find_chrome()
        self.assertIsNone(result)

    def test_returns_first_existing_candidate(self):
        first = convert._CHROME_CANDIDATES[0]

        def fake_exists(path):
            return path == first

        with patch("os.path.exists", fake_exists):
            result = convert._find_chrome()
        self.assertEqual(result, first)


# ── post_notification ─────────────────────────────────────────────────────────

class TestPostNotification(unittest.TestCase):
    def test_calls_osascript(self):
        with patch("subprocess.run") as mock_run:
            convert.post_notification("success_single", fmt="PDF", name="report.pdf")
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            self.assertEqual(cmd[0], "osascript")

    def test_quotes_escaped(self):
        """Double-quotes in filenames must not break the osascript invocation."""
        with patch("subprocess.run") as mock_run:
            convert.post_notification("success_single", fmt="PDF", name='file"with"quotes.pdf')
            script_arg = mock_run.call_args[0][0][-1]
            # The notification body should use single quotes instead
            self.assertNotIn('"file"with"quotes.pdf"', script_arg)


if __name__ == "__main__":
    unittest.main()
