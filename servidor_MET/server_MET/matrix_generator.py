import csv
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from server_MET.config import Settings
from server_MET.data_processor import DataProcessor
from server_MET.region import Region

logger = logging.getLogger(__name__)


class MatrixGenerator:
    def __init__(self) -> None:
        self.settings = Settings()
        self.processor = DataProcessor()

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
            return self._generate_wind_matrices(
                var_name, region, level, date_str, analysis, output_dir
            )

        grib_objs = self.processor.load_gribs(date_str, analysis, forecast_hours)
        if not grib_objs:
            logger.error("No GRIB data loaded.")
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

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["lat", "lon", var_name])
                for i in range(data.shape[0]):
                    for j in range(data.shape[1]):
                        w.writerow([lat_grid[i, j], lon_grid[i, j], data[i, j]])

            saved_files.append(filepath)
            logger.info("Matrix saved: %s", filepath)

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

        resolved_level = self.processor.resolve_level("u", level)
        u_msgs = self.processor.select_variable_from_gribs(grib_objs, "u", resolved_level)
        v_msgs = self.processor.select_variable_from_gribs(grib_objs, "v", resolved_level)

        if output_dir is None:
            output_dir = str(self.settings.dir_matrizes)

        saved_files = []
        lon_min, lon_max, lat_min, lat_max = region.bounds

        for i, (u_msg, v_msg) in enumerate(zip(u_msgs, v_msgs)):
            data_u, lat_u, lon_u = self.processor.extract_data(
                u_msg, lon_min, lon_max, lat_min, lat_max
            )
            data_v, _, _ = self.processor.extract_data(
                v_msg, lon_min, lon_max, lat_min, lat_max
            )

            ft = u_msg.forecastTime
            ft_str = f"{ft:02d}"

            lon_grid, lat_grid = np.meshgrid(lon_u, lat_u)
            speed = np.sqrt(data_u**2 + data_v**2)
            direction = (180 / np.pi) * np.arctan2(-data_u, -data_v)

            filename = (
                f"GFS_{u_msg.iDirectionIncrementInDegrees}_{region.name}_"
                f"N{resolved_level or level}_wind_{u_msg.dataDate}_{ft_str}.csv"
            )
            filepath = f"{output_dir}/{filename}"

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["lat", "lon", "vento_u", "vento_v", "velocidade", "direcao"])
                for r in range(data_u.shape[0]):
                    for c in range(data_u.shape[1]):
                        w.writerow(
                            [
                                lat_grid[r, c],
                                lon_grid[r, c],
                                data_u[r, c],
                                data_v[r, c],
                                speed[r, c],
                                direction[r, c],
                            ]
                        )

            saved_files.append(filepath)
            logger.info("Wind matrix saved: %s", filepath)

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
        speed_knot = np.sqrt(data_u**2 + data_v**2) * 1.943
        direction = (180 / np.pi) * np.arctan2(-data_u, -data_v)
        h_alt = (1 - (resolved_level / 1013.25) ** 0.190284) * 145366.45

        filename = f"bluesky_wind_{region.name}_N{resolved_level}_{u_msg.dataDate}.csv"
        filepath = str(output_dir / filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["lat", "lon", "alt_ft", "wind_dir_deg", "wind_spd_kt"])
            for r in range(data_u.shape[0]):
                for c in range(data_u.shape[1]):
                    w.writerow(
                        [
                            lat_grid[r, c],
                            lon_grid[r, c],
                            h_alt,
                            direction[r, c],
                            speed_knot[r, c],
                        ]
                    )

        logger.info("Bluesky wind matrix saved: %s", filepath)
        return filepath
