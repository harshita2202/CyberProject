import re
from urllib.parse import urlparse
import pandas as pd

# Only the 26 URL features used in model training
url_columns = [
    'NumDots', 'SubdomainLevel', 'PathLevel', 'UrlLength', 'NumDash', 'NumDashInHostname',
    'AtSymbol', 'TildeSymbol', 'NumUnderscore', 'NumPercent', 'NumQueryComponents',
    'NumAmpersand', 'NumHash', 'NumNumericChars', 'NoHttps', 'RandomString', 'IpAddress',
    'DomainInSubdomains', 'DomainInPaths', 'HttpsInHostname', 'HostnameLength',
    'PathLength', 'QueryLength', 'DoubleSlashInPath', 'NumSensitiveWords', 'EmbeddedBrandName'
]

def extract_url_features(url):
    """
    Extract only the 26 URL features for the trained XGBoost model.
    Returns a DataFrame with a single row.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        path = parsed.path or ''
        query = parsed.query or ''
        full_url = url.lower()

        features = {
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
            'RandomString': 1 if re.search(r'[a-zA-Z]{5,}', hostname) and len(set(hostname)) < 3 else 0,
            'IpAddress': 1 if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', hostname) else 0,
            'DomainInSubdomains': 1 if hostname.lower() in hostname.split('.')[0].lower() else 0,
            'DomainInPaths': 1 if hostname.lower() in path.lower() else 0,
            'HttpsInHostname': 1 if 'https' in hostname.lower() else 0,
            'HostnameLength': len(hostname),
            'PathLength': len(path),
            'QueryLength': len(query),
            'DoubleSlashInPath': 1 if '//' in path else 0,
            'NumSensitiveWords': len(re.findall(r'(login|password|bank|account)', full_url)),
            'EmbeddedBrandName': 0  # Placeholder
        }

        df = pd.DataFrame([features], columns=url_columns).astype('float64')
        return df

    except Exception as e:
        print(f"Feature extraction error for {url}: {e}")
        # Return zero-filled features if URL parsing fails
        zero_features = {col: 0.0 for col in url_columns}
        return pd.DataFrame([zero_features], columns=url_columns).astype('float64')