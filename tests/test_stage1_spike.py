"""Tests for Stage 1: pyflp round-trip on Python 3.11."""
import struct
import sys
from pathlib import Path

import pytest

from crystal_cook.compat import patch as _patch_pyflp
_patch_pyflp()

import pyflp
from crystal_cook.spike.stage1_pyflp_test import _build_minimal_flp


def test_python311_eventEnum_missing_works():
    """EventEnum._missing_ must handle any byte value 0-255 without raising."""
    from pyflp._events import EventEnum
    for i in range(256):
        result = EventEnum._missing_(i)
        assert result is not None, f"EventEnum._missing_({i}) returned None"
        assert int(result) == i


def test_minimal_flp_header():
    raw = _build_minimal_flp(bpm=140.0, fl_version="25.2.5")
    assert raw[:4] == b"FLhd"
    assert raw[14:18] == b"FLdt"
    events_size = int.from_bytes(raw[18:22], "little")
    assert len(raw) == events_size + 22


def test_minimal_flp_parse_roundtrip(tmp_path):
    raw = _build_minimal_flp(bpm=140.0, fl_version="25.2.5")
    src = tmp_path / "test.flp"
    src.write_bytes(raw)

    proj = pyflp.parse(src)
    assert proj.version.major == 25
    assert proj.tempo == pytest.approx(140.0, abs=0.1)
    assert proj.ppq == 96

    out = tmp_path / "test_roundtrip.flp"
    pyflp.save(proj, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_minimal_flp_contains_one_pattern(tmp_path):
    raw = _build_minimal_flp()
    src = tmp_path / "test.flp"
    src.write_bytes(raw)

    proj = pyflp.parse(src)
    patterns = list(proj.patterns)
    assert len(patterns) == 1, f"Expected 1 pattern, got {len(patterns)}"


def test_spike_output_exists_and_parses():
    """The pre-generated spike_output.flp committed to the repo must be parseable."""
    spike_flp = Path(__file__).parent.parent / "crystal_cook" / "spike" / "spike_output.flp"
    assert spike_flp.exists(), "spike_output.flp missing from repo"

    proj = pyflp.parse(spike_flp)
    assert proj.version.major is not None
    assert proj.tempo > 0
