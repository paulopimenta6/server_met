"""Exportação das estatísticas descritivas para CSV (dir_analise).

Complementa a persistência na tabela `statistics`: cada hora de previsão vira
uma linha do CSV, disponibilizado pela API REST em `/files/analise/...`.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from server_MET.core.config import Settings
from server_MET.output.base import OutputGeneratorMixin
from server_MET.processing.regions import Region

STAT_COLUMNS = [
    "variable", "level", "region", "date", "analysis", "forecast", "units",
    "n_points", "n_missing", "min", "max", "mean", "median", "std", "iqr",
    "p1", "p5", "p25", "p50", "p75", "p95", "p99", "skewness", "kurtosis",
]


def _slugify(text: str) -> str:
    """Nome seguro para arquivo: sem acentos, espaços nem pontuação."""
    import re
    import unicodedata

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("_")


class StatisticsCSVGenerator(OutputGeneratorMixin):
    """Grava resumo estatístico por hora de previsão em um arquivo CSV."""

    def __init__(self) -> None:
        self.settings = Settings()
        super().__init__("statistics")

    def generate(
        self,
        rows: list[dict],
        region: Region,
        variable: str,
        level: Optional[int],
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> Optional[str]:
        """Escreve `estatisticas_...csv` em `data/analise` e registra a saída."""
        if not rows:
            return None
        output_dir = self.settings.dir_analise
        output_dir.mkdir(parents=True, exist_ok=True)

        region_slug = _slugify(region.full_name)
        level_slug = f"N{level}" if level else "sup"
        date_slug = date_str or rows[0].get("date") or "semdata"
        ana_slug = analysis or rows[0].get("analysis") or "XX"

        filename = (
            f"estatisticas_{variable}_{region_slug}_{level_slug}_"
            f"{date_slug}_{ana_slug}.csv"
        )
        filepath = output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=STAT_COLUMNS)
            writer.writeheader()
            for r in rows:
                writer.writerow(
                    {
                        "variable": r.get("variable", variable),
                        "level": r.get("level", level),
                        "region": r.get("region", region.name),
                        "date": r.get("date", date_str),
                        "analysis": r.get("analysis", analysis),
                        **{c: r.get(c) for c in STAT_COLUMNS[5:]},
                    }
                )

        self._register_outputs(
            [str(filepath)],
            variable=variable,
            level=level,
            region=region,
            date_str=date_str,
            analysis=analysis,
            kind="statistics",
        )
        return str(filepath)


__all__ = ["StatisticsCSVGenerator", "STAT_COLUMNS"]
