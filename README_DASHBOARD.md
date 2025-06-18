# PLUS Product Analysis Interactive Dashboard

This interactive web dashboard analyzes product data from PLUS supermarket to discover insights about nutrition, prices, and more. The dashboard includes hover functionality for products, interactive charts, and a modern user interface.

## Features

- **Interactive Visualizations**: Dynamic charts with hover functionality to show detailed product information
- **Product Images**: Visualizations include product images for a better user experience
- **Search Functionality**: Search for products by name, brand, or ingredient
- **Responsive Design**: Mobile-friendly interface that adapts to different screen sizes
- **Nutritional Insights**: Discover products with highest calories, best protein value, and more
- **Brand Comparisons**: Compare different brands based on nutritional content
- **Allergen Analysis**: See the most common allergens across products

## Getting Started

### Prerequisites

Make sure you have Python 3.7+ installed. All required dependencies are listed in the `requirements.txt` file.

### Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Dashboard

Launch the interactive dashboard with:

```bash
python run_dashboard.py
```

The dashboard will be accessible at: http://127.0.0.1:5000

## Dashboard Sections

1. **Top Calorie Products**: Bar chart showing products with the highest calorie content
2. **Best Protein Value**: Bar chart showing products offering the best protein per Euro
3. **Nutritional Composition**: Bubble chart showing the relationship between carbs, fat, and protein
4. **Brand Comparison**: Comparison of brands by average calories and protein
5. **Protein Source Comparison**: Comparison of protein content across different food sources
6. **Common Allergens**: Most common allergens across all products
7. **Category Breakdown**: Distribution of products by category
8. **Fat vs Protein Analysis**: Scatter plot of fat vs. protein content
9. **Sugar Content by Category**: Average sugar content by product category
10. **Price Distribution**: Histogram of product prices
11. **Product Search**: Search functionality to find specific products

## Technical Details

This dashboard is built using:

- **Flask**: Web server framework
- **Dash**: Interactive visualization framework built on Plotly
- **Plotly**: Interactive charting library
- **Pandas**: Data manipulation and analysis
- **Bootstrap**: Responsive styling framework

## Notes

- Product images are downloaded and cached for better performance
- The analysis normalizes prices to ensure accurate comparisons (per kg/liter or per piece)
- The dashboard allows zooming, panning, and exporting of visualizations
