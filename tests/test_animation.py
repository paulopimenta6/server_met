"""Testes do gerador de animações GIF (offline, com PNGs sintéticos)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from server_MET.output.animation import AnimationGenerator, HAS_PILLOW
from server_MET.processing.regions import Region


def _make_frame(path: Path, color: tuple[int, int, int]) -> Path:
    img = Image.new("RGB", (64, 48), color)
    img.save(path)
    return path


class TestAnimationGenerator:
    def test_pillow_available(self):
        assert HAS_PILLOW is True

    def test_compose_gif_creates_valid_animation(self, tmp_path):
        frames = [
            _make_frame(tmp_path / f"f{i}.png", (i * 40, 60, 200))
            for i in (0, 1, 2, 3)
        ]
        gif_path = tmp_path / "anim_test.gif"
        gen = AnimationGenerator()
        gen._compose_gif(frames, gif_path, duration_ms=500, loop=0)
        assert gif_path.exists()
        with open(gif_path, "rb") as f:
            assert f.read(6) == b"GIF89a"
        with Image.open(gif_path) as img:
            assert getattr(img, "n_frames", 1) == 4

    def test_generate_without_grib_returns_none(self, isolated_db, tmp_path):
        gen = AnimationGenerator()
        result = gen.generate(
            "temp", Region(name="SP"), 500,
            "20990101", "06", output_dir=str(tmp_path),
        )
        assert result is None

    def test_slugify_filename(self):
        from server_MET.output.animation import _slugify

        assert _slugify("Cidade de São Paulo") == "Cidade_de_Sao_Paulo"
