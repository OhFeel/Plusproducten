"""
database.py - TinyDB database handler for the PLUS scraper
"""

import os
import time
import ujson
from tinydb import TinyDB, Query
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from utils import logger

class ProductDatabase:
    """
    TinyDB database for storing product information
    """
    
    def __init__(self, db_path: str = "data/db.json"):
        self.db_path = db_path
        # Create directory if it doesn't exist
        Path(db_path).parent.mkdir(exist_ok=True, parents=True)
        
        # Use CachingMiddleware and ujson for better performance
        self.db = TinyDB(
            db_path, 
            storage=CachingMiddleware(JSONStorage),
            sort_keys=True,
            indent=2,
            ensure_ascii=False
        )
        
        # Create tables
        self.products = self.db.table('products')
        self.nutrients = self.db.table('nutrients')
        self.stats = self.db.table('stats')
        
        logger.info(f"Database initialized at {db_path}")
    
    def insert_product(self, product: Dict[str, Any]) -> int:
        """
        Insert a product into the database
        Returns the document ID
        """
        # Extract the SKU
        sku = product.get("sku", "")
        if not sku:
            logger.warning("Cannot insert product without SKU")
            return -1
        
        # Check if the product already exists
        Product = Query()
        existing = self.products.get(Product.sku == sku)
        
        if existing:
            # Update existing product
            doc_id = existing.doc_id
            self.products.update(product, doc_ids=[doc_id])
            logger.debug(f"Updated product {sku} with ID {doc_id}")
            return doc_id
        else:
            # Insert new product
            doc_id = self.products.insert(product)
            logger.debug(f"Inserted product {sku} with ID {doc_id}")
            return doc_id
    
    def insert_products(self, products: List[Dict[str, Any]]) -> List[int]:
        """
        Insert multiple products into the database
        Returns a list of document IDs
        """
        if not products:
            return []
        
        to_insert = []
        to_update = {}
        doc_ids = []
        
        # Check which products already exist
        Product = Query()
        skus = [p.get("sku") for p in products if p.get("sku")]
        
        for sku in skus:
            existing = self.products.get(Product.sku == sku)
            if existing:
                to_update[existing.doc_id] = next((p for p in products if p.get("sku") == sku), {})
            else:
                product = next((p for p in products if p.get("sku") == sku), {})
                if product:
                    to_insert.append(product)
        
        # Insert new products in batch
        if to_insert:
            new_ids = self.products.insert_multiple(to_insert)
            doc_ids.extend(new_ids)
        
        # Update existing products
        for doc_id, product in to_update.items():
            self.products.update(product, doc_ids=[doc_id])
            doc_ids.append(doc_id)
        
        logger.info(f"Saved {len(doc_ids)} products to database")
        return doc_ids
    
    def insert_nutrients_data(self, product_id: int, sku: str, nutrients: List[Dict[str, Any]]) -> List[int]:
        """
        Insert nutrient information into the database
        Links it to the product ID
        """
        if not nutrients:
            return []
        
        # Format nutrients data
        nutrients_data = []
        for nutrient in nutrients:
            nutrients_data.append({
                "product_id": product_id,
                "sku": sku,
                "name": nutrient.get("name", ""),
                "value": nutrient.get("value", "0"),
                "unit": nutrient.get("unit", ""),
                "parent_code": nutrient.get("parent_code", ""),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Insert nutrients in batch
        doc_ids = self.nutrients.insert_multiple(nutrients_data)
        logger.debug(f"Inserted {len(doc_ids)} nutrients for product {sku}")
        return doc_ids
    
    def get_processed_skus(self) -> Set[str]:
        """
        Get a set of SKUs that have already been processed
        """
        Product = Query()
        results = self.products.search(Product.sku.exists())
        return {doc.get("sku") for doc in results if doc.get("sku")}
    
    def save_stats(self, stats: Dict[str, Any]) -> int:
        """
        Save statistics about the scraping run
        """
        stats["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return self.stats.insert(stats)
    
    def get_product_count(self) -> int:
        """
        Get the total number of products in the database
        """
        return len(self.products)
    
    def close(self) -> None:
        """
        Close the database connection
        """
        self.db.close()
        logger.debug("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
