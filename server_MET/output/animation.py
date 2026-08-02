"""Animação meteorológica: GIF com a sequência de previsões (f00...f18).

Cada quadro é um mapa gerado pelo `MapGenerator` para uma hora de previsão
do ciclo GFS; os quadros são combinados em um GIF animado com Pillow.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from server_MET.core.config import Settings
from server_MET.core.constants import FORECAST_HOURS
from server_MET.core.logging_conf import get_logger
from server_MET.output.base import OutputGeneratorMixin
from server_MET.output.maps import MapGenerator
from server_MET.processing.regions import Region

logger = get_logger(__name__)

try:
    from PIL import Image, ImageOps

    HAS_PILLOW = True
except ImportError:  # pragma: no cover
    HAS_PILLOW = False


class AnimationGenerator(OutputGeneratorMixin):
    """Gera GIF animado de uma variável sobre uma região ao longo das previsões."""

    def __init__(self, map_generator: Optional[MapGenerator] = None) -> None:
        self.settings = Settings()
        self.maps = map_generator or MapGenerator()
        super().__init__("gif")

    def generate(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        output_dir: Optional[str] = None,
        duration_ms: int = 700,
        loop: int = 0,
        dpi: int = 110,
        title: Optional[str] = None,
    ) -> Optional[str]:
        if not HAS_PILLOW:
            logger.error("GIF requer Pillow (pip install pillow).")
            return None

        forecast_hours = forecast_hours or list(FORECAST_HOURS)
        if output_dir is None:
            output_dir = str(self.settings.dir_tmp)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        frames: list[tuple[int, Path]] = []
        for fh in forecast_hours:
            frame_dir = out_dir / "frames"
            frame_dir.mkdir(parents=True, exist_ok=True)
            files = self.maps.generate(
                var_name=var_name,
                region=region,
                level=level,
                date_str=date_str,
                analysis=analysis,
                forecast_hours=[fh],
                output_dir=str(frame_dir),
                dpi=dpi,
                title=title,
            )
            if not files:
                logger.warning("Sem quadro para a previsão f%02s", int(fh))
                continue
            frames.append((int(fh), Path(files[0])))

        if not frames:
            logger.error("Nenhum quadro gerado para a animação.")
            return None

        frames.sort(key=lambda item: item[0])
        gif_path = out_dir / (
            f"anim_{_slugify(region.full_name)}_"
            f"{var_name}_N{level or 'sup'}_{date_str or 'semdata'}_{analysis or 'XX'}.gif"
        )
        self._compose_gif([f for _, f in frames], gif_path, duration_ms, loop)
        self._register_outputs([str(gif_path)], var_name, level, region, date_str, analysis)
        logger.info("GIF salvo: %s (%d quadros)", gif_path, len(frames))
        return str(gif_path)

    def _compose_gif(
        self, frame_paths: list[Path], gif_path: Path, duration_ms: int, loop: int
    ) -> None:
        images = []
        for path in frame_paths:
            img = Image.open(path).convert("RGB")
            images.append(img)
        base = images[0]
        if any(img.size != base.size for img in images[1:]):
            images = [ImageOps.contain(img, base.size) for img in images]
        base.save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=duration_ms,
            loop=loop,
            optimize=True,
        )
        for img in images:
            img.close()


def _slugify(text: str) -> str:
    """Nome seguro para arquivo: sem acentos, espaços nem pontuação."""
    import re
    import unicodedata

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("_")


__all__ = ["AnimationGenerator", "HAS_PILLOW"]
