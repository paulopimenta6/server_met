import logging
from typing import Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib import rc
import matplotlib.pyplot as plt

from server_MET.config import Settings
from server_MET.data_processor import DataProcessor, VAR_MAP
from server_MET.region import Region

logger = logging.getLogger(__name__)

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False

try:
    from mpl_toolkits.basemap import Basemap

    HAS_BASEMAP = True
except ImportError:
    HAS_BASEMAP = False

HAS_MAP_BACKEND = HAS_CARTOPY or HAS_BASEMAP

if not HAS_MAP_BACKEND:
    logger.warning(
        "Neither Cartopy nor Basemap installed. Map generation disabled."
    )


class MapGenerator:
    def __init__(self) -> None:
        self.settings = Settings()
        self.processor = DataProcessor()

    def _compute_intervals(self, data: np.ndarray) -> np.ndarray:
        min_var = float(data.min()) - 1
        max_var = float(data.max()) + 1
        n = len(data.flatten())
        if n <= 50:
            o = 30
        elif n <= 100:
            o = 50
        elif n <= 500:
            o = 70
        elif n <= 1000:
            o = 90
        elif n <= 10000:
            o = 110
        else:
            o = 500
        return np.linspace(int(min_var), int(max_var), o)

    def _get_unit_label(self, var_name: str) -> str:
        unit_map = {
            "temp": "°C",
            "temps": "°C",
            "ps": "hPa",
            "prnm": "hPa",
            "nuvem": "%",
            "umidadeRel": "%",
            "chuvaNaoConvec": "mm",
            "chuvaConvec": "mm",
            "u": "m/s",
            "v": "m/s",
            "wind": "m/s",
            "winds": "m/s",
        }
        return unit_map.get(var_name, "")

    def generate(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        output_dir: Optional[str] = None,
        dpi: int = 150,
        title: Optional[str] = None,
    ) -> list[str]:
        if not HAS_MAP_BACKEND:
            logger.error(
                "Map generation requires Cartopy or Basemap. "
                "Install one of them (pip install cartopy)."
            )
            return []

        if var_name in ("wind", "winds"):
            return self._generate_wind_maps(
                var_name, region, level, date_str, analysis, output_dir, dpi, title
            )

        return self._generate_variable_maps(
            var_name, region, level, date_str, analysis, forecast_hours,
            output_dir, dpi, title,
        )

    def _generate_variable_maps(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        output_dir: Optional[str] = None,
        dpi: int = 150,
        title: Optional[str] = None,
    ) -> list[str]:
        grib_objs = self.processor.load_gribs(date_str, analysis, forecast_hours)
        if not grib_objs:
            logger.error("No GRIB data loaded.")
            return []

        resolved_level = self.processor.resolve_level(var_name, level)
        var_msgs = self.processor.select_variable_from_gribs(
            grib_objs, var_name, resolved_level
        )

        if output_dir is None:
            output_dir = str(self.settings.dir_mapas)

        saved_files = []
        lon_min, lon_max, lat_min, lat_max = region.bounds

        for msg in var_msgs:
            data, lat, lon = self.processor.extract_data(
                msg, lon_min, lon_max, lat_min, lat_max
            )
            data, unit = self.processor.convert_units(data, var_name)

            ft = msg.forecastTime
            ft_str = f"{ft:02d}"

            lon_grid, lat_grid = np.meshgrid(lon, lat)

            _lon_min = float(lon_grid.min())
            _lon_max = float(lon_grid.max())
            _lat_min = float(lat_grid.min())
            _lat_max = float(lat_grid.max())

            intervals = self._compute_intervals(data)

            rc("font", weight="normal")
            fig = plt.figure(figsize=(18, 16))

            if HAS_CARTOPY:
                ax = self._setup_cartopy_axis(
                    fig, _lon_min, _lon_max, _lat_min, _lat_max
                )
                contourf = ax.contourf(
                    lon_grid, lat_grid, np.squeeze(data),
                    levels=intervals, cmap="viridis",
                    transform=ccrs.PlateCarree(),
                )
                cs1 = ax.contour(
                    lon_grid, lat_grid, np.squeeze(data),
                    colors="k", levels=intervals, linewidths=0.2,
                    transform=ccrs.PlateCarree(),
                )
                plt.clabel(cs1, fmt="%d", fontsize=8)
                cbar = fig.colorbar(contourf, ax=ax, shrink=0.8, pad=0.02)
            else:
                m = Basemap(
                    projection="mill",
                    llcrnrlat=_lat_min,
                    urcrnrlat=_lat_max,
                    llcrnrlon=_lon_min,
                    urcrnrlon=_lon_max,
                    resolution="i",
                )
                x, y = m(lon_grid, lat_grid)
                self._draw_basemap_decorations(m, _lon_min, _lon_max, _lat_min, _lat_max)
                contourf = m.contourf(
                    x, y, np.squeeze(data), cmap="viridis", levels=intervals
                )
                cs1 = m.contour(
                    x, y, np.squeeze(data),
                    colors="k", levels=intervals, linewidths=0.2,
                )
                plt.clabel(cs1, fmt="%d", fontsize=8)
                cbar = m.colorbar(contourf, location="right", pad="1%")

            cbar.set_label(unit if unit != "units" else msg.units)

            default_title = (
                f"GFS {msg.iDirectionIncrementInDegrees} - {region.name} "
                f"{var_name} - Nivel: {resolved_level or level} "
                f"Data: {msg.dataDate} Prev: {ft_str}"
            )
            plt.title(title or default_title, weight="normal", fontsize=12)

            filename = (
                f"GFS_{msg.iDirectionIncrementInDegrees}_{region.name}_"
                f"N{resolved_level or level}_{var_name}_{msg.dataDate}_{ft_str}.png"
            )
            filepath = f"{output_dir}/{filename}"
            plt.savefig(filepath, bbox_inches="tight", dpi=dpi)
            plt.close()
            saved_files.append(filepath)
            logger.info("Map saved: %s", filepath)

        return saved_files

    def _generate_wind_maps(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        output_dir: Optional[str] = None,
        dpi: int = 150,
        title: Optional[str] = None,
    ) -> list[str]:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        if not grib_objs:
            return []

        resolved_level = self.processor.resolve_level("u", level)
        u_msgs = self.processor.select_variable_from_gribs(grib_objs, "u", resolved_level)
        v_msgs = self.processor.select_variable_from_gribs(grib_objs, "v", resolved_level)

        if output_dir is None:
            output_dir = str(self.settings.dir_mapas)

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

            lons, lats = np.meshgrid(lon_u, lat_u)

            _lon_min = float(lons.min())
            _lon_max = float(lons.max())
            _lat_min = float(lats.min())
            _lat_max = float(lats.max())

            fig1 = plt.figure(figsize=(18, 16))

            if HAS_CARTOPY:
                ax = self._setup_cartopy_axis(
                    fig1, _lon_min, _lon_max, _lat_min, _lat_max
                )
                speed = np.sqrt(data_u**2 + data_v**2)
                try:
                    strm = ax.streamplot(
                        lons, lats, data_u, data_v,
                        color=speed, linewidth=1, cmap=plt.cm.inferno,
                        density=5, arrowstyle="->", arrowsize=1.5,
                    )
                    sm = strm.lines
                except ImportError:
                    logger.warning(
                        "Cartopy streamplot requires scipy; falling back to quiver."
                    )
                    step = max(1, lons.shape[0] // 8)
                    sm = ax.quiver(
                        lons[::step, ::step], lats[::step, ::step],
                        data_u[::step, ::step], data_v[::step, ::step],
                        speed[::step, ::step], cmap=plt.cm.inferno,
                    )
                cb = fig1.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
            else:
                m = Basemap(
                    projection="cyl",
                    llcrnrlat=_lat_min,
                    urcrnrlat=_lat_max,
                    llcrnrlon=_lon_min,
                    urcrnrlon=_lon_max,
                    resolution="i",
                )
                ax = fig1.add_axes([0.1, 0.1, 0.7, 0.7])
                x, y = m(lons, lats)
                self._draw_basemap_decorations(m, _lon_min, _lon_max, _lat_min, _lat_max)
                speed = np.sqrt(data_u**2 + data_v**2)
                strm = plt.streamplot(
                    lons, lats, data_u, data_v,
                    color=speed, linewidth=1, cmap=plt.cm.inferno,
                    density=5, arrowstyle="->", arrowsize=1.5,
                )
                cb = plt.colorbar(strm.lines)

            cb.ax.set_ylabel("Vento m/s", fontsize=14)

            default_title = (
                f"GFS {u_msg.iDirectionIncrementInDegrees} - {region.name} "
                f"Vento [m/s] - Nivel: {resolved_level or level} "
                f"Data: {u_msg.dataDate} Prev: {ft_str}"
            )
            plt.title(title or default_title, weight="normal", fontsize=12)

            filename = (
                f"GFS_{u_msg.iDirectionIncrementInDegrees}_{region.name}_"
                f"N{resolved_level or level}_CampoVento_{u_msg.dataDate}_{ft_str}.png"
            )
            filepath = f"{output_dir}/{filename}"
            plt.savefig(filepath, bbox_inches="tight", dpi=dpi)
            plt.close()
            saved_files.append(filepath)
            logger.info("Wind map saved: %s", filepath)

        return saved_files

    def _setup_cartopy_axis(self, fig, lon_min, lon_max, lat_min, lat_max):
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
        try:
            ax.coastlines(resolution="50m", linewidth=0.5)
            ax.add_feature(cfeature.BORDERS, linewidth=0.3)
            ax.add_feature(cfeature.STATES, linewidth=0.2)
        except Exception as e:
            logger.warning("Could not draw Cartopy features (offline?): %s", e)
        try:
            gl = ax.gridlines(
                crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.3,
                color="k", alpha=0.5,
            )
            gl.top_labels = False
            gl.right_labels = False
        except Exception as e:
            logger.warning("Could not draw gridlines: %s", e)
        return ax

    def _draw_basemap_decorations(self, m, lon_min, lon_max, lat_min, lat_max):
        meridianinterval = np.arange(lon_min, lon_max, 4)
        parallelsinterval = np.arange(lat_min, lat_max)
        m.drawparallels(
            parallelsinterval, labels=[1, 0, 0, 0], color="k", linewidth=0.3
        )
        m.drawmeridians(
            meridianinterval, labels=[0, 0, 0, 1], color="k", linewidth=0.3
        )
        m.drawcoastlines(linewidth=0.5)
        m.drawcountries()
        m.drawstates()
