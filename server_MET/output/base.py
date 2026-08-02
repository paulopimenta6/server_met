"""Base compartilhada dos geradores de saída (registro de artefatos no SQLite)."""
from __future__ import annotations

from typing import Optional

from server_MET.persistence.repositories import OutputRepository


class OutputGeneratorMixin:
    """Registra arquivos gerados na tabela `outputs` do banco SQLite."""

    def __init__(self, default_kind: str) -> None:
        self.output_repo = OutputRepository()
        self._default_kind = default_kind

    def _register_outputs(
        self,
        files: list[str],
        variable: Optional[str] = None,
        level: Optional[int] = None,
        region: object = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> None:
        kind = kind or self._default_kind
        region_name = getattr(region, "name", None)
        for f in files:
            forecast = None
            self.output_repo.register(
                kind=kind,
                file_path=f,
                variable=variable,
                level=level,
                region=region_name,
                date_str=date_str,
                analysis=analysis,
                forecast=forecast,
            )


__all__ = ["OutputGeneratorMixin"]
