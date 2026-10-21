import subprocess

from conftest import REPO


def test_licensed_font_is_never_tracked():
    """Corporate S ist lizenziert: Git ignoriert sie in jedem Ordner, auch im Skill-Paket und auf der Seite."""
    for path in ("fonts/CorporateS-Regular.otf",
                 "skill/flaesh-campus/assets/fonts/CorporateS-Regular.otf",
                 "site/assets/fonts/CorporateS-Bold.otf"):
        assert subprocess.run(["git", "check-ignore", "-q", path], cwd=REPO).returncode == 0, path
