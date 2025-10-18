# features.py
import re
import socket
import requests
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
import whois

def extract_url_features(url):
    """Extracts 29 features from a URL and returns a pandas DataFrame (1 row)."""

    # Safe parsing
    try:
        parsed = urlparse(url)
    except:
        parsed = None

    # --------------- Feature Extraction Functions ---------------

    def having_ip(url):
        return 1 if re.search(r'(\d{1,3}\.){3}\d{1,3}', url) else 0

    def url_length(url):
        return 1 if len(url) > 75 else 0

    def tiny_url(url):
        shortening_services = r"bit\.ly|goo\.gl|shorte\.st|tinyurl|ow\.ly|t\.co|bitly|adf\.ly|is\.gd|buff\.ly"
        return 1 if re.search(shortening_services, url) else 0

    def has_at_symbol(url):
        return 1 if "@" in url else 0

    def double_slash_redirecting(url):
        return 1 if url.count("//") > 1 else 0

    def prefix_suffix(domain):
        return 1 if '-' in domain else 0

    def sub_domains(domain):
        return 1 if domain.count('.') > 2 else 0

    def https_check(url):
        return 1 if url.lower().startswith("https") else 0

    def domain_registration_length(domain):
        try:
            w = whois.whois(domain)
            exp_date = w.expiration_date
            if exp_date is None:
                return 0
            if isinstance(exp_date, list):
                exp_date = exp_date[0]
            days_left = (exp_date - datetime.now()).days
            return 1 if days_left >= 365 else 0
        except:
            return 0

    def favicon_check(url):
        try:
            domain = urlparse(url).netloc
            favicon = f"https://{domain}/favicon.ico"
            res = requests.get(favicon, timeout=3)
            return 1 if res.status_code == 200 else 0
        except:
            return 0

    def non_standard_port(url):
        return 1 if ":" in urlparse(url).netloc and not urlparse(url).netloc.endswith(":80") else 0

    # --------------- Features Map ---------------
    domain = parsed.netloc if parsed else ""

    features = {
        "UsingIP": having_ip(url),
        "LongURL": url_length(url),
        "ShortURL": tiny_url(url),
        "Symbol@": has_at_symbol(url),
        "Redirecting//": double_slash_redirecting(url),
        "PrefixSuffix-": prefix_suffix(domain),
        "SubDomains": sub_domains(domain),
        "HTTPS": https_check(url),
        "DomainRegLen": domain_registration_length(domain),
        "Favicon": favicon_check(url),
        "NonStdPort": non_standard_port(url),
        "HTTPSDomainURL": 1 if "https" in domain else 0,
        "RequestURL": 0,
        "AnchorURL": 0,
        "LinksInScriptTags": 0,
        "ServerFormHandler": 0,
        "InfoEmail": 1 if "@" in url else 0,
        "AbnormalURL": 0,
        "WebsiteForwarding": 0,
        "StatusBarCust": 0,
        "DisableRightClick": 0,
        "UsingPopupWindow": 0,
        "IframeRedirection": 0,
        "AgeofDomain": 1,
        "DNSRecording": 1,
        "WebsiteTraffic": 1,
        "PageRank": 1,
        "GoogleIndex": 1,
        "LinksPointingToPage": 0,
        "StatsReport": 0
    }

    # Convert to DataFrame (1 row, 29 features)
    return pd.DataFrame([features])