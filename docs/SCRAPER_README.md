# PLUS Product Scraper

A scalable scraper for collecting product information from PLUS.nl, including nutritional values.

## Features

- **Sitemap Crawler**: Parses the sitemap of PLUS.nl to collect all product URLs
- **Product Scraper**: Retrieves detailed product information via the PLUS API
- **JSON Database**: Data storage with TinyDB for easy querying
- **Proxy Rotation**: Supports multiple proxy solutions for scalability
- **Error Handling**: Exponential backoff and retry mechanisms

## Installation

1. Clone the repository or download the source code.
2. Create a virtual Python environment (recommended).
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Adjust the `.env` file with the correct settings. See `.env.example` for a template.

## Usage

The scraper has several options:

- **`--sitemap`**: Analyze and cache the sitemap.
- **`--scrape`**: Scrape product details from collected URLs.
- **`--all`**: Run the full pipeline.
- **`--sku <ID>`**: Scrape a specific product.
- **`--limit <N>`**: Limit the number of products.

## Project Structure

```
scraper/
├── main.py           # Main program
├── sitemap_parser.py # Sitemap processing
├── product_scraper.py # Product scraping
├── database.py       # TinyDB database management
├── proxy_manager.py  # Proxy rotation
├── cookie_manager.py # Cookie management
├── utils.py          # Helper functions
├── requirements.txt  # Package requirements
├── .env.example      # Configuration template
└── data/             # Data storage
```

## License

This project is available under the MIT license.

## Disclaimer

This scraper is for educational purposes only. Use according to the website's terms of use.
