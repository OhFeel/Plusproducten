"""
test_product.py - Eenvoudig testscript om 1 product te scrapen
"""

import argparse
import json
from utils import setup_logger
from product_scraper import ProductScraper
from cookie_manager import cookie_manager

def main():
    # Setup logging
    logger = setup_logger()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Test product scraper')
    parser.add_argument('--sku', type=str, default='553975', help='Product SKU to test')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel('DEBUG')
    
    sku = args.sku
    
    # Toon cookie informatie
    cookies = cookie_manager.get_cookies()
    print(f"Geladen cookies: {len(cookies)}")
    
    # Maak een product scraper aan
    scraper = ProductScraper()
    
    # Probeer het product op te halen
    try:
        print(f"Ophalen van product SKU: {sku}...")
        product = scraper.process_product(sku)
        
        if product:
            print("\nProduct informatie:")
            print(f"Naam: {product.get('name')}")
            print(f"Merk: {product.get('brand')}")
            print(f"Prijs: {product.get('price')}")
            print(f"Aantal voedingswaarden: {len(product.get('nutrients', []))}")
            
            # Toon eerste 3 voedingswaarden
            print("\nVoedingswaarden:")
            for nutrient in product.get('nutrients', [])[:3]:
                print(f"- {nutrient.get('name')}: {nutrient.get('value')} {nutrient.get('unit')}")
            
            # Toon ingrediënten preview
            ingredients = product.get('ingredients', '')
            if ingredients:
                print(f"\nIngrediënten: {ingredients[:100]}...")
            
            print("\nSUCCES! Product opgehaald.")
        else:
            print("Fout: Kon geen product gegevens ophalen.")
    
    except Exception as e:
        print(f"Fout bij ophalen product: {e}")

if __name__ == "__main__":
    main()
