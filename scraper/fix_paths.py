"""
fix_paths.py - Fix path issues for the PLUS Product Analyzer
"""
import os
import sys
import logging
from pathlib import Path
import json
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_and_fix_paths():
    """Check paths and fix issues"""
    # Current directory should be the scraper directory
    script_dir = Path(__file__).parent.absolute()
    logger.info(f"Running from: {script_dir}")
    
    # Check required folders
    data_dir = script_dir / "data"
    products_dir = data_dir / "products"
    analysis_dir = data_dir / "analysis"
    
    # Create missing directories
    for directory in [data_dir, products_dir, analysis_dir]:
        if not directory.exists():
            logger.info(f"Creating missing directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
    
    # Check if products directory has files
    product_files = list(products_dir.glob("*.json"))
    logger.info(f"Found {len(product_files)} product files in {products_dir}")
    
    # Check database file
    db_path = data_dir / "db.json"
    if db_path.exists():
        logger.info(f"Database file found: {db_path}")
    else:
        logger.warning(f"Database file not found: {db_path}")
        
        # If we have product files, we can create the database
        if product_files:
            logger.info("Will create database when you run the analysis")

    # Check Python packages
    try:
        import flask
        logger.info("Flask is installed")
    except ImportError:
        logger.warning("Flask is not installed. Run: pip install -r requirements_analysis.txt")
    
    try:
        import pandas
        logger.info("Pandas is installed")
    except ImportError:
        logger.warning("Pandas is not installed. Run: pip install -r requirements_analysis.txt")
        
    try:
        import plotly
        logger.info("Plotly is installed")
    except ImportError:
        logger.warning("Plotly is not installed. Run: pip install -r requirements_analysis.txt")

    # Check if the analysis directory is properly set up
    analysis_app = script_dir / "analysis" / "app.py"
    if analysis_app.exists():
        logger.info(f"Analysis app found: {analysis_app}")
    else:
        logger.error(f"Analysis app not found: {analysis_app}")

    logger.info(f"Path check completed.")
    logger.info("-" * 40)
    logger.info("To run the analysis, use: python start_analysis.py")
    
    return True

if __name__ == "__main__":
    check_and_fix_paths()
