# 🛒 PLUS Product Analyzer

Een uitgebreide scraper en analyse-tool voor productinformatie van PLUS.nl, inclusief voedingswaarden, prijzen en ingrediënten.

> **⚠️ Belangrijk:** Dit project is bedoeld voor educatieve doeleinden. Zorg ervoor dat je de gebruiksvoorwaarden van PLUS.nl respecteert en gebruik de scraper verantwoordelijk.

> **🔒 Configuratie Vereist:** Dit is een openbare repository. Alle API-sleutels en cookies zijn verwijderd. Zie `SECURITY.md` en `scraper/COOKIES.md` voor configuratie-instructies.

## � Quick Start

```bash
# 1. Clone de repository
git clone https://github.com/your-username/plusproducten.git
cd plusproducten

# 2. Run automatische setup
python setup.py

# 3. Configureer je credentials (zie SECURITY.md)
# Edit scraper/.env met je CSRF token en cookies

# 4. Start scraping
cd scraper
python main.py --all --limit 50

# 5. Genereer analyses en visualisaties
cd ..
python analyze_data.py
```

## �📋 Inhoudsopgave

- [Vereisten voor Gebruik](#vereisten-voor-gebruik)
- [Project Structuur](#project-structuur)
- [Installatie](#installatie)
- [Configuratie](#configuratie)
- [Gebruik](#gebruik)
- [Data Analyse](#data-analyse)
- [Voorbeelden](#voorbeelden)

## 🔑 Vereisten voor Gebruik

**Voordat je begint, heb je nodig:**
- Python 3.8+ en pip
- CSRF token van PLUS.nl (via browser dev tools)
- Geldige cookies voor API toegang

📖 **Lees eerst:** `SECURITY.md` voor volledige setup-instructies

## 📁 Project Structuur

```
plusproducten/
├── scraper/                    # 🕷️ Web scraper
│   ├── main.py                # Hoofd scraper script
│   ├── product_scraper.py     # Product detail scraper
│   ├── sitemap_parser.py      # Sitemap parser
│   ├── cookie_manager.py      # Cookie beheer
│   ├── proxy_manager.py       # Proxy rotatie
│   ├── database.py            # Database beheer
│   ├── utils.py               # Hulpfuncties
│   ├── requirements.txt       # Scraper dependencies
│   ├── .env.example          # Configuratie template
│   ├── COOKIES.md            # Cookie setup gids
│   └── data/                 # Gescrapte data
│       ├── products/         # Product JSON bestanden
│       └── analysis/         # Analyse cache
├── analyze_data.py            # � Data analysescript
├── setup.py                  # 🔧 Automatische setup
├── requirements_analysis.txt  # Analyse dependencies
├── SECURITY.md               # Veiligheid & setup gids
└── README.md                 # Deze documentatie
```

## 🛠️ Installatie

### Optie 1: Automatische Setup (Aanbevolen)

```bash
python setup.py
```

Dit script installeert automatisch alle vereisten en configureert de mappen.

### Optie 2: Handmatige Setup

```bash
# Installeer scraper dependencies
cd scraper
pip install -r requirements.txt

# Installeer analyse dependencies
cd ..
pip install -r requirements_analysis.txt

# Maak configuratie bestand
cp scraper/.env.example scraper/.env
```

Dit project bestaat uit twee hoofdcomponenten:

1. **Product Scraper** - Verzamelt productgegevens van PLUS.nl via de officiële API
2. **Data Analyzer** - Analyseert de verzamelde gegevens met interactieve visualisaties

De tool kan duizenden producten scrapen en biedt inzicht in:
- Voedingswaarden en ingrediënten
- Prijs-kwaliteitsverhouding
- Merkanalyses
- Allergeneninformatie
- En veel meer!

## ✨ Functies

### 🕷️ Web Scraper
- **Sitemap Parsing** - Automatische detectie van alle product-URL's
- **API Integration** - Directe toegang tot de PLUS product-API
- **Proxy Support** - Rotatie voor schaalbaarheid
- **Cookie Management** - Automatisch beheer van sessie-cookies
- **Error Handling** - Robuuste foutafhandeling met retry-mechanismen
- **JSON Database** - Efficiënte opslag met TinyDB

### 📊 Data Analyse
- **Interactieve Visualisaties** - Plotly-gebaseerde grafieken
- **Web Dashboard** - Flask-gebaseerde web-interface
- **Voedingswaarde Analyse** - Protein-per-euro, calorieën, etc.
- **Ingrediënten Wordcloud** - Visuele weergave van populaire ingrediënten
- **Brand Comparison** - Vergelijking tussen verschillende merken
- **Price Distribution** - Prijsverdelingen en trends

## 🚀 Installatie

### Vereisten
- Python 3.8 of hoger
- Windows PowerShell (voor de meegeleverde scripts)

### Stap-voor-stap installatie

1. **Clone het project**
   ```bash
   git clone <repository-url>
   cd plusproducten
   ```

2. **Maak een virtuele omgeving** (aanbevolen)
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Installeer afhankelijkheden**
   ```powershell
   cd scraper
   pip install -r requirements.txt
   pip install -r requirements_analysis.txt
   ```

4. **Configureer omgevingsvariabelen**
   ```powershell
## ⚙️ Configuratie

> **🔑 Vereist:** Voor het gebruik van deze scraper heb je een CSRF token en cookies nodig van PLUS.nl.

### 1. Environment Setup

```bash
# Kopieer de template
cp scraper/.env.example scraper/.env

# Bewerk met je credentials
nano scraper/.env  # of je favoriete editor
```

### 2. Verkrijg CSRF Token

1. Open PLUS.nl in je browser
2. Open Developer Tools (F12)
3. Ga naar Network tab
4. Navigeer naar een product pagina
5. Zoek naar API calls naar `screenservices`
6. Kopieer de `X-CSRFToken` header waarde
7. Plak in je `.env` bestand

### 3. Cookie Setup

Zie `scraper/COOKIES.md` voor gedetailleerde instructies over het instellen van cookies.

## 🚀 Gebruik

### Stap 1: Data Scrapen

```bash
cd scraper

# Scrape eerste 50 producten (voor testen)
python main.py --all --limit 50

# Scrape alle producten (kan lang duren!)
python main.py --all

# Scrape specifiek product
python main.py --sku 553975
```

### Stap 2: Data Analyseren

```bash
cd ..  # Terug naar root directory

# Genereer alle analyses en visualisaties
python analyze_data.py

# Gebruik custom data directory
python analyze_data.py --data-dir scraper/data
```

## 📊 Data Analyse

Het analyse script genereert:

### 📈 Visualisaties
- **Prijsverdeling** - Histogram van productprijzen
- **Merkanalyse** - Top merken per aantal producten  
- **Eiwitanalyse** - Hoogste eiwit content en beste waarde
- **Ingrediënten Wordcloud** - Meest voorkomende ingrediënten
- **Alcohol Analyse** - Goedkoopste alcoholische producten

### 📋 Rapporten
- **JSON Rapport** - Volledige analyse data
- **README** - Overzicht van resultaten met afbeeldingen
- **Statistieken** - Samenvattende statistieken

### Output Structuur
```
data/analysis/
├── README.md              # Analyse overzicht
├── analysis_report.json   # Volledige data
└── images/                # Gegenereerde grafieken
    ├── price_distribution.png
    ├── brand_analysis.png
    ├── protein_analysis.png
    ├── ingredients_wordcloud.png
    └── alcohol_analysis.png
```

## 🎯 Voorbeelden

### Basis Scraping Workflow

```bash
# 1. Setup (eenmalig)
python setup.py

# 2. Configureer credentials
# Edit scraper/.env

# 3. Test met klein aantal
cd scraper
python main.py --all --limit 10

```

## 🔧 Geavanceerde Opties

### Scraper Opties

```bash
cd scraper

# Alle opties tonen
python main.py --help

# Met proxy ondersteuning
USE_PROXY=true python main.py --all

# Specifieke batch grootte
python main.py --all --batch-size 20

# Met custom timeout
REQUEST_TIMEOUT=60 python main.py --all
```

### Analyse Opties

```bash
# Custom output directory
python analyze_data.py --output-dir /path/to/output

# Alleen specifieke analyse
python analyze_data.py --data-dir scraper/data
```

## 📋 Project Structuur

```
plusproducten/
├── scraper/                    # 🕷️ Web scraper
│   ├── main.py                # Hoofd scraper script  
│   ├── product_scraper.py     # Product detail scraper
│   ├── sitemap_parser.py      # Sitemap parser
│   ├── cookie_manager.py      # Cookie beheer
│   ├── proxy_manager.py       # Proxy rotatie
│   ├── database.py            # Database beheer
│   ├── utils.py               # Hulpfuncties
│   ├── requirements.txt       # Scraper dependencies
│   ├── .env.example          # Configuratie template
│   ├── COOKIES.md            # Cookie setup gids
│   └── data/                 # Gescrapte data
├── analyze_data.py            # 📊 Data analyse tool
├── setup.py                  # 🔧 Automatische setup
├── requirements_analysis.txt  # Analyse dependencies
├── SECURITY.md               # Veiligheid & setup
└── README.md                 # Deze documentatie
```

## 🛠️ Troubleshooting

### Veelvoorkomende Problemen

**Cookie/Authentication Errors:**
- Vernieuw je cookies (zie `scraper/COOKIES.md`)
- Controleer je CSRF token

**Database Errors:**
- Run `cd scraper && python migrate_db.py`

**Analysis Errors:**
- Zorg dat je eerst data hebt gescraped
- Installeer analyse dependencies: `pip install -r requirements_analysis.txt`

### Debug Mode

```bash
cd scraper
python main.py --debug --all --limit 10
```

## 📊 Output Voorbeelden

Na het draaien van `python analyze_data.py` krijg je:

- 📈 **Grafieken** in `data/analysis/images/`
- 📋 **JSON rapport** met alle data  
- 📖 **README** met overzicht en afbeeldingen
- 📊 **Statistieken** van je dataset

## 🔒 Privacy & Ethiek

- **Respectvolle scraping** - Ingebouwde delays en rate limiting
- **Publieke data** - Alleen publiek beschikbare productinfo
- **Educational purpose** - Bedoeld voor leren en onderzoek
- **Terms compliance** - Respecteer PLUS.nl's voorwaarden

## 🤝 Bijdragen

1. Fork het project
2. Maak een feature branch
3. Commit je wijzigingen  
4. Open een Pull Request

## 📄 Licentie

MIT License - zie LICENSE bestand voor details.

## ⚠️ Disclaimer

**Dit project is alleen voor educatieve doeleinden.** 
Respecteer de terms of service van PLUS.nl en gebruik verantwoordelijk.

---

**Voor vragen of problemen:** Open een issue op GitHub
