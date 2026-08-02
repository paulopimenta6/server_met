"""Servir artefatos gerados (PNG/CSV) via HTTP com proteção contra path traversal."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from server_MET.api.dependencies import resolve_path, safe_join

router = APIRouter(tags=["files"])


@router.get("/files/{kind}/{file_path:path}")
async def get_artifact(kind: str, file_path: str):
    """Baixa um artefato gerado (mapas, matrizes, bluesky, analise, tmp).

    `kind` restringe o diretório raiz e `file_path` é validado para não
    escapar dele (anti path traversal).
    """
    base = resolve_path(kind)
    target = safe_join(base, file_path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(
        target,
        filename=target.name,
        media_type=_guess_media_type(target.suffix),
    )


def _guess_media_type(suffix: str) -> str:
    return {
        ".png": "image/png",
        ".csv": "text/csv",
        ".json": "application/json",
        ".txt": "text/plain",
    }.get(suffix, "application/octet-stream")


__all__ = ["router"]
