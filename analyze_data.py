"""
analyze_data.py - PLUS Product Data Analyzer
Generates static visualizations and analysis reports from scraped data
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from collections import Counter
import logging

# Optional imports with graceful fallback
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False
    print("⚠️  WordCloud not available. Install with: pip install wordcloud")

# Configure matplotlib to use non-interactive backend
import matplotlib
matplotlib.use('Agg')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class PLUSDataAnalyzer:
    """
    Analyzes scraped PLUS product data and generates visualizations
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.products_dir = self.data_dir / "products"
        self.output_dir = self.data_dir / "analysis"
        self.images_dir = self.output_dir / "images"
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.images_dir.mkdir(exist_ok=True, parents=True)
        
        # Data containers
        self.products_df = None
        self.nutrients_df = None
        
        # Style configuration
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        logger.info(f"Analyzer initialized - Output directory: {self.output_dir}")
    
    def load_data(self) -> bool:
        """Load product data from JSON files"""
        if not self.products_dir.exists():
            logger.error(f"Products directory not found: {self.products_dir}")
            return False
        
        product_files = list(self.products_dir.glob("*.json"))
        if not product_files:
            logger.error(f"No product JSON files found in {self.products_dir}")
            return False
        
        logger.info(f"Loading {len(product_files)} product files...")
        
        products_data = []
        nutrients_data = []
        
        for file_path in product_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    product = json.load(f)
                    
                    # Extract basic product info
                    product_info = {
                        'sku': product.get('sku', ''),
                        'name': product.get('name', ''),
                        'brand': product.get('brand', ''),
                        'price': self._parse_price(product.get('price', '0')),
                        'category': product.get('category', ''),
                        'ingredients': product.get('ingredients', ''),
                        'allergens': product.get('allergens', ''),
                        'alcohol_percentage': self._parse_float(product.get('alcohol_percentage', '0'))
                    }
                    products_data.append(product_info)
                    
                    # Extract nutrients
                    nutrients = product.get('nutrients', [])
                    for nutrient in nutrients:
                        nutrient_info = {
                            'sku': product.get('sku', ''),
                            'name': nutrient.get('name', ''),
                            'value': self._parse_float(nutrient.get('value', '0')),
                            'unit': nutrient.get('unit', ''),
                            'per_100g': self._parse_float(nutrient.get('per_100g', '0'))
                        }
                        nutrients_data.append(nutrient_info)
                        
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                continue
        
        # Create DataFrames
        self.products_df = pd.DataFrame(products_data)
        self.nutrients_df = pd.DataFrame(nutrients_data)
        
        logger.info(f"Loaded {len(self.products_df)} products and {len(self.nutrients_df)} nutrient entries")
        return True
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float"""
        if not price_str:
            return 0.0
        try:
            # Remove currency symbols and convert
            clean_price = str(price_str).replace('€', '').replace(',', '.').strip()
            return float(clean_price)
        except:
            return 0.0
    
    def _parse_float(self, value: Any) -> float:
        """Safely parse value to float"""
        if not value:
            return 0.0
        try:
            return float(str(value).replace(',', '.'))
        except:
            return 0.0
    
    def generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        if self.products_df is None or self.products_df.empty:
            return {}
        
        # Filter out products with no price
        priced_products = self.products_df[self.products_df['price'] > 0]
        
        stats = {
            'total_products': len(self.products_df),
            'total_brands': len(self.products_df['brand'].dropna().unique()),
            'avg_price': priced_products['price'].mean(),
            'min_price': priced_products['price'].min(),
            'max_price': priced_products['price'].max(),
            'median_price': priced_products['price'].median(),
            'total_categories': len(self.products_df['category'].dropna().unique()),
        }
        
        return stats
    
    def create_price_distribution_chart(self) -> str:
        """Create price distribution histogram"""
        if self.products_df is None or self.products_df.empty:
            return ""
        
        plt.figure(figsize=(12, 8))
        
        # Filter out extreme outliers for better visualization
        priced_products = self.products_df[self.products_df['price'] > 0]
        Q1 = priced_products['price'].quantile(0.25)
        Q3 = priced_products['price'].quantile(0.75)
        IQR = Q3 - Q1
        filtered_prices = priced_products[
            (priced_products['price'] >= Q1 - 1.5 * IQR) & 
            (priced_products['price'] <= Q3 + 1.5 * IQR)
        ]['price']
        
        plt.hist(filtered_prices, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('PLUS Product Price Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Price (€)', fontsize=12)
        plt.ylabel('Number of Products', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Add statistics text
        avg_price = filtered_prices.mean()
        plt.axvline(avg_price, color='red', linestyle='--', linewidth=2, label=f'Average: €{avg_price:.2f}')
        plt.legend()
        
        output_path = self.images_dir / "price_distribution.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Price distribution chart saved to {output_path}")
        return str(output_path)
    
    def create_brand_analysis_chart(self) -> str:
        """Create top brands bar chart"""
        if self.products_df is None or self.products_df.empty:
            return ""
        
        # Get top 15 brands by product count
        brand_counts = self.products_df['brand'].value_counts().head(15)
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(range(len(brand_counts)), brand_counts.values, color='lightcoral')
        plt.title('Top 15 Brands by Product Count', fontsize=16, fontweight='bold')
        plt.xlabel('Brand', fontsize=12)
        plt.ylabel('Number of Products', fontsize=12)
        plt.xticks(range(len(brand_counts)), brand_counts.index, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.grid(True, alpha=0.3, axis='y')
        
        output_path = self.images_dir / "brand_analysis.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Brand analysis chart saved to {output_path}")
        return str(output_path)
    
    def create_protein_analysis(self) -> str:
        """Create protein content analysis"""
        if self.nutrients_df is None or self.nutrients_df.empty:
            return ""
        
        # Filter for protein data
        protein_data = self.nutrients_df[
            self.nutrients_df['name'].str.contains('eiwit|protein', case=False, na=False)
        ]
        
        if protein_data.empty:
            logger.warning("No protein data found")
            return ""
        
        # Merge with product data
        protein_products = protein_data.merge(
            self.products_df[['sku', 'name', 'price']], 
            on='sku', 
            how='left'
        )
        
        # Filter for products with price and protein data
        valid_data = protein_products[
            (protein_products['per_100g'] > 0) & 
            (protein_products['price'] > 0)
        ].copy()
        
        if valid_data.empty:
            logger.warning("No valid protein/price data found")
            return ""
        
        # Calculate protein per euro
        valid_data['protein_per_euro'] = valid_data['per_100g'] / valid_data['price']
        
        # Create subplot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Top 10 highest protein products
        top_protein = valid_data.nlargest(10, 'per_100g')
        ax1.barh(range(len(top_protein)), top_protein['per_100g'], color='lightgreen')
        ax1.set_yticks(range(len(top_protein)))
        ax1.set_yticklabels([name[:30] + '...' if len(name) > 30 else name 
                            for name in top_protein['name']], fontsize=8)
        ax1.set_xlabel('Protein (g per 100g)')
        ax1.set_title('Top 10 Products by Protein Content')
        ax1.invert_yaxis()
        
        # Top 10 best protein value (protein per euro)
        top_value = valid_data.nlargest(10, 'protein_per_euro')
        ax2.barh(range(len(top_value)), top_value['protein_per_euro'], color='lightblue')
        ax2.set_yticks(range(len(top_value)))
        ax2.set_yticklabels([name[:30] + '...' if len(name) > 30 else name 
                            for name in top_value['name']], fontsize=8)
        ax2.set_xlabel('Protein per Euro (g/€)')
        ax2.set_title('Top 10 Products by Protein Value')
        ax2.invert_yaxis()
        
        output_path = self.images_dir / "protein_analysis.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Protein analysis chart saved to {output_path}")
        return str(output_path)
    
    def create_ingredients_wordcloud(self) -> str:
        """Create a word cloud from ingredients"""
        if not WORDCLOUD_AVAILABLE:
            logger.warning("WordCloud not available - skipping ingredients wordcloud")
            return ""
            
        if self.products_df is None or self.products_df.empty:
            return ""
        
        # Combine all ingredients
        all_ingredients = ' '.join(self.products_df['ingredients'].dropna().astype(str))
        
        if not all_ingredients.strip():
            logger.warning("No ingredients data found")
            return ""
        
        # Custom stopwords for Dutch
        dutch_stopwords = {
            'en', 'van', 'de', 'het', 'een', 'in', 'met', 'voor', 'uit', 'op', 'aan', 'bij',
            'water', 'zout', 'suiker', 'kan', 'bevatten', 'sporen', 'e', 'mg', 'g', 'kg',
            'bevat', 'ingrediënten', 'ingredienten', 'procent', '%'
        }
        
        try:
            wordcloud = WordCloud(
                width=1200, 
                height=600,
                background_color='white',
                stopwords=dutch_stopwords,
                max_words=100,
                colormap='viridis',
                collocations=False
            ).generate(all_ingredients)
            
            plt.figure(figsize=(15, 8))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('Most Common Ingredients in PLUS Products', fontsize=16, fontweight='bold')
            
            output_path = self.images_dir / "ingredients_wordcloud.png"
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Ingredients wordcloud saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating wordcloud: {e}")
            return ""
    
    def create_alcohol_analysis(self) -> str:
        """Create alcohol products analysis"""
        if self.products_df is None or self.products_df.empty:
            return ""
        
        # Filter alcohol products
        alcohol_products = self.products_df[
            (self.products_df['alcohol_percentage'] > 0) & 
            (self.products_df['price'] > 0)
        ].copy()
        
        if alcohol_products.empty:
            logger.warning("No alcohol products found")
            return ""
        
        # Sort by price
        cheapest_alcohol = alcohol_products.nsmallest(15, 'price')
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(range(len(cheapest_alcohol)), cheapest_alcohol['price'], color='orange')
        plt.title('15 Cheapest Alcoholic Products', fontsize=16, fontweight='bold')
        plt.xlabel('Product', fontsize=12)
        plt.ylabel('Price (€)', fontsize=12)
        plt.xticks(range(len(cheapest_alcohol)), 
                  [name[:20] + '...' if len(name) > 20 else name 
                   for name in cheapest_alcohol['name']], 
                  rotation=45, ha='right')
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'€{height:.2f}', ha='center', va='bottom', fontsize=8)
        
        plt.grid(True, alpha=0.3, axis='y')
        
        output_path = self.images_dir / "alcohol_analysis.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Alcohol analysis chart saved to {output_path}")
        return str(output_path)
    
    def generate_analysis_report(self) -> str:
        """Generate a comprehensive analysis report"""
        if not self.load_data():
            return ""
        
        logger.info("Starting comprehensive analysis...")
        
        # Generate summary stats
        stats = self.generate_summary_stats()
        
        # Create all visualizations
        charts = {
            'price_distribution': self.create_price_distribution_chart(),
            'brand_analysis': self.create_brand_analysis_chart(),
            'protein_analysis': self.create_protein_analysis(),
            'ingredients_wordcloud': self.create_ingredients_wordcloud(),
            'alcohol_analysis': self.create_alcohol_analysis()
        }
        
        # Create summary report
        report = {
            'summary_statistics': stats,
            'generated_charts': {k: v for k, v in charts.items() if v},
            'analysis_date': pd.Timestamp.now().isoformat(),
            'total_files_processed': len(list(self.products_dir.glob("*.json")))
        }
        
        # Save report as JSON
        report_path = self.output_dir / "analysis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis report saved to {report_path}")
        
        # Create README for analysis
        self._create_analysis_readme(stats, charts)
        
        return str(report_path)
    
    def _create_analysis_readme(self, stats: Dict[str, Any], charts: Dict[str, str]) -> None:
        """Create a README file for the analysis results"""
        readme_content = f"""# PLUS Product Data Analysis Results

