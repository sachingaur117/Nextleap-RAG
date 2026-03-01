import sys
import os
import time
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent path to allow importing previous phase logic
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
sys.path.append(PARENT_DIR)

# We will trigger the Phase 1 and Phase 2 scripts purely via subprocesses
# to avoid pathing complexites and state imports
import subprocess

def run_data_pipeline():
    logger.info("====================================")
    logger.info("Automatic NextLeap Data Pipeline Triggered")
    logger.info("====================================")
    
    try:
        # 1. Run Phase 1 Scraper
        logger.info("Executing Phase 1 Web Scraper...")
        scraper_script = os.path.join(PARENT_DIR, "phase1_data_acquisition", "scraper.py")
        subprocess.run([sys.executable, scraper_script], check=True, cwd=PARENT_DIR)
        logger.info("Phase 1 complete! Data has been scraped.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute the Phase 1 web scraper: {e}")
        return

    try:
        # 2. Run Phase 2 DB Construction to consume the fresh data
        logger.info("Executing Phase 2 Vector Embedding & DB insertion...")
        # Since process_courses natively operates on its own path assumption, we trigger build_db.py exactly like scraper
        build_db_script = os.path.join(PARENT_DIR, "phase2_vector_database", "build_db.py")
        db_dir = os.path.dirname(build_db_script)
        subprocess.run([sys.executable, build_db_script], check=True, cwd=db_dir)
        logger.info("Phase 2 complete! Vector database updated with latest chunks.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute Phase 2 ingestion: {e}")
        return
        
    logger.info("====================================")
    logger.info("Automatic Pipeline Completed Successfully!")
    logger.info("====================================")

if __name__ == "__main__":
    logger.info("Initializing Automated Scheduler for NextLeap...")
    logger.info("Running initial pipeline sync on startup...")
    
    # Run once at startup
    run_data_pipeline()
    
    # Schedule to run every Sunday at 3:00 AM
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_data_pipeline, 'cron', day_of_week='sun', hour=3, minute=0)
    scheduler.start()
    
    logger.info("Scheduler is now running in the background. Press Ctrl+C to exit.")
    
    try:
        # Keep the main thread alive.
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down gracefully.")
