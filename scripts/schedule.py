#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agendador de tarefas - Server MET v2.0
Usa APScheduler para execução periódica do pipeline
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from core.config import SCHEDULER_TIMEZONE, PIPELINE_SCHEDULE_HOURS
from scripts.run_pipeline import METPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class METScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)
        self.pipeline = METPipeline()
    
    def add_jobs(self):
        for hour in PIPELINE_SCHEDULE_HOURS:
            self.scheduler.add_job(
                self.run_scheduled_pipeline,
                CronTrigger(hour=hour, minute=30, timezone=SCHEDULER_TIMEZONE),
                id=f"pipeline_{hour:02d}",
                name=f"MET Pipeline {hour:02d}Z",
                replace_existing=True
            )
            logger.info(f"Scheduled pipeline for {hour:02d}:30 {SCHEDULER_TIMEZONE}")
    
    async def run_scheduled_pipeline(self):
        logger.info(f"Starting scheduled pipeline at {datetime.now()}")
        try:
            await self.pipeline.run_download()
            result = self.pipeline.run_full_pipeline()
            logger.info(f"Scheduled pipeline completed: {result}")
        except Exception as e:
            logger.error(f"Scheduled pipeline failed: {e}")
    
    def start(self):
        self.add_jobs()
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

async def main():
    scheduler = METScheduler()
    scheduler.start()
    
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())