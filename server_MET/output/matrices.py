"""Geração de matrizes CSV (variáveis e campo de vento) e matrizes BlueSky.

Cálculos de vento centralizados em WindProcessor; artefatos registrados
na tabela `outputs` do SQLite.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from server_MET.core.config import Settings
from server_MET.output.base import OutputGeneratorMixin
from server_MET.persistence.repositories import GridDataRepository
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region
from server_MET.processing.wind import WindProcessor

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Nome seguro para valores (sem acentos, espaços nem pontuação)."""
    import re
    import unicodedata

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


class MatrixGenerator(OutputGeneratorMixin):
    def __init__(
        self,
        processor: Optional[DataProcessor] = None,
        wind: Optional[WindProcessor] = None,
        grid_repo: Optional[GridDataRepository] = None,
    ) -> None:
        self.settings = Settings()
        self.processor = processor or DataProcessor()
        self.wind = wind or WindProcessor()
        self.grid_repo = grid_repo or GridDataRepository()
        super().__init__("matrix")

    def generate(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        output_dir: Optional[str] = None,
    ) -> list[str]:
        if var_name in ("wind", "winds"):
            files = self._generate_wind_matrices(
                var_name, region, level, date_str, analysis, output_dir
            )
        else:
            files = self._generate_variable_matrices(
                var_name, region, level, date_str, analysis, forecast_hours, output_dir
            )
        self._register_outputs(files, var_name, level, region, date_str, analysis)
        return files

    def _generate_variable_matrices(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        output_dir: Optional[str] = None,
    ) -> list[str]:
        grib_objs = self.processor.load_gribs(date_str, analysis, forecast_hours)
        if not grib_objs:
            logger.error("Nenhum dado GRIB carregado.")
            return []

        resolved_level = self.processor.resolve_level(var_name, level)
        var_msgs = self.processor.select_variable_from_gribs(
            grib_objs, var_name, resolved_level
        )

        if output_dir is None:
            output_dir = str(self.settings.dir_matrizes)

        saved_files = []
        lon_min, lon_max, lat_min, lat_max = region.bounds

        for msg in var_msgs:
            data, lat, lon = self.processor.extract_data(
                msg, lon_min, lon_max, lat_min, lat_max
            )
            data, _ = self.processor.convert_units(data, var_name)

            ft = msg.forecastTime
            ft_str = f"{ft:02d}"

            lon_grid, lat_grid = np.meshgrid(lon, lat)

            filename = (
                f"GFS_{msg.iDirectionIncrementInDegrees}_{region.name}_"
                f"N{resolved_level or level}_{var_name}_{msg.dataDate}_{ft_str}.csv"
            )
            filepath = f"{output_dir}/{filename}"

            table = np.column_stack(
                [lat_grid.ravel(), lon_grid.ravel(), data.ravel()]
            )
            np.savetxt(
                filepath, table, delimiter=",",
                header=f"lat,lon,{var_name}", comments="", fmt="%.6f",
            )

            saved_files.append(filepath)
            logger.info("Matriz salva: %s", filepath)

            try:
                self.grid_repo.delete_region(
                    var_name, region.name, msg.dataDate, analysis,
                    forecast=int(ft), level=resolved_level,
                )
                self.grid_repo.save_region(
                    variable=var_name,
                    region=region.name,
                    date_str=msg.dataDate,
                    analysis=analysis or "",
                    forecast=int(ft),
                    resolution=_slugify(str(msg.iDirectionIncrementInDegrees)),
                    level=resolved_level,
                    lat=lat,
                    lon=lon,
                    values=np.asarray(data),
                )
            except Exception as e:
                logger.warning("Falha ao persistir %s no SQLite: %s", var_name, e)

        return saved_files

    def _generate_wind_matrices(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> list[str]:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        if not grib_objs:
            return []

        base_var = "uSupe" if var_name == "winds" else "u"
        resolved_level = self.processor.resolve_level(base_var, level)
        u_msgs = self.processor.select_variable_from_gribs(grib_objs, base_var, resolved_level)
        v_msgs = self.processor.select_variable_from_gribs(
            grib_objs, "vSupe" if var_name == "winds" else "v", resolved_level
        )

        if output_dir is None:
            output_dir = str(self.settings.dir_matrizes)

        saved_files = []
        lon_min, lon_max, lat_min, lat_max = region.bounds

        for u_msg, v_msg in zip(u_msgs, v_msgs):
            data_u, lat_u, lon_u = self.processor.extract_data(
                u_msg, lon_min, lon_max, lat_min, lat_max
            )
            data_v, _, _ = self.processor.extract_data(
                v_msg, lon_min, lon_max, lat_min, lat_max
            )

            ft = u_msg.forecastTime
            ft_str = f"{ft:02d}"

            lon_grid, lat_grid = np.meshgrid(lon_u, lat_u)
            speed = self.wind.compute_speed(data_u, data_v)
            direction = self.wind.compute_direction_met(data_u, data_v)

            filename = (
                f"GFS_{u_msg.iDirectionIncrementInDegrees}_{region.name}_"
                f"N{resolved_level or level}_wind_{u_msg.dataDate}_{ft_str}.csv"
            )
            filepath = f"{output_dir}/{filename}"

            table = np.column_stack(
                [
                    lat_grid.ravel(),
                    lon_grid.ravel(),
                    data_u.ravel(),
                    data_v.ravel(),
                    speed.ravel(),
                    direction.ravel(),
                ]
            )
            np.savetxt(
                filepath, table, delimiter=",",
                header="lat,lon,vento_u,vento_v,velocidade,direcao",
                comments="", fmt="%.6f",
            )

            saved_files.append(filepath)
            logger.info("Matriz de vento salva: %s", filepath)

        return saved_files

    def generate_bluesky(
        self,
        region: Region,
        level: int,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> Optional[str]:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        if not grib_objs:
            return None

        resolved_level = self.processor.resolve_level("u", level)
        u_msgs = self.processor.select_variable_from_gribs(grib_objs, "u", resolved_level)
        v_msgs = self.processor.select_variable_from_gribs(grib_objs, "v", resolved_level)
        if not u_msgs or not v_msgs:
            return None

        output_dir = self.settings.dir_matrizes_bluesky

        lon_min, lon_max, lat_min, lat_max = region.bounds
        u_msg = u_msgs[0]
        v_msg = v_msgs[0]

        data_u, lat_u, lon_u = self.processor.extract_data(
            u_msg, lon_min, lon_max, lat_min, lat_max
        )
        data_v, _, _ = self.processor.extract_data(
            v_msg, lon_min, lon_max, lat_min, lat_max
        )

        lon_grid, lat_grid = np.meshgrid(lon_u, lat_u)
        speed_knot = self.wind.compute_speed_knot(data_u, data_v)
        direction = self.wind.compute_direction_met(data_u, data_v)
        h_alt = self.wind.pressure_to_altitude(resolved_level)

        filename = f"bluesky_wind_{region.name}_N{resolved_level}_{u_msg.dataDate}.csv"
        filepath = str(output_dir / filename)

        table = np.column_stack(
            [
                lat_grid.ravel(),
                lon_grid.ravel(),
                np.full_like(data_u.ravel(), h_alt),
                direction.ravel(),
                speed_knot.ravel(),
            ]
        )
        np.savetxt(
            filepath, table, delimiter=",",
            header="lat,lon,alt_ft,wind_dir_deg,wind_spd_kt",
            comments="", fmt="%.6f",
        )

        self._register_outputs(
            [filepath], "wind", resolved_level, region, date_str, analysis,
            kind="bluesky",
        )

        logger.info("Matriz BlueSky salva: %s", filepath)
        return filepath


__all__ = ["MatrixGenerator"]
