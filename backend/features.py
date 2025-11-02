
import re
import socket
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
import whois
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

@lru_cache(maxsize=100)
def extract_page_text_cached(url):
    """Cached version of page text extraction."""
    return extract_page_text(url)

def extract_url_features(url):
    """Extracts 29 features from a URL and returns a pandas DataFrame (1 row)."""

    
    try:
        parsed = urlparse(url)
    except:
        parsed = None

    

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

    return pd.DataFrame([features])


def categorize_website(url):
    """Return a broad website category based on enhanced domain and content analysis."""
    try:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()
    except Exception:
        domain = ""
        path = ""

    # Comprehensive keyword to category mapping
    keyword_categories = [
        # Search engines
        (["google", "bing", "yahoo", "duckduckgo", "baidu", "yandex"], "Search Engine"),
        
        # Social media
        (["facebook", "instagram", "twitter", "x.com", "tiktok", "snapchat", 
          "linkedin", "reddit", "pinterest", "tumblr", "whatsapp", "telegram"], "Social Media"),
        
        # Developer/Tech
        (["github", "gitlab", "bitbucket", "stackoverflow", "stackexchange", 
          "npmjs", "pypi", "docker", "kubernetes", "dev.to", "medium.com"], "Developer/Tech"),
        
        # Streaming/Entertainment
        (["netflix", "youtube", "spotify", "hulu", "primevideo", "disney", "instagram", 
          "twitch", "vimeo", "soundcloud"], "Streaming/Entertainment"),
        
        # Shopping/E-commerce
        (["amazon", "ebay", "walmart", "aliexpress", "etsy", "shopify", 
          "bestbuy", "target", "shop", "store"], "E-commerce/Shopping"),
        
        # News/Media
        (["cnn", "bbc", "nytimes", "reuters", "bloomberg", "theguardian", 
          "wsj", "forbes", "news", "press"], "News/Media"),
        
        # Finance/Banking
        (["bankofamerica", "chase", "wellsfargo", "paypal", "stripe", 
          "coinbase", "robinhood", "fidelity", "bank", "finance"], "Finance/Banking"),
        
        # Education
        (["harvard", "mit.edu", "stanford", "coursera", "udemy", "edx", 
          "khanacademy", "duolingo", "edu"], "Education"),
        
        # Government
        ([".gov", "whitehouse", "government"], "Government"),
        
        # Health
        (["webmd", "mayoclinic", "nih.gov", "healthline", "health", "medical"], "Health/Medical"),
        
        # Travel
        (["booking", "expedia", "airbnb", "tripadvisor", "hotels", "travel"], "Travel"),
        
        # Gaming
        (["steam", "epicgames", "playstation", "xbox", "nintendo", "game"], "Gaming"),
        
        # Cloud/Productivity
        (["google.com/drive", "dropbox", "onedrive", "notion", "trello", "slack"], "Productivity/Cloud"),
    ]

    # Check domain and path
    full_url = domain + path
    for keywords, category in keyword_categories:
        for keyword in keywords:
            if keyword in full_url:
                return category

    # TLD-based fallback
    if domain.endswith(".gov"):
        return "Government"
    if domain.endswith(".edu"):
        return "Education"
    if domain.endswith(".org"):
        return "Organization/Nonprofit"
    if domain.endswith((".co", ".com")):
        return "Business/Commercial"

    return "General/Other"


