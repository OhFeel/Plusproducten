"""
app.py - Flask web application for PLUS product data analysis
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for
import plotly
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from tinydb import TinyDB, Query

# Initialize Flask app
app = Flask(__name__)

# Path to the data directory
DATA_DIR = Path("../data")
DB_PATH = DATA_DIR / "db.json"

# Load the database
db = TinyDB(DB_PATH)
products_table = db.table('products')
nutrients_table = db.table('nutrients')

# Load all products into a pandas DataFrame
def load_products():
    """Load products from database into a pandas DataFrame"""
    products = products_table.all()
    df = pd.DataFrame(products)
    
    # Convert price to float
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    
    return df

# Load all nutrients into a pandas DataFrame
def load_nutrients():
    """Load nutrients from database into a pandas DataFrame"""
    nutrients = nutrients_table.all()
    df = pd.DataFrame(nutrients)
    
    # Convert value to float
    if 'value' in df.columns:
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    return df

# Generate insights about the products
def generate_insights():
    """Generate various insights about the products"""
    df_products = load_products()
    df_nutrients = load_nutrients()
    
    if df_products.empty:
        return {
            "error": "No products found in the database. Please scrape some products first."
        }
    
    # Merge products and nutrients
    if not df_nutrients.empty:
        df_merged = pd.merge(df_nutrients, df_products, left_on='sku', right_on='sku')
    else:
        df_merged = None
    
    insights = {
        "total_products": len(df_products),
        "total_brands": len(df_products['brand'].dropna().unique()),
        "avg_price": df_products['price'].mean(),
        "price_range": (df_products['price'].min(), df_products['price'].max()),
    }
    
    # Most common brands
    if 'brand' in df_products.columns:
        brand_counts = df_products['brand'].value_counts().head(10)
        insights["top_brands"] = [{"name": brand, "count": count} for brand, count in brand_counts.items()]
    
    # Protein insights (if available)
    if df_merged is not None:
        protein_df = df_merged[df_merged['name'] == 'Eiwitten']
        
        if not protein_df.empty:
            protein_df['protein_per_price'] = pd.to_numeric(protein_df['value'], errors='coerce') / pd.to_numeric(protein_df['price'], errors='coerce')
            
            # Best protein sources
            best_protein = protein_df.sort_values('value', ascending=False).head(10)
            insights["best_protein_sources"] = [
                {
                    "sku": row["sku"],
                    "name": df_products[df_products["sku"] == row["sku"]]["name"].values[0] if not df_products[df_products["sku"] == row["sku"]].empty else "Unknown",
                    "protein_per_100g": row["value"],
                    "price": row["price"]
                } for _, row in best_protein.iterrows()
            ]
            
            # Best protein value (protein per price)
            best_protein_value = protein_df.sort_values('protein_per_price', ascending=False).head(10)
            insights["best_protein_value"] = [
                {
                    "sku": row["sku"],
                    "name": df_products[df_products["sku"] == row["sku"]]["name"].values[0] if not df_products[df_products["sku"] == row["sku"]].empty else "Unknown",
                    "protein_per_price": row["protein_per_price"],
                    "protein_per_100g": row["value"],
                    "price": row["price"]
                } for _, row in best_protein_value.iterrows()
            ]
    
    # Alcohol insights (if available)
    alcohol_products = df_products[df_products['ingredients'].str.contains('alcohol', case=False, na=False)]
    if not alcohol_products.empty:
        alcohol_products = alcohol_products.sort_values('price')
        insights["cheapest_alcohol"] = [
            {
                "sku": row["sku"],
                "name": row["name"],
                "price": row["price"]
            } for _, row in alcohol_products.head(10).iterrows()
        ]
    
    return insights

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/insights')
def get_insights():
    """API endpoint to get product insights"""
    return jsonify(generate_insights())

@app.route('/api/price_distribution')
def price_distribution():
    """API endpoint to get price distribution data"""
    df = load_products()
    
    if df.empty or 'price' not in df.columns:
        return jsonify({"error": "No price data available"})
    
    # Create histogram data
    fig = px.histogram(df, x="price", nbins=20, title="Product Price Distribution")
    fig.update_layout(bargap=0.1)
    
    # Convert to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return jsonify({"chart": graphJSON})

@app.route('/api/brand_distribution')
def brand_distribution():
    """API endpoint to get brand distribution data"""
    df = load_products()
    
    if df.empty or 'brand' not in df.columns:
        return jsonify({"error": "No brand data available"})
    
    # Count brands
    brand_counts = df['brand'].value_counts().head(15)
    
    # Create bar chart
    fig = px.bar(
        x=brand_counts.index, 
        y=brand_counts.values,
        title="Top 15 Brands by Number of Products",
        labels={"x": "Brand", "y": "Number of Products"}
    )
    
    # Convert to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return jsonify({"chart": graphJSON})

@app.route('/api/protein_comparison')
def protein_comparison():
    """API endpoint to get protein comparison data"""
    df_products = load_products()
    df_nutrients = load_nutrients()
    
    if df_products.empty or df_nutrients.empty:
        return jsonify({"error": "Not enough data available"})
    
    # Find protein data
    protein_data = df_nutrients[df_nutrients['name'] == 'Eiwitten']
    
    if protein_data.empty:
        return jsonify({"error": "No protein data available"})
    
    # Merge with product data
    protein_df = pd.merge(protein_data, df_products, left_on='sku', right_on='sku')
    protein_df = protein_df.sort_values(by='value', ascending=False).head(15)
    
    # Create bar chart
    fig = px.bar(
        protein_df,
        x='name_y',  # Product name
        y='value',   # Protein value
        title="Top 15 Products by Protein Content (per 100g)",
        labels={"name_y": "Product", "value": "Protein (g)"},
        color='value',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig.update_layout(xaxis_tickangle=-45)
    
    # Convert to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return jsonify({"chart": graphJSON})

@app.route('/api/wordcloud')
def generate_wordcloud():
    """API endpoint to generate a wordcloud of ingredients"""
    df = load_products()
    
    if df.empty or 'ingredients' not in df.columns:
        return jsonify({"error": "No ingredient data available"})
    
    # Combine all ingredients
    text = ' '.join(df['ingredients'].dropna().astype(str))
    
    # Define stopwords
    dutch_stopwords = set(STOPWORDS)
    dutch_stopwords.update(['bevat', 'kan', 'bevatten', 'en', 'van', 'het', 'de', 'met'])
    
    # Generate wordcloud
    wordcloud = WordCloud(width=800, height=400, 
                          background_color='white',
                          stopwords=dutch_stopwords,
                          max_words=100,
                          colormap='viridis',
                          contour_width=1,
                          contour_color='steelblue').generate(text)
    
    # Save wordcloud to a BytesIO object
    img = BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    
    # Encode the image to base64
    img_b64 = base64.b64encode(img.getvalue()).decode()
    
    return jsonify({"image": f"data:image/png;base64,{img_b64}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
