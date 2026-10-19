"""PPTX → PDF (LibreOffice) → PNG (pdftoppm) für die Sichtprüfung."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PPTX_SKILL_SCRIPTS = Path("/mnt/skills/public/pptx/scripts")


def _run_soffice(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    if (PPTX_SKILL_SCRIPTS / "office" / "soffice.py").exists():
        if str(PPTX_SKILL_SCRIPTS) not in sys.path:
            sys.path.insert(0, str(PPTX_SKILL_SCRIPTS))
        from office.soffice import run_soffice  # LibreOffice-Wrapper des pptx-Skills

        return run_soffice(args, capture_output=True, text=True, timeout=timeout)
    profile = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    env = {**os.environ, "SAL_USE_VCLPLUGIN": "svp"}
    return subprocess.run(["soffice", f"-env:UserInstallation={profile.as_uri()}", *args],
                          capture_output=True, text=True, timeout=timeout, env=env)


def render_pdf(pptx: Path, outdir: Path, timeout: int = 240) -> Path:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    result = _run_soffice(["--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(pptx)], timeout)
    pdf = outdir / (Path(pptx).stem + ".pdf")
    if not pdf.exists():
        raise RuntimeError(f"PDF-Export fehlgeschlagen: {result.stdout} {result.stderr}")
    return pdf


def render_pngs(pdf: Path, outdir: Path, dpi: int = 80) -> list[Path]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = outdir / "slide"
    for old in outdir.glob("slide-*.png"):
        old.unlink()
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)], check=True)
    return sorted(outdir.glob("slide-*.png"))
