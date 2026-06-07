"""Environment and config smoke tests."""

from config import ROOT_DIR, SCOPES


def test_project_paths_exist():
    assert ROOT_DIR.is_dir()
    assert (ROOT_DIR / "streamlit_app.py").exists()


def test_scopes_exclude_forbidden_endpoints():
    assert "user-top-read" in SCOPES
    assert "audio-features" not in SCOPES


def test_env_file_exists():
    assert (ROOT_DIR / ".env").exists() or (ROOT_DIR / ".env.example").exists()
