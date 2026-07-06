from pathlib import Path

from scripts.check_folder_guides import REQUIRED_GUIDES, validate_folder_guides

ROOT = Path(__file__).resolve().parents[2]


def test_folder_guides_match_required_navigation_contract() -> None:
    assert validate_folder_guides(ROOT) == []


def test_make_lint_runs_folder_guide_check() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "$(MAKE) folder-guides" in makefile
    assert "python scripts/check_folder_guides.py" in makefile


def test_root_readme_links_first_slice_folder_guides() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for guide in REQUIRED_GUIDES:
        assert f"({guide.as_posix()})" in readme
