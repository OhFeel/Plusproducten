# PLUS Products Analysis

This project analyzes product data from the PLUS supermarket chain to discover insights about nutrition, prices, and more. The analysis includes visualization of products with the most calories, best protein value, nutritional composition, and other interesting metrics.

## Features

- **Product Calorie Rankings**: Discover the products with the highest calorie content
- **Protein Price Ratio**: Find products offering the best value for protein content
- **Interactive Nutritional Composition**: Explore the relationship between carbs, fat, and protein 
- **Brand Comparisons**: Compare different brands based on nutritional content
- **Allergen Analysis**: See the most common allergens across products
- **Many More Insights**: Including sugar content by category, fat vs. protein analysis, and price distribution

## Getting Started

### Prerequisites

Make sure you have Python 3.7+ installed. All required dependencies are listed in the `requirements.txt` file.

### Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Jupyter Notebook (Interactive)

For an interactive experience with data visualizations:

1. Open the Jupyter Notebook:

```bash
jupyter notebook product_analysis.ipynb
```

2. Run each cell in sequence to generate visualizations and insights.

### Python Script (Batch Processing)

To run the entire analysis in batch mode and generate all visualizations:

```bash
python analyze_products.py
```

This will:
- Load all product data from the `products` folder
- Process and analyze the nutritional information
- Generate visualizations with product images
- Create a comprehensive dashboard
- Export processed data to CSV for further analysis

## Visualizations Generated

The analysis generates several visualizations:

1. `top_calories_products.png` - Bar chart showing products with the highest calorie content
2. `best_protein_value.png` - Bar chart showing products offering the best protein per Euro
3. `nutrition_bubble_chart.png` - Bubble chart showing the relationship between carbs, fat, and protein
4. `brand_comparison.png` - Comparison of brands by average calories and protein
5. `common_allergens.png` - Most common allergens across all products
6. `fat_protein_scatter.png` - Scatter plot of fat vs. protein content by product type
7. `sugar_by_category.png` - Average sugar content by product category
8. `price_distribution.png` - Histogram of product prices
9. `product_analysis_dashboard.png` - Comprehensive dashboard combining key insights

## Data Structure

The analysis uses product data stored as JSON files with the following structure:

```json
{
  "sku": "",
  "name": "Product Name",
  "brand": "Brand",
  "price": "1.99",
  "base_unit_price": "1.00",
  "image_url": "https://example.com/image.png",
  "ingredients": "Ingredient list",
  "allergens": "Allergen information",
  "nutrients_base": {
    "unit": "gram",
    "value": 100
  },
  "nutrients": [
    {
      "name": "Energie KJ",
      "value": "585.0",
      "unit": "kilojoule",
      "parent_code": ""
    },
    ...
  ]
}
```

## Notes

- The analysis normalizes prices by interpreting `base_unit_price` correctly (per kg/liter or per piece)
- Product images are downloaded for visualization purposes
- Some visualizations include only a subset of products to avoid overcrowding
