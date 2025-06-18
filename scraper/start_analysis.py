"""
start_analysis.py - Helper script to prepare and start the product analysis
"""
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def print_step(step, message):
    print(f"\n[{step}] {message}")
    print("=" * 60)

def run_command(command, explanation):
    print(f"  > {explanation}")
    print(f"  $ {command}")
    result = subprocess.run(command, shell=True, text=True)
    return result.returncode == 0

def main():
    print("\n" + "=" * 60)
    print("         PLUS PRODUCT ANALYZER - STARTUP HELPER         ")
    print("=" * 60)
    
    # Step 0: Fix paths
    print_step(0, "Checking and fixing paths")
    try:
        run_command("python fix_paths.py", "Running path fixer")
        print("Path check completed")
    except Exception as e:
        print(f"Warning: Path check failed: {e}")
    
    # Step 1: Verify data exists
    print_step(1, "Checking for product data")
    script_dir = Path(__file__).parent.absolute()
    products_dir = script_dir / "data" / "products"
    if not products_dir.exists() or len(list(products_dir.glob("*.json"))) == 0:
        print("ERROR: No product data found in data/products/")
        print("Please run the scraper first to collect product data:")
        print("  $ python main.py --all")
        return False

    product_count = len(list(products_dir.glob("*.json")))
    print(f"Found {product_count} product files. Good!")
    
    # Step 2: Create database from individual files
    print_step(2, "Creating analysis database")
    if not run_command("python migrate_db.py", "Converting product files to database"):
        print("ERROR: Failed to create database from product files")
        return False
    
    # Step 3: Install required packages
    print_step(3, "Installing required packages")
    if not run_command("pip install -r requirements_analysis.txt", "Installing analysis requirements"):
        print("WARNING: Some packages might not be installed correctly")
        print("If you encounter errors, try installing them manually:")
        print("  $ pip install -r requirements_analysis.txt")
    
    # Step 4: Start the analyzer
    print_step(4, "Starting the analysis web server")
    print("\nThe analysis web app will start in a moment.")
    print("A browser window should open automatically.")
    print("If not, visit http://localhost:5000 in your browser.\n")
    
    # Give the user a chance to read the information
    input("Press Enter to continue...")
    
    # Run the analysis app
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_command("python run_analysis.py", "Starting web server")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
