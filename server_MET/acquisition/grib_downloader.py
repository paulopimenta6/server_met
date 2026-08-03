"""Download de arquivos GFS GRIB2 do NOMADS (NOAA) + limpeza de dados antigos.

Registra cada arquivo no banco SQLite (tabela `downloads`).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from server_MET.core.config import Settings
from server_MET.core.constants import ANALYSIS_HOURS, RESOLUTIONS
from server_MET.core.logging_conf import get_logger
from server_MET.persistence.repositories import DownloadRepository

logger = get_logger(__name__)


def get_date_str(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y%m%d")


def get_current_analysis_hour() -> str:
    """Hora de análise GFS mais próxima (00/06/12/18) baseada no horário atual."""
    h = datetime.now().hour
    if h < 6:
        return "00"
    if h < 12:
        return "06"
    if h < 18:
        return "12"
    return "18"


class GribDownloader:
    def __init__(self, repositories: Optional[DownloadRepository] = None) -> None:
        self.settings = Settings()
        self.repo = repositories or DownloadRepository()

    def check_url_exists(self, url: str) -> bool:
        try:
            result = subprocess.run(
                ["wget", "--spider", "--quiet", url],
                capture_output=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("wget indisponível ou timeout ao verificar URL: %s", url)
            return False

    def download_file(self, url: str, dest_path: Path, timeout: int = 300) -> bool:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                ["wget", "-O", str(dest_path), url],
                capture_output=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                logger.info("Baixado: %s -> %s", url, dest_path)
                return True
            logger.error("Falha ao baixar %s: %s", url, result.stderr.decode(errors="replace"))
            return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout ao baixar %s", url)
            return False
        except FileNotFoundError:
            logger.error("wget não encontrado. Instale wget ou use curl.")
            return False

    def validate_grib(self, filepath: Path, timeout: int = 90) -> bool:
        """Valida um arquivo GRIB em subprocesso (com timeout).

        pygrib/eccodes podem travar em loop infinito ao ler arquivos
        corrompidos (download interrompido etc.); a validação em subprocesso
        permite abortar e descartar o arquivo antes que trave o pipeline.
        """
        script = (
            "import sys, pygrib\n"
            "g = pygrib.open(sys.argv[1])\n"
            "sel = g.select(name='Temperature', typeOfLevel='isobaricInhPa', level=500)\n"
            "if not sel:\n"
            "    sys.exit(2)\n"
            "sel[0].values\n"
            "print('OK')\n"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-c", script, str(filepath)],
                capture_output=True,
                timeout=timeout,
            )
            return result.returncode == 0 and b"OK" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error("Validação GRIB falhou para %s: %s", filepath, e)
            return False

    def download_gribs(
        self,
        date_str: Optional[str] = None,
        analysis_hour: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        resolution: str = "0p25",
        force: bool = False,
    ) -> list[Path]:
        date_str = date_str or get_date_str()
        analysis_hour = analysis_hour or get_current_analysis_hour()

        # Horas de previsão padrão: 00, 06, 12, 18 (Settings.forecast_hours).
        forecast_hours = forecast_hours or list(self.settings.forecast_hours)

        downloaded = []
        base_url = f"{self.settings.gfs_url}{date_str}/{analysis_hour}/atmos/"
        dest_dir = self.settings.dir_gribs / date_str / analysis_hour
        dest_dir.mkdir(parents=True, exist_ok=True)

        for fh in forecast_hours:
            filename = f"gfs.t{analysis_hour}z.pgrb2.{resolution}.f0{fh}"
            filepath = dest_dir / filename

            self.repo.register(date_str, analysis_hour, resolution, fh, filepath)

            if filepath.exists() and not force:
                record = self.repo.get(date_str, analysis_hour, resolution, fh)
                already_validated = bool(
                    record
                    and record.get("status") == "downloaded"
                    and filepath.stat().st_size > 0
                )
                if already_validated:
                    logger.info("Arquivo já existe e foi validado: %s", filepath)
                    self.repo.mark(date_str, analysis_hour, resolution, fh, "skipped",
                                   file_size=filepath.stat().st_size)
                    downloaded.append(filepath)
                    continue
                if self.validate_grib(filepath):
                    logger.info("Arquivo existente validado: %s", filepath)
                    self.repo.mark(date_str, analysis_hour, resolution, fh, "downloaded",
                                   file_size=filepath.stat().st_size)
                    downloaded.append(filepath)
                    continue
                logger.error(
                    "Arquivo existente corrompido/parcial (%s); removendo para re-download.",
                    filepath,
                )
                try:
                    filepath.unlink(missing_ok=True)
                except OSError as e:
                    logger.error("Não foi possível remover %s: %s", filepath, e)
                self.repo.mark(
                    date_str, analysis_hour, resolution, fh, "failed",
                    error="arquivo existente corrompido",
                )

            url = f"{base_url}{filename}"
            logger.info("Verificando URL: %s", url)

            if not self.check_url_exists(url):
                logger.warning("URL não disponível: %s", url)
                self.repo.mark(date_str, analysis_hour, resolution, fh, "failed",
                               error="URL não disponível")
                continue

            if self.download_file(url, filepath):
                if not self.validate_grib(filepath):
                    logger.error(
                        "Arquivo GRIB corrompido (%s); removendo para novo download.",
                        filepath,
                    )
                    try:
                        filepath.unlink(missing_ok=True)
                    except OSError as e:
                        logger.error("Não foi possível remover %s: %s", filepath, e)
                    self.repo.mark(
                        date_str, analysis_hour, resolution, fh, "failed",
                        error="arquivo corrompido",
                    )
                    continue
                self.repo.mark(date_str, analysis_hour, resolution, fh, "downloaded",
                               file_size=filepath.stat().st_size)
                downloaded.append(filepath)
            else:
                self.repo.mark(date_str, analysis_hour, resolution, fh, "failed")

        return downloaded

    def download_gribs_all_resolutions(
        self,
        date_str: Optional[str] = None,
        analysis_hour: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        resolutions: Optional[list[str]] = None,
        force: bool = False,
    ) -> dict[str, list[Path]]:
        results = {}
        for res in resolutions or RESOLUTIONS:
            files = self.download_gribs(
                date_str=date_str,
                analysis_hour=analysis_hour,
                forecast_hours=forecast_hours,
                resolution=res,
                force=force,
            )
            if files:
                results[res] = files
        return results

    def clean_old_data(self, days_old: int = 2) -> int:
        removed = 0
        cutoff = datetime.now() - timedelta(days=days_old)

        for data_dir in (
            self.settings.dir_gribs,
            self.settings.dir_mapas,
            self.settings.dir_matrizes,
            self.settings.dir_analise,
        ):
            for date_dir in data_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y%m%d")
                except ValueError:
                    continue
                if dir_date < cutoff:
                    for ana_dir in date_dir.iterdir():
                        if ana_dir.is_dir():
                            for f in ana_dir.iterdir():
                                if f.is_file():
                                    f.unlink(missing_ok=True)
                                    removed += 1
                            ana_dir.rmdir()
                    date_dir.rmdir()
                    logger.info("Diretório antigo removido: %s", date_dir)

        removed += self._clean_old_tmp_dir(cutoff)
        return removed

    def clean_old_tmp(self, days_old: int = 2) -> int:
        """Remove subpastas `data/tmp/<uuid>` mais antigas que N dias."""
        cutoff = datetime.now() - timedelta(days=days_old)
        return self._clean_old_tmp_dir(cutoff)

    def _clean_old_tmp_dir(self, cutoff: datetime) -> int:
        removed = 0
        tmp_dir = self.settings.dir_tmp
        if not tmp_dir.is_dir():
            return removed
        for d in tmp_dir.iterdir():
            if not d.is_dir():
                continue
            try:
                mtime = datetime.fromtimestamp(d.stat().st_mtime)
            except OSError:
                continue
            if mtime < cutoff:
                removed += sum(1 for _ in d.rglob("*") if _.is_file())
                shutil.rmtree(d, ignore_errors=True)
                logger.info("Diretório temporário antigo removido: %s", d)
        return removed

    def clean_old_gribs(self, days_old: int = 2) -> int:
        return self.clean_old_data(days_old=days_old)


__all__ = ["GribDownloader", "get_date_str", "get_current_analysis_hour"]
