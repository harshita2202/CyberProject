# features.py - Enhanced version
import re
import socket
import requests
from bs4 import BeautifulSoup
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

    return pd.DataFrame([features])


def categorize_website(url):
    """Return a broad website category based on simple domain heuristics."""
    try:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower()
    except Exception:
        domain = ""

    # Expanded keyword to category mapping
    keyword_categories = [
        # Search engines
        ("google", "Search"),
        ("bing", "Search"),
        ("yahoo", "Search"),
        ("duckduckgo", "Search"),
        ("baidu", "Search"),

        # Social media
        ("facebook", "Social"),
        ("instagram", "Social"),
        ("twitter", "Social"),
        ("x.com", "Social"),
        ("tiktok", "Social"),
        ("snapchat", "Social"),
        ("linkedin", "Social"),
        ("reddit", "Social"),
        ("pinterest", "Social"),
        ("tumblr", "Social"),
        ("whatsapp", "Social"),

        # Developer/Tech
        ("github", "Developer"),
        ("gitlab", "Developer"),
        ("bitbucket", "Developer"),
        ("stackoverflow", "Developer"),
        ("stackexchange", "Developer"),
        ("npmjs", "Developer"),
        ("pypi", "Developer"),
        ("docker", "Developer"),
        ("kubernetes", "Developer"),

        # Streaming/Entertainment
        ("netflix", "Streaming"),
        ("youtube", "Streaming"),
        ("spotify", "Streaming"),
        ("hulu", "Streaming"),
        ("primevideo", "Streaming"),
        ("disney", "Streaming"),
        ("twitch", "Streaming"),
        ("vimeo", "Streaming"),

        # Shopping/E-commerce
        ("amazon", "Shopping"),
        ("ebay", "Shopping"),
        ("walmart", "Shopping"),
        ("aliexpress", "Shopping"),
        ("etsy", "Shopping"),
        ("shopify", "Shopping"),
        ("bestbuy", "Shopping"),
        ("target", "Shopping"),

        # News/Media
        ("cnn", "News"),
        ("bbc", "News"),
        ("nytimes", "News"),
        ("reuters", "News"),
        ("bloomberg", "News"),
        ("theguardian", "News"),
        ("wsj", "News"),
        ("forbes", "News"),

        # Finance/Banking
        ("bankofamerica", "Finance"),
        ("chase", "Finance"),
        ("wellsfargo", "Finance"),
        ("paypal", "Finance"),
        ("stripe", "Finance"),
        ("coinbase", "Finance"),
        ("robinhood", "Finance"),
        ("fidelity", "Finance"),

        # Education
        ("harvard", "Education"),
        ("mit.edu", "Education"),
        ("stanford", "Education"),
        ("coursera", "Education"),
        ("udemy", "Education"),
        ("edx", "Education"),
        ("khanacademy", "Education"),
        ("duolingo", "Education"),

        # Government
        (".gov", "Government"),
        ("whitehouse", "Government"),

        # Health
        ("webmd", "Health"),
        ("mayoclinic", "Health"),
        ("nih.gov", "Health"),
        ("healthline", "Health"),

        # Travel
        ("booking", "Travel"),
        ("expedia", "Travel"),
        ("airbnb", "Travel"),
        ("tripadvisor", "Travel"),
        ("hotels", "Travel"),
    ]

    for keyword, category in keyword_categories:
        if keyword in domain:
            return category

    # TLD-based fallback
    if domain.endswith(".gov"):
        return "Government"
    if domain.endswith(".edu"):
        return "Education"
    if domain.endswith(".org"):
        return "Nonprofit"

    return "General"


