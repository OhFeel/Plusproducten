# Cookie Setup Guide

To access the PLUS API, the scraper must use valid cookies. This guide explains how to set up cookies for the scraper.

## Option 1: Manually collect cookies

1. Open a browser and go to [PLUS.nl](https://www.plus.nl)
2. Open the browser developer tools (F12 or right-click -> Inspect)
3. Go to the Network tab
4. Load a product page, for example https://www.plus.nl/product/plus-boerentrots-bbq-worst-tuinkruiden-krimp-280-g-553975
5. Filter for "API" or "XHR" and look for a request to `DataActionGetProductDetailsAndAgeInfo`
6. Click on this request and look under "Headers" -> "Request Headers" for the Cookie value
7. Copy these cookies and save them in the `.env` file

## Option 2: Use the PowerShell cookie extractor

The easiest method is to use the PowerShell cookie extractor:

1. Open PowerShell with administrator rights
2. Execute the following commands:

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
$session.Cookies.Add((New-Object System.Net.Cookie("SSLB", "1", "/", ".plus.nl")))
$session.Cookies.Add((New-Object System.Net.Cookie("plus_cookie_level", "3", "/", "www.plus.nl")))

# Add more cookies if necessary...

# Copy the output and paste it into test_cookies.py
```

3. Open the `test_cookies.py` file and place the PowerShell cookie lines in the `powershell_output` variable
4. Run the script: `python test_cookies.py`
5. The cookies will be automatically written to the `.env` file

## Option 3: Use the interactive cookie setup wizard

1. Run the following command:

```powershell
python run_scraper.py setup-cookies
```

2. Follow the on-screen instructions to enter the cookie rules
3. The cookies will be automatically written to the `.env` file

## Testing cookies

To check if the cookies are working, you can run the following command:

```powershell
python test_product_cookies.py --sku 553975 --debug
```

If everything works correctly, you will see a success message and the product data will be saved in `data/test/product_553975_cookie_test.json`.

## Troubleshooting

If you encounter problems with cookies:

1. Make sure your cookies are up-to-date (cookies expire over time)
2. Check if you have copied the correct values
3. Try to collect cookies again via the browser
4. Run the test script with the debug option to see more details: `python test_product_cookies.py --debug`
