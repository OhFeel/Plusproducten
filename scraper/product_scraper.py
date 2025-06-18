"""
product_scraper.py - Scrapes product details from PLUS
"""

import os
import time
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Set
from utils import (
    logger, exponential_backoff, get_plus_headers, save_to_retry,
    create_checkpoint, load_checkpoint, format_filename
)
from proxy_manager import proxy_manager
from cookie_manager import cookie_manager

class ProductScraper:
    """
    Scrapes product details using the PLUS API
    """
    
    def __init__(self):
        self.api_url = "https://www.plus.nl/screenservices/ECP_Product_CW/ProductDetails/PDPContent/DataActionGetProductDetailsAndAgeInfo"
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.backoff_factor = float(os.getenv("BACKOFF_FACTOR", "2"))
        self.request_delay = float(os.getenv("REQUEST_DELAY", ".25"))
        self.last_request_time = 0
        self.csrf_token = os.getenv("PLUS_CSRF_TOKEN", "T6C+9iB49TLra4jEsMeSckDMNhQ=")
    def _build_payload(self, sku: str, product_name: str = "") -> Dict[str, Any]:
        """
        Build the API request payload (exact match from the JavaScript fetch example)
        """
        # Gebruik het exacte formaat dat in de JavaScript fetch wordt gebruikt
        product_slug = product_name or f"product-{sku}"
        
        return {
            "versionInfo": {
                "moduleVersion": "6uc+XDsRynmQ7JQS4jOSaQ",
                "apiVersion": "j2jjJJxS4heD58kEZAYPUQ"
            },
            "viewName": "MainFlow.ProductDetailsPage",
            "screenData": {
                "variables": {
                    "ShowMedicineSidebar": False,
                    "Product": {
                        "Overview": {
                            "Name": "",
                            "Subtitle": "",
                            "Brand": "",
                            "Slug": "",
                            "Image": {
                                "Label": "",
                                "URL": ""
                            },
                            "Meta": {
                                "Description": "",
                                "Title": ""
                            },
                            "IsNIX18": False,
                            "Price": "0",
                            "BaseUnitPrice": "",
                            "LineItem": {
                                "Id": "",
                                "Quantity": 0
                            },
                            "IsOfflineSaleOnly": False,
                            "IsServiceItem": False,
                            "IsAvailableInStore": False,
                            "MaxOrderLimit": 0
                        },
                        "ProductClassificationId": "",
                        "Categories": {
                            "List": [],
                            "EmptyListItem": {
                                "Name": ""
                            }
                        },
                        "Logos": {
                            "PDPInUpperLeft": {"List": [], "EmptyListItem": {"Name": "", "LongDescription": "", "URL": "", "Order": 0}},
                            "PDPInProductInformation": {"List": [], "EmptyListItem": {"Name": "", "LongDescription": "", "URL": "", "Order": 0}},
                            "PDPBehindSizeUnit": {"List": [], "EmptyListItem": {"Name": "", "LongDescription": "", "URL": "", "Order": 0}},
                            "PDPBelowAddToCart": {"List": [], "EmptyListItem": {"Name": "", "LongDescription": "", "URL": "", "Order": 0}},
                            "PDPAboveTitle": {"List": [], "EmptyListItem": {"Name": "", "LongDescription": "", "URL": "", "Order": 0}},
                            "PDPInRemarks": {"List": [], "EmptyListItem": {"Name": "", "LongDescription": "", "URL": "", "Order": 0}}
                        },
                        "Legal": {"RegulatedName": "", "HealthClaim": "", "DrainWeight": {"UoM": "", "Value": 0}, "RequiredNotificationByLaw": "", "AppointedAuthority": "", "AdittionalClassification": {"System": "", "Trades": ""}},
                        "UsageDuring": {"BreastFeeding": "", "Pregnancy": "", "SafePeriodAfterOpening": 0},
                        "Marketing": {"Description": "", "UniqueSellingPoint": "", "Message": ""},
                        "SupplierContact": {"LegalContact": {"Address": "", "Name": ""}, "LegalSupplier": {"Address": "", "Name": ""}, "PDP_ProductMeans": {"Email_List": {"List": [], "EmptyListItem": ""}, "SocialMedia_List": {"List": [], "EmptyListItem": ""}, "Contact_List": {"List": [], "EmptyListItem": ""}, "WebSites_List": {"List": [], "EmptyListItem": ""}}},
                        "Composition": "",
                        "Ingredients": "",
                        "Nutrient": {"Base": {"UoM": "", "Value": 0}, "Additional": {"NutricionalClaim": "", "PreparedDeviation": "", "ReferenceIntake": ""}, "Nutrients": {"List": [], "EmptyListItem": {"TypeCode": "", "UnitCode": "", "Description": "", "ParentCode": "", "DailyValueIntakePercent": "", "QuantityContained": {"Value": "0", "UoM": ""}, "SortOrder": 0}}},
                        "Allergen": {"Warning": "", "Description": ""},
                        "InstructionsAndSuggestions": {"Instructions": {"Preparation": "", "Storage": "", "Usage": ""}, "Suggestions": {"Serving": ""}},
                        "PercentageOfAlcohol": "",
                        "Beer": {"Kind": "", "Taste": "", "FoodAdvice": "", "Description": {"Long": "", "Short": ""}},
                        "Wine": {"Type": "", "Quote": "", "LongDescription": "", "Flavour": "", "GrapeVariety": "", "Country": "", "Region": "", "WineTastingNote": {"FoodAdvice": "", "SmellAndTaste": "", "FoodAdvices": {"List": [], "EmptyListItem": ""}}, "Awards": {"List": [], "EmptyListItem": ""}},
                        "SeaFood": {"Production": {"Method": ""}, "Catch": {"Areas": "", "Methods": ""}},
                        "PetFood": {"TargetConsumptionBy": "", "Feed": {"Instructions": "", "Type": ""}, "FoodStatetment": {"Additive": "", "AnalyticalConstituents": "", "Composition": ""}},
                        "Medicine": {"EAN": ""},
                        "DrugStore": {"Store": {"Origin": "", "Number": {"RVG": "", "RVH": ""}, "Certification": {"Agency": "", "Standard": ""}}, "Dosage": {"Admnistration": "", "Recommendation": ""}, "SideEffectsAndWarnings": ""},
                        "HealthCare": {"UsageAge": {"Description": "", "Max": {"UoM": "", "Value": 0}, "Min": {"UoM": "", "Value": 0}}, "SunProtection": {"Category": "", "Factor": ""}},
                        "LightBulb": {"BaseType": "", "LampTypeCode": "", "NumberOfSwitches": "", "SuitableForAccentLighting": "", "DeclaredPower": {"UoM": "", "Value": 0}, "EquivalentPower": {"UoM": "", "Value": 0}, "Diameter": {"UoM": "", "Value": 0}, "VisibleLight": {"UoM": "", "Value": 0}, "ColourTemperature": {"Avg": {"UoM": "", "Value": 0}, "Max": {"UoM": "", "Value": 0}, "Min": {"UoM": "", "Value": 0}}, "WarmUpTime": {"UoM": "", "Value": 0}},
                        "Battery": {"Voltage": {"UoM": "", "Value": "0"}, "Capacity": {"UoM": "", "Value": 0}, "Weight": {"UoM": "", "Value": "0"}, "Quantity": 0, "MaterialAgency": "", "Type": "", "TechnologyTypes": {"List": [], "EmptyListItem": ""}, "IsRechargeable": False, "BuiltIn": {"IsBuiltIn": False, "Quantity": 0}},
                        "Hazardous": {"ChildSafeClosure": "", "Chemical": {"Identification": "", "Name": "", "Organisation": "", "Concentration": 0}, "SafetyRecommendations": {"List": [], "EmptyListItem": {"Key": "", "Value": ""}}, "HazardDesignations": {"List": [], "EmptyListItem": {"Key": "", "Value": ""}}, "GHSSignal": {"Symbols": "", "Word": ""}},
                        "IsVisibleSection": {"AboutThisBeer": False, "AboutThisProduct": False, "AboutThisWine": False, "AllergieInfo": False, "HandyInfo": False, "Ingredients": False, "LegalInfo": False, "NutrionalValues": False, "PreparationInstruction": False, "ServingSuggestions": False, "SupplierContact": False, "TasteInfo": False, "UsageAndStorage": False}
                    },
                    "ChannelId": "",
                    "Locale": "nl-NL",
                    "StoreId": "0",
                    "StoreNumber": 0,
                    "CheckoutId": "6c2d0426-f0a7-40f3-81fc-b889b8c74399",
                    "OrderEditId": "",
                    "IsOrderEditMode": False,
                    "TotalLineItemQuantity": 0,
                    "ShoppingListProducts": {
                        "List": [],
                        "EmptyListItem": {
                            "SKU": "",
                            "Quantity": "0"
                        }
                    },
                    "HasDailyValueIntakePercent": False,
                    "CartPromotionDeliveryDate": "2025-01-24",
                    "LineItemQuantity": 0,
                    "IsPhone": False,
                    "_isPhoneInDataFetchStatus": 1,
                    "OneWelcomeUserId": "",
                    "_oneWelcomeUserIdInDataFetchStatus": 1,
                    "SKU": sku,
                    "_sKUInDataFetchStatus": 1,
                    "TotalCartItems": 0,
                    "_totalCartItemsInDataFetchStatus": 1,
                    "ProductName": product_slug,
                    "_productNameInDataFetchStatus": 1
                }
            }
        }
    
    def _get_referrer(self, product_url: str) -> str:
        """
        Get the referrer URL for the request
        """
        if not product_url or not product_url.startswith("http"):
            return "https://www.plus.nl"
        return product_url
    @exponential_backoff(max_retries=3, initial_delay=1.0)
    def fetch_product(self, sku: str, product_url: str = "") -> Dict[str, Any]:
        """
        Fetch product details using the PLUS API
        """
        # Respect rate limiting
        time_since_last_request = time.time() - self.last_request_time
        if time_since_last_request < self.request_delay:
            time.sleep(self.request_delay - time_since_last_request)
        
        # Build the product URL for referrer if not provided
        if not product_url:
            product_url = f"https://www.plus.nl/product/product-{sku}"
          # Build the request
        payload = self._build_payload(sku)
        referrer = product_url
        proxies = proxy_manager.get_proxy()
        
        logger.info(f"Fetching product SKU: {sku}")
        
        # Headers gebaseerd op de werkende PowerShell request
        headers = {
            "authority": "www.plus.nl",
            "method": "POST",
            "path": "/screenservices/ECP_Product_CW/ProductDetails/PDPContent/DataActionGetProductDetailsAndAgeInfo",
            "scheme": "https",
            "accept": "application/json",
            "accept-language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://www.plus.nl",
            "outsystems-locale": "nl-NL",
            "priority": "u=1, i",
            "referer": referrer,
            "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Opera GX\";v=\"117\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-csrftoken": self.csrf_token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0"
        }
          # Gebruik de cookie manager om cookies op te halen
        cookies = cookie_manager.get_cookies()
        response = requests.post(
            self.api_url,
            json=payload,
            headers=headers,
            cookies=cookies,
            proxies=proxies,
            timeout=self.timeout
        )
        
        # Update last request time
        self.last_request_time = time.time()
        
        # Bewaar eventuele nieuwe cookies uit de response
        if response.status_code == 200:
            cookie_manager.extract_cookies_from_response(response)
        
        # Report proxy success/failure
        if proxies:
            if response.status_code == 200:
                proxy_manager.report_success(proxies.get("https"))
            else:
                proxy_manager.report_failure(proxies.get("https"))
        
        # Handle the response
        response.raise_for_status()
        data = response.json()
        
        # Check if we got valid data
        if "data" not in data:
            raise ValueError(f"Invalid response format for SKU {sku}")
        
        return data
    
    def extract_product_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant product data from the API response
        """
        data = response_data.get("data", {})
        product_out = data.get("ProductOut", {})
        overview = product_out.get("Overview", {})
        
        # Extract nutrients information
        nutrients = []
        nutrient_data = product_out.get("Nutrient", {})
        base_uom = nutrient_data.get("Base", {}).get("UoM", "")
        base_value = nutrient_data.get("Base", {}).get("Value", 0)
        
        for nutrient in nutrient_data.get("Nutrients", {}).get("List", []):
            nutrients.append({
                "name": nutrient.get("Description", ""),
                "value": nutrient.get("QuantityContained", {}).get("Value", "0"),
                "unit": nutrient.get("QuantityContained", {}).get("UoM", ""),
                "parent_code": nutrient.get("ParentCode", "")
            })
        
        # Extract product details
        product = {
            "sku": data.get("SKU", ""),
            "name": overview.get("Name", ""),
            "brand": overview.get("Brand", ""),
            "price": overview.get("Price", "0"),
            "base_unit_price": overview.get("BaseUnitPrice", ""),
            "image_url": data.get("ImageURL", ""),
            "ingredients": product_out.get("Ingredients", ""),
            "allergens": product_out.get("Allergen", {}).get("Description", ""),
            "nutrients_base": {
                "unit": base_uom,
                "value": base_value
            },
            "nutrients": nutrients,
            "percentage_alcohol": product_out.get("PercentageOfAlcohol", ""),
            "composition": product_out.get("Composition", ""),
            "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return product
    
    def save_product_json(self, product_data: Dict[str, Any], sku: str) -> str:
        """
        Save product data to a JSON file
        """
        product_dir = Path("data/products")
        product_dir.mkdir(exist_ok=True, parents=True)
        
        # Create a filename based on the SKU and name
        name = format_filename(product_data.get("name", "product"))
        filename = f"{sku}_{name}.json"
        file_path = product_dir / filename
        
        # Save the data
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved product {sku} to {file_path}")
        return str(file_path)
    
    def process_product(self, sku: str, product_url: str = "") -> Optional[Dict[str, Any]]:
        """
        Process a product: fetch, extract data, and save
        """
        try:
            # Fetch the product data
            response_data = self.fetch_product(sku, product_url)
            
            # Extract relevant product information
            product_data = self.extract_product_data(response_data)
            
            # Save to file
            self.save_product_json(product_data, sku)
            
            logger.info(f"Successfully processed product SKU: {sku}")
            return product_data
            
        except Exception as e:
            logger.error(f"Error processing product SKU {sku}: {e}")
            save_to_retry({"sku": sku, "url": product_url}, str(e))
            return None