def extract_page_text(url):
    """Enhanced page text extraction with better error handling and content prioritization."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        # Handle redirects, timeout, and SSL with better error handling
        session = requests.Session()
        session.max_redirects = 5  # Increased for better navigation
        
        resp = session.get(
            url, 
            headers=headers, 
            timeout=10,  # Increased timeout
            allow_redirects=True, 
            verify=False,
            stream=True  # Stream for large pages
        )
        
        if resp.status_code >= 400:
            print(f"⚠️ HTTP {resp.status_code} for {url}")
            return ""
        
        # Try to decode properly with better encoding detection
        if resp.encoding is None or resp.encoding.lower() in ['iso-8859-1', 'windows-1252']:
            resp.encoding = resp.apparent_encoding or 'utf-8'
        
        # Read content in chunks for large pages
        content = ""
        for chunk in resp.iter_content(chunk_size=8192, decode_unicode=True):
            if chunk:
                content += chunk
                # Limit content size to prevent memory issues
                if len(content) > 500000:  # 500KB limit
                    break
        
        if len(content) < 100:
            print(f"⚠️ Page too short: {url}")
            return ""
        
        soup = BeautifulSoup(content, "lxml")

        # Remove unwanted elements but keep important content
        for tag in soup(["script", "style", "noscript", "nav", "footer", 
                         "aside", "iframe", "header", "button", "form", "advertisement", "ads"]):
            tag.decompose()

        # Extract text with enhanced priority weighting for category detection
        important_text = []
        
        # 1. Title (highest weight) - most important for category
        title = soup.find("title")
        if title and title.get_text(strip=True):
            title_text = title.get_text(strip=True)
            important_text.extend([title_text] * 8)  # Increased weight
        
        # 2. Meta tags (very important for SEO and category)
        for meta in soup.find_all("meta"):
            name = meta.get("name", "").lower()
            property_val = meta.get("property", "").lower()
            if name in ["description", "keywords", "category", "type"] or "description" in property_val or "og:" in property_val:
                content = meta.get("content", "")
                if content and len(content) > 10:
                    important_text.extend([content] * 5)  # Increased weight
        
        # 3. Enhanced header extraction (H1-H6)
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(strip=True)
                if text and len(text) > 3:
                    weight = 6 if tag_name == "h1" else 5 if tag_name == "h2" else 4 if tag_name == "h3" else 3
                    important_text.extend([text] * weight)
        
        # 4. Extract structured data (JSON-LD, microdata)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if "name" in data:
                        important_text.extend([data["name"]] * 4)
                    if "description" in data:
                        important_text.extend([data["description"]] * 3)
                    if "@type" in data:
                        important_text.extend([data["@type"]] * 2)
            except:
                pass
        
        # 4. Main content area
        main_selectors = [
            soup.find("main"),
            soup.find("article"),
            soup.find(id=re.compile("content|main|body", re.I)),
            soup.find(class_=re.compile("content|main|body", re.I))
        ]
        
        for main_content in main_selectors:
            if main_content:
                text = main_content.get_text(separator=" ", strip=True)
                if len(text) > 50:
                    important_text.append(text)
                break
        
        # 5. Paragraphs (if no main content found)
        if len(" ".join(important_text)) < 500:
            for p in soup.find_all("p", limit=30):
                text = p.get_text(strip=True)
                if len(text) > 30:
                    important_text.append(text)
        
        # 6. Lists
        for ul in soup.find_all(["ul", "ol"], limit=15):
            text = ul.get_text(separator=" ", strip=True)
            if len(text) > 30:
                important_text.append(text)
        
        # Combine all text
        all_text = " ".join(important_text)
        
        # Fallback to body if nothing found
        if len(all_text.strip()) < 100:
            body = soup.find("body")
            if body:
                all_text = body.get_text(separator=" ", strip=True)
        
        if not all_text.strip():
            print(f"⚠️ No text extracted from {url}")
            return ""
        
        # Clean the text
        text = " ".join(all_text.split())
        
        # Remove noise while keeping meaningful content
        text = re.sub(r'\b\d{5,}\b', '', text)  # Long numbers
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\']', ' ', text)  # Special chars
        text = " ".join(text.split())
        
        print(f"✅ Extracted {len(text)} chars from {url}")
        return text[:100000]
        
    except requests.Timeout:
        print(f"⏱️ Timeout for {url}")
        return ""
    except requests.RequestException as e:
        print(f"🌐 Network error for {url}: {str(e)[:50]}")
        return ""
    except Exception as e:
        print(f"❌ Text extraction failed for {url}: {str(e)[:50]}")
        return ""


def advanced_text_preprocessing(text):
    """Advanced text preprocessing for ML category classification."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs but keep domain keywords
    text = re.sub(r'http[s]?://(?:www\.)?', ' ', text)
    text = re.sub(r'\.com|\.org|\.net|\.edu|\.gov', ' ', text)
    
    # Remove emails
    text = re.sub(r'\S+@\S+', ' ', text)
    
    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', ' ', text)
    
    # Remove hex colors
    text = re.sub(r'#[0-9a-f]{3,6}\b', ' ', text)
    
    # Keep alphanumeric and basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    
    # Remove standalone numbers
    text = re.sub(r'\b\d+\b', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def create_advanced_features(df, text_col):
    """Create comprehensive features from text for ML classification."""
    features = []
    
    for text in df[text_col]:
        text = str(text)
        words = text.lower().split()
        
        # Basic statistics
        word_count = len(words)
        char_count = len(text)
        avg_word_length = char_count / max(word_count, 1)
        unique_words = len(set(words))
        unique_ratio = unique_words / max(word_count, 1)
        
        # Sentence features
        sentence_count = max(1, text.count('.') + text.count('!') + text.count('?'))
        avg_sentence_length = word_count / sentence_count
        
        # Punctuation
        exclamation_count = text.count('!')
        question_count = text.count('?')
        comma_count = text.count(',')
        
        # Enhanced domain keywords
        text_lower = text.lower()
        
        # Technology keywords
        tech_kw = ['software', 'technology', 'computer', 'digital', 'app', 'code', 
                   'programming', 'developer', 'api', 'cloud', 'data', 'ai', 'ml']
        tech_score = sum(1 for w in tech_kw if w in text_lower)
        
        # Business keywords
        business_kw = ['business', 'company', 'corporate', 'management', 'finance',
                       'market', 'industry', 'service', 'professional', 'enterprise']
        business_score = sum(1 for w in business_kw if w in text_lower)
        
        # E-commerce keywords
        ecom_kw = ['shop', 'buy', 'sell', 'product', 'price', 'cart', 'order',
                   'shipping', 'delivery', 'discount', 'sale', 'payment']
        ecom_score = sum(1 for w in ecom_kw if w in text_lower)
        
        # Education keywords
        edu_kw = ['education', 'learn', 'course', 'student', 'school', 'university',
                  'study', 'teach', 'training', 'lesson', 'academic', 'research']
        edu_score = sum(1 for w in edu_kw if w in text_lower)
        
        # News keywords
        news_kw = ['news', 'article', 'report', 'story', 'journalist', 'breaking',
                   'latest', 'update', 'announced', 'revealed']
        news_score = sum(1 for w in news_kw if w in text_lower)
        
        # Entertainment keywords
        ent_kw = ['entertainment', 'movie', 'music', 'game', 'video', 'stream',
                  'watch', 'play', 'show', 'series', 'artist']
        ent_score = sum(1 for w in ent_kw if w in text_lower)
        
        # Social keywords
        social_kw = ['social', 'friend', 'follow', 'share', 'post', 'comment',
                     'like', 'message', 'chat', 'community', 'profile']
        social_score = sum(1 for w in social_kw if w in text_lower)
        
        # Health keywords
        health_kw = ['health', 'medical', 'doctor', 'patient', 'hospital',
                     'treatment', 'medicine', 'wellness', 'fitness', 'care']
        health_score = sum(1 for w in health_kw if w in text_lower)
        
        # Finance keywords
        finance_kw = ['bank', 'banking', 'financial', 'money', 'loan', 'credit',
                      'investment', 'trading', 'stock', 'insurance']
        finance_score = sum(1 for w in finance_kw if w in text_lower)
        
        # Travel keywords
        travel_kw = ['travel', 'hotel', 'flight', 'booking', 'vacation', 'trip',
                     'tour', 'destination', 'resort', 'tourist']
        travel_score = sum(1 for w in travel_kw if w in text_lower)
        
        # Normalize scores
        norm = max(word_count, 1) / 100
        
        features.append({
            'word_count': word_count,
            'char_count': char_count,
            'avg_word_length': avg_word_length,
            'unique_ratio': unique_ratio,
            'avg_sentence_length': avg_sentence_length,
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            'comma_count': comma_count,
            'tech_score': tech_score / norm,
            'business_score': business_score / norm,
            'ecommerce_score': ecom_score / norm,
            'education_score': edu_score / norm,
            'news_score': news_score / norm,
            'entertainment_score': ent_score / norm,
            'social_score': social_score / norm,
            'health_score': health_score / norm,
            'finance_score': finance_score / norm,
            'travel_score': travel_score / norm,
            'action_score': sum(1 for w in ['buy', 'sell', 'learn', 'read', 'watch'] if w in text_lower) / norm,
            'cta_score': sum(1 for w in ['free', 'now', 'join', 'get', 'start'] if w in text_lower) / norm
        })
    
    return pd.DataFrame(features)