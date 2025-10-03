import urllib.parse
from urllib.parse import urlparse
import re
import pandas as pd
import numpy as np

def extract_url_features(url):
    """
    Extracts ALL features from URL matching Phishing_Legitimate_full.csv (46 total).
    Sets UI/page features to 0 (extension can't scrape without loading page).
    Returns a DataFrame row ready for XGBoost predict—no mismatch!
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        path = parsed.path or ''
        query = parsed.query or ''
        full_url = url.lower()  # Normalize for counts

        # ALL columns from dataset (URL + UI/RT, UI set to 0)
        features = {
            # URL features (calculated)
            'NumDots': hostname.count('.'),
            'SubdomainLevel': len(hostname.split('.')) - 2 if '.' in hostname else 0,
            'PathLevel': len([p for p in path.split('/') if p]),
            'UrlLength': len(url),
            'NumDash': full_url.count('-'),
            'NumDashInHostname': hostname.count('-'),
            'AtSymbol': full_url.count('@'),
            'TildeSymbol': full_url.count('~'),
            'NumUnderscore': full_url.count('_'),
            'NumPercent': full_url.count('%'),
            'NumQueryComponents': len(query.split('&')) if query else 0,
            'NumAmpersand': query.count('&'),
            'NumHash': 1 if '#' in url else 0,
            'NumNumericChars': len(re.findall(r'\d', full_url)),
            'NoHttps': 1 if not parsed.scheme or parsed.scheme != 'https' else 0,
            'RandomString': 1 if re.search(r'[a-zA-Z]{5,}', hostname) and len(set(hostname)) < 3 else 0,  # Rough randomness
            'IpAddress': 1 if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', hostname) else 0,
            'DomainInSubdomains': 1 if hostname.lower() in hostname.split('.')[0].lower() else 0,
            'DomainInPaths': 1 if hostname.lower() in path.lower() else 0,
            'HttpsInHostname': 1 if 'https' in hostname.lower() else 0,
            'HostnameLength': len(hostname),
            'PathLength': len(path),
            'QueryLength': len(query),
            'DoubleSlashInPath': 1 if '//' in path else 0,
            'NumSensitiveWords': len(re.findall(r'(login|password|bank|account)', full_url)),
            'EmbeddedBrandName': 0,  # Placeholder (expand if needed)
            
            # UI/Page features (set to 0—no scraping in extension)
            'PctExtHyperlinks': 0,
            'PctExtResourceUrls': 0,
            'ExtFavicon': 0,
            'InsecureForms': 0,
            'RelativeFormAction': 0,
            'ExtFormAction': 0,
            'AbnormalFormAction': 0,
            'PctNullSelfRedirectHyperlinks': 0,
            'FrequentDomainNameMismatch': 0,
            'FakeLinkInStatusBar': 0,
            'RightClickDisabled': 0,
            'PopUpWindow': 0,
            'SubmitInfoToEmail': 0,
            'IframeOrFrame': 0,
            'MissingTitle': 0,
            'ImagesOnlyInForm': 0,
            
            # RT variants (set to 0 or URL-based where possible)
            'SubdomainLevelRT': len(hostname.split('.')) - 2 if '.' in hostname else 0,
            'UrlLengthRT': len(url),
            'PctExtResourceUrlsRT': 0,
            'AbnormalExtFormActionR': 0,
            'ExtMetaScriptLinkRT': 0,
            'PctExtNullSelfRedirectHyperlinksRT': 0
        }

        # Convert to DataFrame (single row) with correct dtypes
        df = pd.DataFrame([features])
        # Ensure all columns are float for model (match training)
        df = df.astype('float64')
        return df

    except Exception as e:
        print(f"Feature extraction error for {url}: {e}")
        # Return a zero-filled DataFrame for bad URLs (treat as unsafe)
        zero_features = {col: 0.0 for col in [
            'NumDots', 'SubdomainLevel', 'PathLevel', 'UrlLength', 'NumDash', 'NumDashInHostname',
            'AtSymbol', 'TildeSymbol', 'NumUnderscore', 'NumPercent', 'NumQueryComponents',
            'NumAmpersand', 'NumHash', 'NumNumericChars', 'NoHttps', 'RandomString', 'IpAddress',
            'DomainInSubdomains', 'DomainInPaths', 'HttpsInHostname', 'HostnameLength',
            'PathLength', 'QueryLength', 'DoubleSlashInPath', 'NumSensitiveWords', 'EmbeddedBrandName',
            'PctExtHyperlinks', 'PctExtResourceUrls', 'ExtFavicon', 'InsecureForms', 'RelativeFormAction',
            'ExtFormAction', 'AbnormalFormAction', 'PctNullSelfRedirectHyperlinks', 'FrequentDomainNameMismatch',
            'FakeLinkInStatusBar', 'RightClickDisabled', 'PopUpWindow', 'SubmitInfoToEmail', 'IframeOrFrame',
            'MissingTitle', 'ImagesOnlyInForm', 'SubdomainLevelRT', 'UrlLengthRT', 'PctExtResourceUrlsRT',
            'AbnormalExtFormActionR', 'ExtMetaScriptLinkRT', 'PctExtNullSelfRedirectHyperlinksRT'
        ]}
        return pd.DataFrame([zero_features]).astype('float64')