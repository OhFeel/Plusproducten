"""
data_processor.py - Preprocess scraped product data for analysis
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tinydb import TinyDB, Query

class ProductDataProcessor:
    """
    Process and analyze PLUS product data
    """
    def __init__(self, db_path=None):
        """Initialize with path to TinyDB database"""
        if db_path is None:
            # Use absolute path to avoid working directory issues
            script_dir = Path(__file__).parent.absolute() 
            db_path = script_dir.parent / "data" / "db.json"
        
        self.db_path = db_path
        
        # Check if database exists - if not, try to create it
        if not self.db_path.exists():
            print(f"Database not found at {self.db_path}. Attempting to create it...")
            import subprocess
            import sys
            try:
                script_dir = Path(__file__).parent.absolute()
                migrate_script = script_dir.parent / "migrate_db.py"
                subprocess.run([sys.executable, str(migrate_script)], check=True)
            except subprocess.CalledProcessError:
                print("Warning: Could not create database from product files.")
                
        # Initialize database connection
        self.db = TinyDB(db_path) if self.db_path.exists() else TinyDB(str(self.db_path))
        self.products_table = self.db.table('products')
        self.nutrients_table = self.db.table('nutrients')
        
        # Cache for dataframes
        self._df_products = None
        self._df_nutrients = None
    
    @property
    def products_df(self):
        """Get products as DataFrame"""
        if self._df_products is None:
            products = self.products_table.all()
            self._df_products = pd.DataFrame(products) if products else pd.DataFrame()
            
            # Convert price to numeric
            if 'price' in self._df_products.columns:
                self._df_products['price'] = pd.to_numeric(self._df_products['price'], errors='coerce')
        
        return self._df_products
    
    @property
    def nutrients_df(self):
        """Get nutrients as DataFrame"""
        if self._df_nutrients is None:
            nutrients = self.nutrients_table.all()
            self._df_nutrients = pd.DataFrame(nutrients) if nutrients else pd.DataFrame()
            
            # Convert value to numeric
            if 'value' in self._df_nutrients.columns:
                self._df_nutrients['value'] = pd.to_numeric(self._df_nutrients['value'], errors='coerce')
        
        return self._df_nutrients
    
    def get_merged_data(self, nutrient_name=None):
        """Get merged product and nutrient data"""
        if self.products_df.empty or self.nutrients_df.empty:
            return pd.DataFrame()
        
        if nutrient_name:
            nutrients = self.nutrients_df[self.nutrients_df['name'] == nutrient_name]
            return pd.merge(nutrients, self.products_df, left_on='sku', right_on='sku')
        else:
            return pd.merge(self.nutrients_df, self.products_df, left_on='sku', right_on='sku')
    
    def analyze_nutrients(self):
        """Analyze nutrient content across products"""
        if self.nutrients_df.empty:
            return {}
        
        # Group by nutrient name and calculate stats
        grouped = self.nutrients_df.groupby('name')
        
        results = {}
        for name, group in grouped:
            results[name] = {
                'count': len(group),
                'mean': group['value'].mean(),
                'min': group['value'].min(),
                'max': group['value'].max(),
            }
        
        return results
    
    def find_best_protein_products(self, n=10):
        """Find products with highest protein content"""
        protein_df = self.get_merged_data('Eiwitten')
        
        if protein_df.empty:
            return []
        
        return protein_df.sort_values('value', ascending=False).head(n)
    
    def find_best_protein_value(self, n=10):
        """Find products with best protein content per price"""
        protein_df = self.get_merged_data('Eiwitten')
        
        if protein_df.empty or 'price' not in protein_df.columns:
            return []
        
        # Calculate protein per price ratio
        protein_df['protein_per_price'] = protein_df['value'] / protein_df['price']
        
        return protein_df.sort_values('protein_per_price', ascending=False).head(n)
    
    def find_cheapest_alcohol(self, n=10):
        """Find the cheapest alcohol products"""
        if self.products_df.empty:
            return []
        
        # Look for alcohol in product name or ingredients
        alcohol_pattern = r'alcohol|bier|wijn|jenever|whiskey|vodka|rum|gin'
        alcohol_products = self.products_df[
            self.products_df['name'].str.contains(alcohol_pattern, case=False, na=False) |
            self.products_df['ingredients'].str.contains(alcohol_pattern, case=False, na=False)
        ]
        
        if alcohol_products.empty:
            return []
        
        return alcohol_products.sort_values('price').head(n)
    
    def analyze_ingredients(self):
        """Analyze common ingredients across products"""
        if self.products_df.empty or 'ingredients' not in self.products_df.columns:
            return {}
        
        # Extract ingredients and split
        all_ingredients = []
        for ingr in self.products_df['ingredients'].dropna():
            ingredients = str(ingr).lower()
            ingredients = ingredients.replace(',', ' ').replace('(', ' ').replace(')', ' ')
            all_ingredients.extend([ing.strip() for ing in ingredients.split() if len(ing.strip()) > 3])
        
        # Count occurrences
        from collections import Counter
        ingredients_counter = Counter(all_ingredients)
        
        # Return top ingredients
        return dict(ingredients_counter.most_common(30))
    
    def analyze_brands(self):
        """Analyze brands by product count and average price"""
        if self.products_df.empty or 'brand' not in self.products_df.columns:
            return {}
        
        # Group by brand
        grouped = self.products_df.groupby('brand')
        
        results = {}
        for brand, group in grouped:
            if isinstance(brand, str) and len(brand) > 0:
                results[brand] = {
                    'count': len(group),
                    'avg_price': group['price'].mean() if 'price' in group else None,
                }
        
        return {k: v for k, v in sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)}
    
    def export_analysis_to_json(self, output_path=None):
        """Export complete analysis to JSON file"""
        if output_path is None:
            output_path = Path("../data/analysis/product_analysis.json")
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate all analysis
        analysis = {
            'summary': {
                'total_products': len(self.products_df),
                'total_brands': len(self.products_df['brand'].dropna().unique()) if 'brand' in self.products_df.columns else 0,
                'avg_price': float(self.products_df['price'].mean()) if 'price' in self.products_df.columns else None,
                'price_range': [float(self.products_df['price'].min()), float(self.products_df['price'].max())] if 'price' in self.products_df.columns else [None, None],
            },
            'nutrients': self.analyze_nutrients(),
            'brands': self.analyze_brands(),
            'best_protein': self.find_best_protein_products(20).to_dict(orient='records') if not self.products_df.empty else [],
            'best_protein_value': self.find_best_protein_value(20).to_dict(orient='records') if not self.products_df.empty else [],
            'cheapest_alcohol': self.find_cheapest_alcohol(20).to_dict(orient='records') if not self.products_df.empty else [],
            'common_ingredients': self.analyze_ingredients()
        }
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return output_path

if __name__ == "__main__":
    processor = ProductDataProcessor()
    output_path = processor.export_analysis_to_json()
    print(f"Analysis exported to {output_path}")
    
    # Print summary stats
    print("\nSummary statistics:")
    print(f"- Total products: {processor.products_df.shape[0]}")
    
    if not processor.products_df.empty and 'price' in processor.products_df.columns:
        print(f"- Average price: €{processor.products_df['price'].mean():.2f}")
        print(f"- Price range: €{processor.products_df['price'].min():.2f} - €{processor.products_df['price'].max():.2f}")
        
    # Protein info
    protein_products = processor.find_best_protein_products(5)
    if not protein_products.empty:
        print("\nTop 5 products with highest protein content:")
        for i, (_, row) in enumerate(protein_products.iterrows(), 1):
            print(f"{i}. {row['name_y']} - {row['value']}g per 100g - €{row['price']:.2f}")