def extract_page_text(url):
    """Fetch page and return visible text for ML categorization with enhanced extraction."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        # Handle redirects and SSL issues
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True, verify=False)
        if resp.status_code >= 400:
            return ""
            
        # Try to decode properly
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text
        
        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted elements
        for tag in soup(["script", "style", "noscript", "nav", "footer", "aside", "iframe"]):
            tag.extract()

        # Extract text from important elements with priority
        important_text = []
        
        # Title (highest priority)
        title = soup.find("title")
        if title:
            important_text.append(title.get_text(strip=True) * 3)  # Repeat for emphasis
        
        # Meta description and keywords
        for meta in soup.find_all("meta"):
            if meta.get("name") in ["description", "keywords", "og:description"]:
                content = meta.get("content", "")
                if content:
                    important_text.append(content * 2)  # Repeat for emphasis
        
        # Headers (h1-h3 are most important)
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text(strip=True)
            if text:
                important_text.append(text * 2)  # Repeat for emphasis
        
        # Main content area
        main_content = soup.find("main") or soup.find("article") or soup.find(id=re.compile("content|main", re.I))
        if main_content:
            important_text.append(main_content.get_text(separator=" ", strip=True))
        
        # Paragraphs
        for p in soup.find_all("p", limit=50):  # Limit to avoid too much noise
            text = p.get_text(strip=True)
            if len(text) > 20:  # Only meaningful paragraphs
                important_text.append(text)
        
        # Lists (often contain key information)
        for ul in soup.find_all(["ul", "ol"], limit=20):
            text = ul.get_text(separator=" ", strip=True)
            if len(text) > 20:
                important_text.append(text)
        
        # Combine all text
        all_text = " ".join(important_text)
        
        if not all_text.strip():
            # Fallback to body text if no structured content found
            body = soup.find("body")
            if body:
                all_text = body.get_text(separator=" ", strip=True)
        
        if not all_text.strip():
            return ""
        
        # Clean the text
        text = " ".join(all_text.split())
        
        # Remove common noise patterns but keep meaningful content
        text = re.sub(r'\b\d{4,}\b', '', text)  # Remove long numbers (IDs, etc.)
        text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)  # Keep alphanumeric and basic punctuation
        text = " ".join(text.split())  # Normalize whitespace
        
        return text[:100000]  # Increased limit for better categorization
        
    except Exception as e:
        print(f"Text extraction failed for {url}: {e}")
        return ""


def advanced_text_preprocessing(text):
    """Advanced text preprocessing for category classification."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs but keep domain keywords
    text = re.sub(r'http[s]?://(?:www\.)?', ' ', text)
    text = re.sub(r'\.com|\.org|\.net|\.edu|\.gov', ' ', text)
    
    # Remove emails but keep text
    text = re.sub(r'\S+@\S+\.\S+', ' ', text)
    
    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', ' ', text)
    
    # Remove hex colors
    text = re.sub(r'#[0-9a-f]{3,6}\b', ' ', text)
    
    # Keep alphanumeric and important punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    
    # Remove standalone numbers
    text = re.sub(r'\b\d+\b', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def create_advanced_features(df, text_col):
    """Create comprehensive features from text for classification."""
    features = []
    
    for text in df[text_col]:
        text = str(text)
        words = text.lower().split()
        
        # Basic text statistics
        word_count = len(words)
        char_count = len(text)
        avg_word_length = char_count / max(word_count, 1)
        unique_words = len(set(words))
        unique_ratio = unique_words / max(word_count, 1)
        
        # Sentence features
        sentence_count = max(1, text.count('.') + text.count('!') + text.count('?'))
        avg_sentence_length = word_count / sentence_count
        
        # Punctuation features
        exclamation_count = text.count('!')
        question_count = text.count('?')
        comma_count = text.count(',')
        
        # Enhanced domain-specific keywords
        tech_keywords = ['software', 'technology', 'computer', 'digital', 'app', 'application',
                        'system', 'data', 'tech', 'code', 'programming', 'developer', 'api',
                        'cloud', 'server', 'database', 'algorithm', 'ai', 'machine learning']
        
        business_keywords = ['business', 'company', 'corporate', 'enterprise', 'management',
                           'finance', 'investment', 'profit', 'revenue', 'market', 'industry',
                           'strategy', 'consulting', 'service', 'solution', 'professional']
        
        ecommerce_keywords = ['shop', 'buy', 'sell', 'store', 'product', 'price', 'cart',
                             'order', 'purchase', 'shipping', 'delivery', 'discount', 'sale',
                             'customer', 'payment', 'checkout', 'wishlist', 'inventory']
        
        education_keywords = ['education', 'learn', 'learning', 'course', 'student', 'school',
                            'university', 'study', 'teach', 'teaching', 'training', 'lesson',
                            'tutorial', 'class', 'exam', 'degree', 'academic', 'research']
        
        news_keywords = ['news', 'article', 'report', 'update', 'breaking', 'latest', 'story',
                        'journalist', 'press', 'media', 'publish', 'headline', 'coverage',
                        'announced', 'revealed', 'reported', 'according', 'sources']
        
        entertainment_keywords = ['entertainment', 'movie', 'film', 'music', 'game', 'gaming',
                                'video', 'stream', 'streaming', 'watch', 'play', 'listen',
                                'show', 'series', 'episode', 'artist', 'album', 'song']
        
        social_keywords = ['social', 'friend', 'follow', 'share', 'post', 'comment', 'like',
                          'message', 'chat', 'connect', 'community', 'profile', 'feed',
                          'timeline', 'status', 'update', 'notification']
        
        health_keywords = ['health', 'medical', 'doctor', 'patient', 'hospital', 'clinic',
                          'disease', 'treatment', 'medicine', 'wellness', 'fitness', 'care',
                          'symptoms', 'diagnosis', 'therapy', 'healthy']
        
        finance_keywords = ['bank', 'banking', 'financial', 'money', 'loan', 'credit', 'debit',
                           'account', 'transaction', 'payment', 'insurance', 'investment',
                           'trading', 'stock', 'fund', 'interest', 'mortgage', 'savings']
        
        travel_keywords = ['travel', 'hotel', 'flight', 'booking', 'vacation', 'trip',
                          'destination', 'tour', 'airport', 'ticket', 'resort', 'tourist',
                          'accommodation', 'reservation', 'journey']
        
        # Calculate normalized keyword scores
        text_lower = text.lower()
        tech_score = sum(1 for word in tech_keywords if word in text_lower) / max(word_count, 1) * 100
        business_score = sum(1 for word in business_keywords if word in text_lower) / max(word_count, 1) * 100
        ecommerce_score = sum(1 for word in ecommerce_keywords if word in text_lower) / max(word_count, 1) * 100
        education_score = sum(1 for word in education_keywords if word in text_lower) / max(word_count, 1) * 100
        news_score = sum(1 for word in news_keywords if word in text_lower) / max(word_count, 1) * 100
        entertainment_score = sum(1 for word in entertainment_keywords if word in text_lower) / max(word_count, 1) * 100
        social_score = sum(1 for word in social_keywords if word in text_lower) / max(word_count, 1) * 100
        health_score = sum(1 for word in health_keywords if word in text_lower) / max(word_count, 1) * 100
        finance_score = sum(1 for word in finance_keywords if word in text_lower) / max(word_count, 1) * 100
        travel_score = sum(1 for word in travel_keywords if word in text_lower) / max(word_count, 1) * 100
        
        # Action words
        action_words = ['buy', 'sell', 'learn', 'read', 'watch', 'play', 'download', 
                       'subscribe', 'register', 'login', 'search', 'browse', 'shop']
        action_score = sum(1 for word in action_words if word in text_lower) / max(word_count, 1) * 100
        
        # Call-to-action indicators
        cta_words = ['free', 'now', 'today', 'join', 'get', 'start', 'try', 'click']
        cta_score = sum(1 for word in cta_words if word in text_lower) / max(word_count, 1) * 100
        
        features.append({
            'word_count': word_count,
            'char_count': char_count,
            'avg_word_length': avg_word_length,
            'unique_ratio': unique_ratio,
            'avg_sentence_length': avg_sentence_length,
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            'comma_count': comma_count,
            'tech_score': tech_score,
            'business_score': business_score,
            'ecommerce_score': ecommerce_score,
            'education_score': education_score,
            'news_score': news_score,
            'entertainment_score': entertainment_score,
            'social_score': social_score,
            'health_score': health_score,
            'finance_score': finance_score,
            'travel_score': travel_score,
            'action_score': action_score,
            'cta_score': cta_score
        })
    
    return pd.DataFrame(features)