## Summary Statistics

- **Total Products**: {stats.get('total_products', 0):,}
- **Total Brands**: {stats.get('total_brands', 0):,}
- **Total Categories**: {stats.get('total_categories', 0):,}
- **Average Price**: €{stats.get('avg_price', 0):.2f}
- **Price Range**: €{stats.get('min_price', 0):.2f} - €{stats.get('max_price', 0):.2f}
- **Median Price**: €{stats.get('median_price', 0):.2f}

## Generated Visualizations

"""
        
        chart_descriptions = {
            'price_distribution': 'Price Distribution - Histogram showing the distribution of product prices',
            'brand_analysis': 'Brand Analysis - Top 15 brands by product count',
            'protein_analysis': 'Protein Analysis - Products with highest protein content and best protein value',
            'ingredients_wordcloud': 'Ingredients Word Cloud - Most common ingredients across all products',
            'alcohol_analysis': 'Alcohol Analysis - Cheapest alcoholic products'
        }
        
        for chart_key, description in chart_descriptions.items():
            if charts.get(chart_key):
                filename = Path(charts[chart_key]).name
                readme_content += f"- **{description}**\n  ![{description}](images/{filename})\n\n"
        
        readme_content += f"""
## Analysis Details

- **Analysis Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Data Source**: Individual product JSON files from PLUS.nl scraper
- **Visualization Tools**: Python (matplotlib, seaborn, wordcloud)

