"""Servidor Meteorológico MET — captação, tratamento, análise e distribuição de dados GFS.

Pipeline: acquisition (captação) -> processing (tratamento) -> analysis (análise)
        -> persistence (persistência SQLite) -> output (resultados) -> api (servidor).
"""

__version__ = "3.0.0"

from server_MET.core.config import Settings
from server_MET.acquisition.grib_reader import GribReader
from server_MET.acquisition.grib_downloader import GribDownloader
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region, REGIOES_PREDEFINIDAS
from server_MET.output.maps import MapGenerator
from server_MET.output.matrices import MatrixGenerator
from server_MET.processing.wind import WindProcessor
from server_MET.acquisition.metar_client import MetarClient
from server_MET.persistence.database import Database, get_database

__all__ = [
    "Settings",
    "GribReader",
    "GribDownloader",
    "DataProcessor",
    "Region",
    "REGIOES_PREDEFINIDAS",
    "MapGenerator",
    "MatrixGenerator",
    "WindProcessor",
    "MetarClient",
    "Database",
    "get_database",
    "__version__",
]
