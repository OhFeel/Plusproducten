"""
run_analysis.py - Script to run the product analysis
"""
import os
import sys
import argparse
from pathlib import Path
import subprocess
import webbrowser
from datetime import datetime

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PLUS Product Analyzer")
    
    parser.add_argument("--port", type=int, default=5000, help="Port to run the web server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--preprocess", action="store_true", help="Only run data preprocessing")
    
    return parser.parse_args()

def ensure_requirements():
    """Make sure all requirements are installed"""
    req_file = Path("requirements_analysis.txt")
    
    if not req_file.exists():
        print("Error: requirements_analysis.txt not found.")
        return False
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False

def run_preprocessing():
    """Run data preprocessing"""
    print("Running data preprocessing...")
    
    # Use absolute paths to avoid working directory issues
    script_dir = Path(__file__).parent.absolute()
    analysis_dir = script_dir / "data" / "analysis"
    db_path = script_dir / "data" / "db.json"
    
    # Make sure data/analysis folder exists
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Print debug info
    print(f"Script directory: {script_dir}")
    print(f"Data directory: {script_dir / 'data'}")
    print(f"Database path: {db_path}")
    
    # First check if db.json exists, otherwise run migrate_db.py
    if not db_path.exists():
        print("Database file not found. Running migration script...")
        try:
            migrate_script = script_dir / "migrate_db.py"
            subprocess.run([sys.executable, str(migrate_script)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running database migration: {e}")
            return False
    
    # Run the processor
    try:
        from analysis.data_processor import ProductDataProcessor
        processor = ProductDataProcessor()
        output_path = processor.export_analysis_to_json()
        print(f"Analysis data exported to {output_path}")
        return True
    except Exception as e:
        print(f"Error running preprocessing: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def run_webapp(port, open_browser=True):
    """Run the web application"""
    print(f"Starting web server on port {port}...")
    print(f"You can access the analysis at http://localhost:{port}")
    
    # Change to the analysis directory
    analysis_dir = Path("analysis").absolute()
    os.chdir(analysis_dir)
    
    # Add the analysis directory to the sys.path so the import works
    sys.path.insert(0, str(analysis_dir))
    
    # Open browser if requested
    if open_browser:
        webbrowser.open(f"http://localhost:{port}")
    
    # Run the Flask app
    from app import app
    app.run(debug=True, port=port)

def main():
    # Change to the script's directory to ensure all paths work correctly
    script_path = Path(__file__).parent.absolute()
    os.chdir(script_path)
    
    args = parse_args()
    print("=" * 50)
    print(f"PLUS Product Analyzer - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    print("=" * 50)
    
    # Ensure requirements are installed
    if not ensure_requirements():
        sys.exit(1)
    
    # Run preprocessing if requested
    if args.preprocess:
        success = run_preprocessing()
        sys.exit(0 if success else 1)
    
    # Run preprocessing in any case
    success = run_preprocessing()
    if not success:
        print("WARNING: Preprocessing failed. The app might not work correctly.")
        input("Press Enter to continue anyway, or Ctrl+C to abort...")
    
    # Run the web app
    run_webapp(args.port, not args.no_browser)

if __name__ == "__main__":
    main()