## Files Generated

- `analysis_report.json` - Complete analysis data in JSON format
- `images/` - Directory containing all generated charts and visualizations
"""
        
        readme_path = self.output_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Analysis README saved to {readme_path}")


def main():
    """Main function to run the analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PLUS Product Data Analyzer")
    parser.add_argument("--data-dir", default="data", help="Directory containing product JSON files")
    parser.add_argument("--output-dir", help="Output directory for analysis results")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    data_dir = args.data_dir
    if args.output_dir:
        analyzer = PLUSDataAnalyzer(data_dir)
        analyzer.output_dir = Path(args.output_dir)
        analyzer.images_dir = analyzer.output_dir / "images"
        analyzer.output_dir.mkdir(exist_ok=True, parents=True)
        analyzer.images_dir.mkdir(exist_ok=True, parents=True)
    else:
        analyzer = PLUSDataAnalyzer(data_dir)
    
    # Run analysis
    report_path = analyzer.generate_analysis_report()
    
    if report_path:
        print(f"\n✅ Analysis completed successfully!")
        print(f"📊 Report saved to: {report_path}")
        print(f"🖼️  Images saved to: {analyzer.images_dir}")
        print(f"📖 README available at: {analyzer.output_dir / 'README.md'}")
    else:
        print("❌ Analysis failed. Check the logs for details.")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
