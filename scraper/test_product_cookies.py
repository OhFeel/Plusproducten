"""
test_product_cookies.py - Test the cookie-based product fetching
"""

import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from utils import logger, setup_logger
from product_scraper import ProductScraper
from cookie_manager import cookie_manager

# Load environment variables
load_dotenv()

def main():
    # Configure logger
    logger = setup_logger(log_file=True)
    logger.setLevel("INFO")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PLUS Product Cookie Test")
    parser.add_argument("--sku", type=str, default="553975", help="SKU van het product om te scrapen")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel("DEBUG")
    
    sku = args.sku
    logger.info(f"Test cookie-based product scraping voor SKU: {sku}")
    
    # Show current cookies
    cookies = cookie_manager.get_cookies()
    logger.info(f"Huidige cookies: {len(cookies)}")
    if args.debug:
        for name, value in cookies.items():
            logger.debug(f"Cookie: {name} = {value[:10]}...")
    
    # Create scraper and fetch product
    product_scraper = ProductScraper()
    
    try:
        # Generate product URL
        product_url = f"https://www.plus.nl/product/product-{sku}"
        
        # Fetch product
        logger.info(f"Fetching product {sku} met cookies...")
        response_data = product_scraper.fetch_product(sku, product_url)
        
        # Process the data
        product_data = product_scraper.extract_product_data(response_data)
        
        # Show product information
        print("\n" + "="*50)
        print(f"SUCCES! Product {sku} opgehaald met cookies")
        print(f"Naam: {product_data.get('name', '')}")
        print(f"Merk: {product_data.get('brand', '')}")
        print(f"Prijs: {product_data.get('price', '')}")
        print("="*50)
        
        # Save to output file for inspection
        output_dir = Path("data/test")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"product_{sku}_cookie_test.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Product data opgeslagen in {output_file}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error bij product cookie test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main())
