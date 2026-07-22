import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from server_MET.config import Settings

logger = logging.getLogger(__name__)

ANALYSIS_HOURS = ["00", "06", "12", "18"]
FORECAST_HOURS = ["00", "06", "12", "18"]
RESOLUTIONS = ["0p25", "0p50", "1p00"]


class GribDownloader:
    def __init__(self) -> None:
        self.settings = Settings()

    def get_current_analysis_hour(self) -> str:
        now = datetime.now()
        h = now.hour
        if h < 6:
            return "00"
        elif h < 12:
            return "06"
        elif h < 18:
            return "12"
        return "18"

    def get_date_str(self, dt: Optional[datetime] = None) -> str:
        if dt is None:
            dt = datetime.now()
        return dt.strftime("%Y%m%d")

    def check_url_exists(self, url: str) -> bool:
        try:
            result = subprocess.run(
                ["wget", "--spider", "--quiet", url],
                capture_output=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("wget not available or timeout checking URL: %s", url)
            return False

    def download_file(
        self, url: str, dest_path: Path, timeout: int = 300
    ) -> bool:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                ["wget", "-O", str(dest_path), url],
                capture_output=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                logger.info("Downloaded: %s -> %s", url, dest_path)
                return True
            logger.error(
                "Failed to download %s: %s", url, result.stderr.decode()
            )
            return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout downloading %s", url)
            return False
        except FileNotFoundError:
            logger.error("wget not found. Install wget or use curl.")
            return False

    def download_gribs(
        self,
        date_str: Optional[str] = None,
        analysis_hour: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        resolution: str = "0p25",
        force: bool = False,
    ) -> list[Path]:
        if date_str is None:
            date_str = self.get_date_str()
        if analysis_hour is None:
            analysis_hour = self.get_current_analysis_hour()
        if forecast_hours is None:
            forecast_hours = FORECAST_HOURS

        downloaded = []
        base_url = f"{self.settings.gfs_url}{date_str}/{analysis_hour}/atmos/"
        dest_dir = self.settings.dir_gribs / date_str / analysis_hour
        dest_dir.mkdir(parents=True, exist_ok=True)

        for fh in forecast_hours:
            filename = f"gfs.t{analysis_hour}z.pgrb2.{resolution}.f0{fh}"
            filepath = dest_dir / filename

            if filepath.exists() and not force:
                logger.info("File already exists: %s", filepath)
                downloaded.append(filepath)
                continue

            url = f"{base_url}{filename}"
            logger.info("Checking URL: %s", url)

            if not self.check_url_exists(url):
                logger.warning("URL not available: %s", url)
                continue

            if self.download_file(url, filepath):
                downloaded.append(filepath)

        return downloaded

    def download_gribs_all_resolutions(
        self,
        date_str: Optional[str] = None,
        analysis_hour: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
        force: bool = False,
    ) -> dict[str, list[Path]]:
        results = {}
        for res in RESOLUTIONS:
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

    def clean_old_gribs(self, days_old: int = 2) -> int:
        removed = 0
        cutoff = datetime.now() - timedelta(days=days_old)

        for date_dir in self.settings.dir_gribs.iterdir():
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
                            f.unlink(missing_ok=True)
                            removed += 1
                        ana_dir.rmdir()
                date_dir.rmdir()
                logger.info("Removed old grib dir: %s", date_dir)
        return removed
