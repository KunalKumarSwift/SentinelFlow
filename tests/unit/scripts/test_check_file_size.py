"""Tests for the CI file-size guard."""

from pathlib import Path

import pytest

from scripts.check_file_size import find_oversized, main


def _write_lines(path: Path, count: int) -> Path:
    path.write_text("x = 1\n" * count)
    return path


def test_find_oversized_allows_file_at_limit(tmp_path: Path) -> None:
    _write_lines(tmp_path / "ok.py", 120)
    assert find_oversized([tmp_path], max_lines=120) == []


def test_find_oversized_reports_file_over_limit(tmp_path: Path) -> None:
    big = _write_lines(tmp_path / "big.py", 121)
    assert find_oversized([tmp_path], max_lines=120) == [(big, 121)]


def test_find_oversized_ignores_non_python_files(tmp_path: Path) -> None:
    _write_lines(tmp_path / "notes.md", 500)
    assert find_oversized([tmp_path], max_lines=120) == []


def test_find_oversized_searches_subdirectories(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    big = _write_lines(tmp_path / "pkg" / "big.py", 200)
    assert find_oversized([tmp_path], max_lines=120) == [(big, 200)]


def test_main_returns_zero_when_all_files_fit(tmp_path: Path) -> None:
    _write_lines(tmp_path / "ok.py", 10)
    assert main(["--max", "120", str(tmp_path)]) == 0


def test_main_returns_one_and_names_offender(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_lines(tmp_path / "big.py", 121)
    assert main(["--max", "120", str(tmp_path)]) == 1
    assert "big.py: 121 lines" in capsys.readouterr().out
