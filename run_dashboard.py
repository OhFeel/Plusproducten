import os
import sys
from pathlib import Path

print("Setting up PLUS Product Analyzer...")

# Create necessary directories
os.makedirs('static', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Install required packages if needed
try:
    import dash
    import plotly
    import flask
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")

# Prepare static assets
try:
    from prepare_assets import create_simple_logo_png, create_simple_favicon
    create_simple_logo_png()
    create_simple_favicon()
except Exception as e:
    print(f"Error preparing assets: {e}")
    print("Continuing with launch...")

# Launch the Flask application
print("\n" + "="*50)
print("Launching PLUS Product Analyzer Dashboard")
print("="*50)
print("Access the dashboard at: http://127.0.0.1:5000")
print("Press CTRL+C to stop the server\n")

from app import app
app.run_server(debug=True)
