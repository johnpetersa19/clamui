"""Tests for the i18n (internationalization) module."""

import os
from unittest import mock


class TestGettext:
    """Test gettext translation functions."""

    def test_passthrough_without_translations(self):
        """_() returns the original string when no .mo file exists."""
        from src.core.i18n import _

        assert _("Hello") == "Hello"
        assert _("Scan Complete") == "Scan Complete"

    def test_ngettext_singular(self):
        """ngettext returns singular form for count=1."""
        from src.core.i18n import ngettext

        result = ngettext("{n} file", "{n} files", 1)
        assert result == "{n} file"

    def test_ngettext_plural(self):
        """ngettext returns plural form for count != 1."""
        from src.core.i18n import ngettext

        result = ngettext("{n} file", "{n} files", 0)
        assert result == "{n} files"

        result = ngettext("{n} file", "{n} files", 2)
        assert result == "{n} files"

        result = ngettext("{n} file", "{n} files", 100)
        assert result == "{n} files"

    def test_ngettext_with_format(self):
        """ngettext works correctly with .format()."""
        from src.core.i18n import ngettext

        result = ngettext("{n} file scanned", "{n} files scanned", 1).format(n=1)
        assert result == "1 file scanned"

        result = ngettext("{n} file scanned", "{n} files scanned", 5).format(n=5)
        assert result == "5 files scanned"

    def test_n_underscore_identity(self):
        """N_() returns the string unchanged (identity function)."""
        from src.core.i18n import N_

        assert N_("Scan") == "Scan"
        assert N_("Update") == "Update"
        assert N_("") == ""

    def test_n_underscore_does_not_translate(self):
        """N_() must not call gettext - it's an identity function for extraction only."""
        from src.core.i18n import N_

        # N_ should be a simple function that returns its argument
        text = "Test String"
        assert N_(text) is text  # Same object, not just equal

    def test_pgettext_available(self):
        """pgettext is importable and callable."""
        from src.core.i18n import pgettext

        # Without translations, pgettext returns the message (not the context)
        result = pgettext("menu", "File")
        assert result == "File"

    def test_format_string_pattern(self):
        """The recommended _().format() pattern works correctly."""
        from src.core.i18n import _

        count = 42
        result = _("Found {count} threats").format(count=count)
        assert result == "Found 42 threats"

    def test_underscore_is_callable(self):
        """_ is a callable function."""
        from src.core.i18n import _

        assert callable(_)

    def test_domain_is_clamui(self):
        """The gettext domain is 'clamui'."""
        from src.core.i18n import DOMAIN

        assert DOMAIN == "clamui"


class TestLocaleDirDetection:
    """Test locale directory detection for different runtime contexts."""

    def test_appimage_locale_dir(self, tmp_path):
        """Detects locale dir in AppImage context."""
        from src.core import i18n

        appdir = str(tmp_path / "AppDir")
        locale_dir = os.path.join(appdir, "usr", "share", "locale")
        os.makedirs(locale_dir)

        with mock.patch.dict(os.environ, {"APPDIR": appdir}):
            result = i18n._get_locale_dir()
            assert result == locale_dir

    def test_flatpak_locale_dir(self):
        """Detects locale dir in Flatpak context."""
        from src.core import i18n

        flatpak_locale = "/app/share/locale"

        with (
            mock.patch.dict(os.environ, {}, clear=False),
            mock.patch("os.path.exists") as mock_exists,
            mock.patch("os.path.isdir") as mock_isdir,
        ):
            # Remove APPDIR to skip AppImage check
            os.environ.pop("APPDIR", None)

            mock_exists.side_effect = lambda path: path == "/.flatpak-info"
            mock_isdir.side_effect = lambda path: path == flatpak_locale

            result = i18n._get_locale_dir()
            assert result == flatpak_locale

    def test_dev_locale_dir(self, tmp_path):
        """Detects locale dir in development context."""
        from src.core import i18n

        # Create a fake src/locale directory
        src_dir = tmp_path / "src"
        locale_dir = src_dir / "locale"
        locale_dir.mkdir(parents=True)

        with (
            mock.patch.dict(os.environ, {}, clear=False),
            mock.patch("os.path.exists", return_value=False),
            mock.patch(
                "os.path.dirname",
                side_effect=[
                    str(src_dir / "core"),  # First call: directory of i18n.py
                    str(src_dir),  # Second call: parent (src/)
                ],
            ),
            mock.patch("os.path.abspath", return_value=str(src_dir / "core" / "i18n.py")),
            mock.patch("os.path.isdir") as mock_isdir,
        ):
            os.environ.pop("APPDIR", None)

            def isdir_side_effect(path):
                return path == str(locale_dir)

            mock_isdir.side_effect = isdir_side_effect
            result = i18n._get_locale_dir()
            assert result == str(locale_dir)

    def test_system_locale_fallback(self):
        """Falls back to /usr/share/locale when available."""
        from src.core import i18n

        with (
            mock.patch.dict(os.environ, {}, clear=False),
            mock.patch("os.path.exists", return_value=False),
            mock.patch("os.path.isdir") as mock_isdir,
        ):
            os.environ.pop("APPDIR", None)

            def isdir_side_effect(path):
                return path == "/usr/share/locale"

            mock_isdir.side_effect = isdir_side_effect
            result = i18n._get_locale_dir()
            assert result == "/usr/share/locale"

    def test_returns_none_when_no_locale_dir(self):
        """Returns None when no locale directory is found."""
        from src.core import i18n

        with (
            mock.patch.dict(os.environ, {}, clear=False),
            mock.patch("os.path.exists", return_value=False),
            mock.patch("os.path.isdir", return_value=False),
        ):
            os.environ.pop("APPDIR", None)
            result = i18n._get_locale_dir()
            assert result is None
