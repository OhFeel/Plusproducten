"""
migrate_db.py - Creates a TinyDB database from individual product JSON files
"""
import os
import sys
import json
import logging
from pathlib import Path
from tinydb import TinyDB, Query
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_database():
    """Create a TinyDB database from individual product JSON files"""
    # Use absolute paths to avoid working directory issues
    script_dir = Path(__file__).parent.absolute()
    products_dir = script_dir / "data" / "products"
    db_path = script_dir / "data" / "db.json"
    
    # Print debug info
    logger.info(f"Script directory: {script_dir}")
    logger.info(f"Products directory: {products_dir}")
    logger.info(f"Database path: {db_path}")
    
    if not products_dir.exists() or not products_dir.is_dir():
        logger.error(f"Products directory not found at {products_dir}")
        return False
    
    # Create the database directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize the TinyDB database
    db = TinyDB(db_path)
    products_table = db.table('products')
    nutrients_table = db.table('nutrients')
    
    # Clear existing data
    products_table.truncate()
    nutrients_table.truncate()
    
    # Process each product JSON file
    product_files = list(products_dir.glob("*.json"))
    
    if not product_files:
        logger.error(f"No product JSON files found in {products_dir}")
        return False
    
    logger.info(f"Processing {len(product_files)} product files...")
    
    processed_count = 0
    nutrient_count = 0
    
    for product_file in product_files:
        try:
            # Load product data
            with open(product_file, 'r', encoding='utf-8') as f:
                product_data = json.load(f)
            
            # Extract SKU from filename or from data
            if 'sku' not in product_data:
                # Try to extract SKU from filename (format: "123456_ProductName.json")
                filename = product_file.stem
                if "_" in filename:
                    sku = filename.split("_")[0]
                    product_data['sku'] = sku
                else:
                    logger.warning(f"Could not determine SKU for {product_file.name}, skipping")
                    continue
            
            # Extract nutrients if available
            nutrients = product_data.pop('nutrients', [])
            
            # Add timestamp if not present
            if 'extracted_at' not in product_data:
                product_data['extracted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert product into database
            product_id = products_table.insert(product_data)
            
            # Process nutrients
            if nutrients:
                for nutrient in nutrients:
                    # Add SKU to each nutrient
                    nutrient['sku'] = product_data['sku']
                    nutrients_table.insert(nutrient)
                    nutrient_count += 1
            
            processed_count += 1
            
            # Log progress periodically
            if processed_count % 50 == 0:
                logger.info(f"Processed {processed_count}/{len(product_files)} products...")
                
        except Exception as e:
            logger.error(f"Error processing {product_file.name}: {e}")
    
    logger.info(f"Database creation completed:")
    logger.info(f"- Added {processed_count} products")
    logger.info(f"- Added {nutrient_count} nutrient entries")
    
    # Create the analysis directory
    analysis_path = Path("data/analysis")
    analysis_path.mkdir(exist_ok=True, parents=True)
    
    return True

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
