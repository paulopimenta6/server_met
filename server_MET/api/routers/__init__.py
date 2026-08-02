"""Router do servidor (agregado)."""
from server_MET.api.routers import (
    analysis,
    catalog,
    files,
    gribs,
    health,
    history,
    maps,
    matrices,
    metar,
)

__all__ = [
    "analysis",
    "catalog",
    "files",
    "gribs",
    "health",
    "history",
    "maps",
    "matrices",
    "metar",
]
