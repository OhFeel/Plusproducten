"""
test_cookies.py - Extract cookies from PowerShell output and save to .env file
"""

import re
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

def extract_cookies_from_powershell(powershell_output):
    """
    Extract cookies from PowerShell New-Object System.Net.Cookie commands
    """
    cookie_pattern = r'\$session\.Cookies\.Add\(\(New-Object System\.Net\.Cookie\("([^"]+)", "([^"]+)", "([^"]+)", "([^"]+)"\)\)\)'
    cookies = {}
    
    matches = re.findall(cookie_pattern, powershell_output)
    for match in matches:
        name, value, path, domain = match
        cookies[name] = {
            "name": name,
            "value": value,
            "path": path,
            "domain": domain
        }
    
    return cookies

def save_cookies_to_env(cookies):
    """
    Save extracted cookies to .env file
    """
    env_path = Path('.env')
    
    # Load existing .env file
    load_dotenv(env_path)
    
    # Add or update cookie entries
    for name, cookie in cookies.items():
        cookie_key = f"COOKIE_{name.upper().replace('-', '_')}"
        set_key(env_path, cookie_key, cookie["value"])
    
    # Add a counter for the number of cookies
    set_key(env_path, "COOKIE_COUNT", str(len(cookies)))

if __name__ == "__main__":
    # Example PowerShell output
    powershell_output = """
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0"
    $session.Cookies.Add((New-Object System.Net.Cookie("SSLB", "1", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("visid_incap_1876175", "qn0ZOkWCTlCG/qxh87cHFbohd2cAAAAAQUIPAAAAAABa9ZSfCFpHJer1afeQ/izG", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("osVisitor", "74d18b43-2fe7-4272-bd20-d8dc5014470b", "/", "www.plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("nlbi_1876175", "v8bdCBd05i7iz+cn+vsR5gAAAAB//OgE2kuHVPRpv4TfqbDl", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("nr2Users", "crf%3dT6C%2b9iB49TLra4jEsMeSckDMNhQ%3d%3buid%3d0%3bunm%3d", "/", "www.plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("nr1Users", "lid%3dAnonymous%3btuu%3d0%3bexp%3d0%3brhs%3dXBC1ss1nOgYW1SmqUjSxLucVOAg%3d%3bhmc%3d4DwFYjtQmhXgYB3zdBmXn5G3zBA%3d", "/", "www.plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("baked", "2023-05-12 10:20:05", "/", "www.plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("plus_cookie_level", "3", "/", "www.plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("incap_ses_281_1876175", "wy7BTBxmjVArRhLKM1DmAwFaC2gAAAAAiEgP5HhzSVOCJmNRwMHlOw==", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("nlbi_1876175_2948836", "PYVlCfTY4QnD6M+I+vsR5gAAAABwNkm694uiRhdiEtXDZOg7", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("SSID_WA9S", "CQB1SR0OAAAAAAC7IXdn8paAA7shd2cNAAAAAADniTlr0GELaAD0DJBOAQNuJCkAuyF3Zw0A", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("SSSC_WA9S", "1036.G7455464795236505330.13|85648.2696302", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("osVisit", "df65b2a2-1039-466a-93fd-794c42d7da10", "/", "www.plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("incap_ses_1689_1876175", "ve4qQ4e05nsBbqEnzIhwFxFiC2gAAAAAIZUa/3XktfGplAgiql5xkA==", "/", ".plus.nl")))
    $session.Cookies.Add((New-Object System.Net.Cookie("SSRT_WA9S", "G2ILaAADAA", "/", ".plus.nl")))
    """
    
    cookies = extract_cookies_from_powershell(powershell_output)
    save_cookies_to_env(cookies)
    
    print(f"Extracted {len(cookies)} cookies and saved to .env file")
    for name, cookie in cookies.items():
        print(f"- {name}: {cookie['value'][:20]}...")
