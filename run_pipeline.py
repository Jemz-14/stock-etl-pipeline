"""run_pipeline.py - Master Orchestrator for the Stock ETL Pipeline"""

import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler() # This keeps printing to your console too
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Executes a python script and logs its results"""
    logger.info(f"RUNNING SCRIPT {script_name}")
    try:
        subprocess.run(["python", script_name], check=True)
        logger.info(f"SUCCESSFULLY RUNNING SCRIPT {script_name}")

    except subprocess.CalledProcessError as e:
        logger.error(f"FAILED RUNNING SCRIPT {script_name} with error code {e.returncode}")
        raise # Stops pipeline if a step fails

def main():
    logger.info("========================================")
    logger.info("INITIATING MASTER ETL PIPELINE")
    logger.info("========================================")

    pipeline_steps = [
        'extract.py',
        'transform.py',
        'load.py',
        'analysis.py',
    ]

    for step in pipeline_steps:
        run_script(step)

    logger.info("========================================")
    logger.info("PIPELINE COMPLETED")
    logger.info("========================================")

if __name__ == "__main__":
    main()