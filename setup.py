#!/usr/bin/env python3
"""
setup.py - Setup script for PLUS Product Scraper
This script helps users configure the scraper for first-time use
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def print_header():
    print("\n" + "="*60)
    print("        🛒 PLUS PRODUCT SCRAPER SETUP")
    print("="*60)
    print("Welcome! This script will help you set up the PLUS Product Scraper.")
    print("Please follow the steps below to get started.\n")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = [
        "scraper/data",
        "scraper/data/products",
        "scraper/data/analysis",
        "data/analysis/images"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {directory}")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    # Install scraper dependencies
    print("   Installing scraper requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "scraper/requirements.txt"], 
                      check=True, capture_output=True)
        print("   ✅ Scraper dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install scraper dependencies: {e}")
        return False
    
    # Install analysis dependencies
    print("   Installing analysis requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_analysis.txt"], 
                      check=True, capture_output=True)
        print("   ✅ Analysis dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install analysis dependencies: {e}")
        return False
    
    return True

def setup_environment():
    """Set up environment configuration"""
    print("\n⚙️  Setting up environment...")
    
    env_path = Path("scraper/.env")
    env_example_path = Path("scraper/.env.example")
    
    if env_path.exists():
        print("   ℹ️  .env file already exists")
        response = input("   Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("   ⏭️  Skipping environment setup")
            return True
    
    if env_example_path.exists():
        shutil.copy(env_example_path, env_path)
        print("   ✅ Created .env from template")
        print("   ⚠️  IMPORTANT: You must configure your .env file!")
        print("      See SECURITY.md and scraper/COOKIES.md for instructions")
    else:
        print("   ❌ .env.example not found")
        return False
    
    return True

def show_next_steps():
    """Show next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 NEXT STEPS:")
    print("1. 🔑 Configure your credentials:")
    print("   - Edit scraper/.env file")
    print("   - Add your CSRF token from PLUS.nl")
    print("   - Set up cookies (see scraper/COOKIES.md)")
    print("\n2. 🕷️  Run the scraper:")
    print("   cd scraper")
    print("   python main.py --all --limit 50")
    print("\n3. 📊 Analyze the data:")
    print("   python analyze_data.py")
    print("\n4. 📚 Read the documentation:")
    print("   - README.md - Main documentation")
    print("   - SECURITY.md - Security and setup guide")
    print("   - scraper/COOKIES.md - Cookie setup guide")
    print("\n⚠️  REMEMBER: This tool is for educational purposes only.")
    print("   Please respect PLUS.nl's terms of service!")

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        return 1
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Setup failed during environment configuration")
        return 1
    
    # Show next steps
    show_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
