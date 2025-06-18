"""
main.py - Main entry point for the PLUS scraper
"""

import os
import time
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dotenv import load_dotenv

# Local imports
from utils import logger, create_checkpoint, load_checkpoint
from sitemap_parser import SitemapParser
from product_scraper import ProductScraper
from database import ProductDatabase
from proxy_manager import proxy_manager
from cookie_manager import cookie_manager  # Importeer cookie_manager

# Load environment variables
load_dotenv()

def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description="PLUS Product Scraper")
    
    # Main operation modes
    parser.add_argument("--sitemap", action="store_true", help="Parse the sitemap only")
    parser.add_argument("--scrape", action="store_true", help="Scrape product details")
    parser.add_argument("--all", action="store_true", help="Run the full pipeline (default)")
    
    # Additional options
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh the sitemap")
    parser.add_argument("--limit", type=int, help="Limit the number of products to process")
    parser.add_argument("--skip", type=int, default=0, help="Skip the first N products")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of products to process in a batch")
    parser.add_argument("--sku", type=str, help="Process only a specific SKU")
    parser.add_argument("--retry", action="store_true", help="Process items in retry.json")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set default mode if none selected
    if not (args.sitemap or args.scrape or args.all or args.retry or args.sku):
        args.all = True
    
    return args

def sitemap_task(args) -> List[Dict[str, str]]:
    """
    Parse and cache the sitemap
    """
    logger.info("Starting sitemap parsing task")
    sitemap_parser = SitemapParser()
    
    # Parse the sitemap
    product_urls = sitemap_parser.get_urls(force_refresh=args.force_refresh)
    logger.info(f"Found {len(product_urls)} product URLs in the sitemap")
    
    return product_urls

def scrape_task(args, product_urls: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Scrape product details
    """
    logger.info("Starting product scraping task")
    
    # Initialize components
    sitemap_parser = SitemapParser()
    product_scraper = ProductScraper()
    db = ProductDatabase()
    
    # Get product URLs if not provided
    if not product_urls:
        product_urls = sitemap_parser.get_urls()
    
    # Get processed SKUs from database
    processed_skus = db.get_processed_skus()
    logger.info(f"Found {len(processed_skus)} already processed SKUs in database")
    
    # Filter to unprocessed products
    if args.sku:
        # Process only the specified SKU
        urls_to_process = [url for url in product_urls if url.get("sku") == args.sku]
        if not urls_to_process:
            urls_to_process = [{"sku": args.sku, "url": "", "lastmod": ""}]
    elif args.retry:
        # Process retry items
        retry_file = Path("data/retry.json")
        if not retry_file.exists():
            logger.warning("No retry file found")
            return {"processed": 0, "failed": 0, "skipped": 0}
        
        import json
        with open(retry_file, "r", encoding="utf-8") as f:
            retry_items = json.load(f)
        
        urls_to_process = []
        for item in retry_items:
            data = item.get("data", {})
            sku = data.get("sku", "")
            url = data.get("url", "")
            if sku:
                urls_to_process.append({"sku": sku, "url": url, "lastmod": ""})
        
        logger.info(f"Found {len(urls_to_process)} items to retry")
    else:
        # Regular processing of unprocessed items
        urls_to_process = sitemap_parser.get_unprocessed_urls(processed_skus)
    
    # Apply skip and limit
    total_urls = len(urls_to_process)
    if args.skip > 0:
        urls_to_process = urls_to_process[args.skip:]
    if args.limit and args.limit > 0:
        urls_to_process = urls_to_process[:args.limit]
    
    logger.info(f"Processing {len(urls_to_process)} products (skip={args.skip}, limit={args.limit})")
    
    # Load checkpoint if exists
    checkpoint = load_checkpoint("scrape")
    start_idx = 0
    if checkpoint and not args.sku and not args.retry:
        start_idx = int(checkpoint.get("current_position", 0))
        if start_idx > 0:
            logger.info(f"Resuming from checkpoint: position {start_idx}")
    
    # Initialize statistics
    stats = {
        "total": total_urls,
        "processed": 0,
        "failed": 0,
        "skipped": start_idx,
    }
    
    # Process products in batches
    batch_size = args.batch_size
    products_to_save = []
    
    try:
        for i, url_info in enumerate(urls_to_process[start_idx:], start=start_idx):
            sku = url_info.get("sku", "")
            url = url_info.get("url", "")
            
            if not sku:
                logger.warning(f"Skipping item without SKU: {url}")
                stats["skipped"] += 1
                continue
            
            try:
                # Process the product
                product_data = product_scraper.process_product(sku, url)
                
                if product_data:
                    products_to_save.append(product_data)
                    stats["processed"] += 1
                else:
                    stats["failed"] += 1
                
                # Save products to database in batches
                if len(products_to_save) >= batch_size:
                    db.insert_products(products_to_save)
                    products_to_save = []
                
                # Create checkpoint every 10 products
                if i % 10 == 0:
                    create_checkpoint(i, len(urls_to_process), "scrape")
                
                # Display progress
                progress = (i + 1) / len(urls_to_process) * 100
                logger.info(f"Progress: {i+1}/{len(urls_to_process)} ({progress:.1f}%) - SKU: {sku}")
                
            except Exception as e:
                logger.error(f"Error processing SKU {sku}: {e}")
                stats["failed"] += 1
    
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
    
    finally:
        # Save any remaining products
        if products_to_save:
            db.insert_products(products_to_save)
        
        # Save statistics
        db.save_stats(stats)
        
        # Final checkpoint
        create_checkpoint(stats["processed"] + stats["failed"] + stats["skipped"], 
                         total_urls, "scrape")
        
        # Close database
        db.close()
    
    # Summary
    logger.info(f"Scraping completed: {stats['processed']} processed, {stats['failed']} failed, {stats['skipped']} skipped")
    return stats

def main():
    """
    Main entry point
    """
    # Parse command line arguments
    args = parse_args()
    
    # Set debug mode if requested
    if args.debug:
        logger.setLevel("DEBUG")
    
    # Start time
    start_time = time.time()
    logger.info("PLUS Product Scraper")
    logger.info("-" * 40)
    
    # Initialize cookies
    cookies = cookie_manager.get_cookies()
    logger.info(f"Loaded {len(cookies)} cookies for API requests")
    
    try:
        # Als er een SKU is opgegeven, gebruik deze direct
        if args.sku:
            logger.info(f"Processing single SKU: {args.sku}")
            product_scraper = ProductScraper()
            product_data = product_scraper.process_product(args.sku)
            
            if product_data:
                # Sla het product op in de database
                db = ProductDatabase()
                db.insert_product(product_data)
                db.close()
                logger.info(f"Successfully processed SKU {args.sku}")
            else:
                logger.error(f"Failed to process SKU {args.sku}")
                
        else:
            # Run the normal requested tasks
            if args.sitemap or args.all:
                product_urls = sitemap_task(args)
            else:
                product_urls = None
            
            if args.scrape or args.all or args.retry:
                stats = scrape_task(args, product_urls)
    
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    # End time and summary
    elapsed_time = time.time() - start_time
    logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
    return 0

if __name__ == "__main__":
    sys.exit(main())
