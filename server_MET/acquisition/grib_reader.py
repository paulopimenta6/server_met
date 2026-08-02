"""Leitura de arquivos GRIB2 com pygrib."""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pygrib

from server_MET.core.config import Settings
from server_MET.core.constants import RESOLUTIONS

logger = logging.getLogger(__name__)


class GribReader:
    def __init__(self) -> None:
        self.settings = Settings()
        self._healthy_cache: dict[str, bool] = {}

    def find_grib_file(
        self,
        date_str: str,
        analysis: str,
        forecast: str,
        resolution: Optional[str] = None,
    ) -> Optional[Path]:
        base_dir = self.settings.dir_gribs / date_str / analysis
        if not base_dir.exists():
            logger.warning("Diretório não encontrado: %s", base_dir)
            return None

        resolutions = [resolution] if resolution else RESOLUTIONS
        for res in resolutions:
            for f in base_dir.iterdir():
                if f.is_file() and f.name.endswith(f".f0{forecast}") and res in f.name:
                    logger.info("Arquivo GRIB encontrado: %s", f)
                    return f
        logger.warning("Nenhum arquivo GRIB para %s %s f%02s", date_str, analysis, int(forecast))
        return None

    def find_available_analyses(self, date_str: str) -> list[str]:
        base_dir = self.settings.dir_gribs / date_str
        if not base_dir.exists():
            return []
        return sorted(d.name for d in base_dir.iterdir() if d.is_dir())

    def is_healthy(self, filepath: Path, timeout: int = 90) -> bool:
        """Valida um GRIB em subprocesso (timeout), com cache por caminho.

        pygrib/eccodes podem travar em loop infinito ao ler arquivos
        corrompidos; a validação em subprocesso permite abortar e descartar
        o arquivo antes que trave o pipeline no processo principal.
        """
        key = str(filepath)
        if key in self._healthy_cache:
            return self._healthy_cache[key]
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
            ok = result.returncode == 0 and b"OK" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error("Validação GRIB falhou para %s: %s", filepath, e)
            ok = False
        self._healthy_cache[key] = ok
        if not ok:
            logger.warning("Arquivo GRIB corrompido: %s", filepath)
        return ok

    def filter_healthy(self, files: list[Path]) -> list[Path]:
        """Mantém apenas GRIBs válidos, removendo corrompidos do pipeline."""
        return [f for f in files if self.is_healthy(f)]

    def _run_list_script(self, script: str, filepath: Path, timeout: int = 120) -> list[str]:
        try:
            result = subprocess.run(
                [sys.executable, "-c", script, str(filepath)],
                capture_output=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                logger.warning(
                    "Descoberta GRIB falhou para %s: %s",
                    filepath, result.stderr.decode(errors="replace").strip(),
                )
                return []
            return [
                line for line in result.stdout.decode(errors="replace").splitlines()
                if line.strip()
            ]
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error("Descoberta GRIB falhou para %s: %s", filepath, e)
            return []

    def available_levels(
        self,
        date_str: str,
        analysis: str,
        forecast: str,
        resolution: Optional[str] = None,
    ) -> list[int]:
        """Níveis isobáricos (hPa) disponíveis num GRIB, via subprocesso.

        Evita abrir o arquivo no processo principal (proteção contra arquivo
        corrompido). Retorna lista vazia se nada for encontrado.
        """
        filepath = self.find_grib_file(date_str, analysis, forecast, resolution)
        if filepath is None or not filepath.exists():
            return []
        script = (
            "import sys, pygrib\n"
            "g = pygrib.open(sys.argv[1])\n"
            "for grb in g:\n"
            "    if grb.typeOfLevel in ('isobaricInhPa', 'isobaricInPa'):\n"
            "        print(int(grb.level))\n"
        )
        lines = self._run_list_script(script, filepath)
        levels = []
        seen: set[int] = set()
        for line in lines:
            try:
                lvl = int(line)
            except ValueError:
                continue
            if lvl not in seen:
                seen.add(lvl)
                levels.append(lvl)
        return sorted(levels)

    def available_variables(
        self,
        date_str: str,
        analysis: str,
        forecast: str,
        resolution: Optional[str] = None,
    ) -> list[dict]:
        """Nome + tipo de nível das mensagens presentes num GRIB, via subprocesso."""
        filepath = self.find_grib_file(date_str, analysis, forecast, resolution)
        if filepath is None or not filepath.exists():
            return []
        script = (
            "import sys, pygrib, json\n"
            "g = pygrib.open(sys.argv[1])\n"
            "out = []\n"
            "for grb in g:\n"
            "    out.append([grb.name, grb.typeOfLevel, int(grb.level)])\n"
            "print(json.dumps(out))\n"
        )
        lines = self._run_list_script(script, filepath)
        if not lines:
            return []
        import json

        try:
            raw = json.loads(lines[-1])
        except (json.JSONDecodeError, IndexError):
            return []
        result = []
        for name, level_type, lvl in raw:
            result.append({"name": name, "type_of_level": level_type, "level": lvl})
        return result

    def find_available_resolutions(self, date_str: str, analysis: str) -> list[str]:
        base_dir = self.settings.dir_gribs / date_str / analysis
        if not base_dir.exists():
            return []
        found: set[str] = set()
        for f in base_dir.iterdir():
            if not f.is_file():
                continue
            for res in RESOLUTIONS:
                if res in f.name:
                    found.add(res)
        return sorted(found)

    def find_all_grib_files(
        self,
        date_str: str,
        analysis: str,
        forecast_hours: Optional[list[str]] = None,
    ) -> list[Path]:
        if forecast_hours is None:
            forecast_hours = self.settings.forecast_hours
        files = []
        for fh in forecast_hours:
            f = self.find_grib_file(date_str, analysis, fh)
            if f:
                files.append(f)
        return files

    def open_grib(self, filepath: Path) -> Optional[pygrib.gribmessage]:
        try:
            return pygrib.open(str(filepath))
        except (OSError, ValueError) as e:
            logger.error("Falha ao abrir GRIB %s: %s", filepath, e)
            return None

    def select_variable(
        self,
        grb: pygrib.gribmessage,
        name: str,
        type_of_level: str,
        level: Optional[int] = None,
    ) -> list:
        try:
            if level is not None:
                return grb.select(name=name, typeOfLevel=type_of_level, level=level)
            return grb.select(name=name, typeOfLevel=type_of_level)
        except (ValueError, KeyError) as e:
            logger.warning("Variável não encontrada: %s em %s/%s (%s)", name, type_of_level, level, e)
            return []

    def list_variables(self, filepath: Path) -> list[dict]:
        grb = self.open_grib(filepath)
        if grb is None:
            return []
        variables = []
        try:
            for g in grb:
                variables.append(
                    {
                        "name": g.name,
                        "type_of_level": g.typeOfLevel,
                        "level": g.level,
                        "units": g.units,
                        "forecast_time": g.forecastTime,
                        "data_date": g.dataDate,
                    }
                )
        finally:
            grb.close()
        return variables


__all__ = ["GribReader"]