
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
import urllib3

# Suppress SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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
    """
    Classify website into its SINGLE most appropriate category based on PRIMARY purpose.
    Fixed version that properly handles e-commerce and streaming sites.
    """
    try:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()
        full_url = (domain + path).lower()
    except Exception:
        domain = ""
        path = ""
        full_url = ""

    # Helper function for domain matching
    def domain_matches(target_domain, domain_to_check):
        """Check if domain matches target domain or subdomain of target."""
        if domain_to_check == target_domain:
            return True
        if domain_to_check.endswith('.' + target_domain):
            return True
        return False

    # ========== CRITICAL FIX: PROPER DOMAIN MATCHING ==========
    
    # E-commerce/Shopping - ABSOLUTE PRIORITY
    ecommerce_domains = [
        "amazon.com", "amazon.in", "amazon.co.uk", "amazon.de", "amazon.fr",
        "amazon.co.jp", "amazon.ca", "amazon.com.au", "amazon.com.br",
        "amazon.it", "amazon.es", "amazon.mx", "amazon.ae", "amazon.sg", "amazon.nl",
        "ebay.com", "ebay.in", "ebay.co.uk", 
        "flipkart.com", "walmart.com", "target.com", "etsy.com", 
        "aliexpress.com", "alibaba.com", "shopify.com", "myntra.com", 
        "bestbuy.com", "costco.com"
    ]
    
    for ecom_domain in ecommerce_domains:
        if domain_matches(ecom_domain, domain):
            return "E-commerce/Shopping"
    
    # Entertainment/Streaming - HIGH PRIORITY  
    streaming_domains = [
        "netflix.com", "hotstar.com", "primevideo.com", "disneyplus.com",
        "hulu.com", "youtube.com", "spotify.com", "zee5.com", "sonyliv.com",
        "voot.com", "mxplayer.in", "twitch.tv", "vimeo.com", "soundcloud.com",
        "hbo.com", "hbonow.com", "paramount.com", "peacock.com",
        "crunchyroll.com", "funimation.com", "amazonprime.com"
    ]
    
    for stream_domain in streaming_domains:
        if domain_matches(stream_domain, domain):
            return "Entertainment/Streaming"
    
    # Social Media/Networking
    social_domains = [
        "facebook.com", "instagram.com", "twitter.com", "x.com",
        "tiktok.com", "snapchat.com", "linkedin.com", "pinterest.com",
        "tumblr.com", "whatsapp.com", "telegram.org", "discord.com",
        "reddit.com"
    ]
    
    for social_domain in social_domains:
        if domain_matches(social_domain, domain):
            return "Social Media/Networking"
    
    # Search Engine - with proper Google service handling
    search_engine_domains = ["bing.com", "yahoo.com", "duckduckgo.com", "baidu.com", "yandex.com", "ask.com"]
    for search_domain in search_engine_domains:
        if domain_matches(search_domain, domain):
            return "Search Engine"
    
    # Google services - FIXED LOGIC
    if "google.com" in domain:
        # YouTube is streaming
        if "youtube.com" in domain or "youtu.be" in domain:
            return "Entertainment/Streaming"
        # Google Drive, Docs, etc are productivity tools
        if any(service in path for service in ["/drive", "/docs", "/sheets", "/slides", "/mail", "/calendar"]):
            return "Productivity/Tools"
        # Google Maps
        if "/maps" in path:
            return "Productivity/Tools"
        # Only classify as Search Engine for actual search or main page
        if "/search" in path or path in ["", "/"]:
            return "Search Engine"
        # Default for other Google services
        return "Technology/Software"
    
    # Gaming
    gaming_domains = [
        "steam.com", "steampowered.com", "epicgames.com", "playstation.com",
        "xbox.com", "nintendo.com", "roblox.com", "minecraft.net",
        "origin.com", "battle.net", "uplay.com"
    ]
    for game_domain in gaming_domains:
        if domain_matches(game_domain, domain):
            return "Gaming"
    
    # News/Media
    news_domains = [
        "cnn.com", "bbc.com", "bbc.co.uk", "nytimes.com", "reuters.com",
        "bloomberg.com", "theguardian.com", "wsj.com", "forbes.com",
        "ndtv.com", "indiatoday.in", "thehindu.com", "hindustantimes.com"
    ]
    for news_domain in news_domains:
        if domain_matches(news_domain, domain):
            return "News/Media"
    
    # Finance/Banking
    finance_domains = [
        "bankofamerica.com", "chase.com", "wellsfargo.com", "paypal.com",
        "stripe.com", "coinbase.com", "robinhood.com", "fidelity.com"
    ]
    for finance_domain in finance_domains:
        if domain_matches(finance_domain, domain):
            return "Finance/Banking"
    
    # Education/Learning
    education_domains = [
        "coursera.org", "udemy.com", "edx.org", "khanacademy.org",
        "duolingo.com", "tcsion.com"
    ]
    for edu_domain in education_domains:
        if domain_matches(edu_domain, domain):
            return "Education/Learning"
    
    if domain.endswith(".edu"):
        return "Education/Learning"
    
    # Technology/Software
    tech_domains = [
        "github.com", "gitlab.com", "npmjs.com", "pypi.org", "docker.com",
        "kubernetes.io", "chatgpt.com", "openai.com", "claude.ai", "anthropic.com",
        "grok.x.ai", "x.ai", "tcs.com", "microsoft.com", "apple.com",
        "oracle.com", "ibm.com"
    ]
    for tech_domain in tech_domains:
        if domain_matches(tech_domain, domain):
            return "Technology/Software"
    
    # Forums/Communities
    forum_domains = ["stackoverflow.com", "quora.com"]
    for forum_domain in forum_domains:
        if domain_matches(forum_domain, domain):
            return "Forums/Communities"
    
    # Travel/Booking
    travel_domains = ["booking.com", "expedia.com", "airbnb.com", "tripadvisor.com", "hotels.com"]
    for travel_domain in travel_domains:
        if domain_matches(travel_domain, domain):
            return "Travel/Booking"
    
    # Jobs/Careers
    jobs_domains = ["indeed.com", "monster.com", "glassdoor.com"]
    for jobs_domain in jobs_domains:
        if domain_matches(jobs_domain, domain):
            return "Jobs/Careers"
    
    if "linkedin.com" in domain and "/jobs" in path:
        return "Jobs/Careers"
    
    # Health/Medical
    health_domains = ["webmd.com", "mayoclinic.org", "healthline.com"]
    for health_domain in health_domains:
        if domain_matches(health_domain, domain):
            return "Health/Medical"
    
    # Sports
    sports_domains = ["espn.com", "nfl.com", "nba.com", "mlb.com"]
    for sports_domain in sports_domains:
        if domain_matches(sports_domain, domain):
            return "Sports"
    
    # Productivity/Tools
    productivity_domains = [
        "dropbox.com", "onedrive.com", "notion.so", "trello.com",
        "slack.com", "asana.com", "monday.com", "zoom.us", "zoom.com",
        "gmail.com", "outlook.com"
    ]
    for prod_domain in productivity_domains:
        if domain_matches(prod_domain, domain):
            return "Productivity/Tools"
    
    # ========== KEYWORD-BASED FALLBACK ==========
    # Only use keywords if no domain matched
    
    # Strong e-commerce indicators
    ecommerce_indicators = ["add to cart", "shopping cart", "buy now", "shop now", "add to bag", "checkout"]
    if any(indicator in full_url for indicator in ecommerce_indicators):
        return "E-commerce/Shopping"
    
    ecommerce_keywords = ["shop", "store", "cart", "checkout", "buy", "purchase", "product"]
    if any(kw in full_url for kw in ecommerce_keywords):
        return "E-commerce/Shopping"
    
    # Strong streaming indicators
    streaming_indicators = ["watch now", "stream now", "full episode", "season", "trailer", "episode"]
    if any(indicator in full_url for indicator in streaming_indicators):
        return "Entertainment/Streaming"
    
    streaming_keywords = ["watch", "stream", "movie", "video", "series", "tv shows"]
    if any(kw in full_url for kw in streaming_keywords):
        return "Entertainment/Streaming"
    
    # Other categories (unchanged)
    if "game" in full_url:
        return "Gaming"
    
    news_keywords = ["news", "press", "journal", "article"]
    if any(kw in full_url for kw in news_keywords):
        return "News/Media"
    
    finance_keywords = ["bank", "finance", "credit", "loan", "investment"]
    if any(kw in full_url for kw in finance_keywords):
        return "Finance/Banking"
    
    education_keywords = ["university", "college", "school", "course", "learn", "tutorial"]
    if any(kw in full_url for kw in education_keywords):
        return "Education/Learning"
    
    health_keywords = ["health", "medical", "hospital", "clinic", "doctor", "patient"]
    if any(kw in full_url for kw in health_keywords):
        return "Health/Medical"
    
    travel_keywords = ["travel", "flight", "hotel", "vacation", "trip"]
    if any(kw in full_url for kw in travel_keywords):
        return "Travel/Booking"
    
    if domain.endswith(".gov") or "government" in full_url:
        return "Government/Public Services"
    
    # Fallback
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
        
        # Technology/Software keywords - PRIMARY purpose indicators
        tech_kw = ['software', 'technology', 'computer', 'digital', 'app', 'application',
                   'code', 'programming', 'developer', 'api', 'cloud', 'data', 'ai', 'ml',
                   'algorithm', 'system', 'platform', 'tech']
        tech_score = sum(1 for w in tech_kw if w in text_lower)
        
        # Productivity/Tools keywords - PRIMARY purpose indicators
        productivity_kw = ['productivity', 'tool', 'utility', 'task', 'project', 'management',
                          'organize', 'schedule', 'calendar', 'note', 'document', 'workspace']
        productivity_score = sum(1 for w in productivity_kw if w in text_lower)
        
        # E-commerce/Shopping keywords - PRIMARY purpose indicators
        ecom_kw = ['shop', 'buy', 'sell', 'product', 'price', 'cart', 'order', 'purchase',
                   'shipping', 'delivery', 'discount', 'sale', 'payment', 'checkout',
                   'store', 'marketplace', 'retail']
        ecom_score = sum(1 for w in ecom_kw if w in text_lower)
        
        # Education/Learning keywords - PRIMARY purpose indicators
        edu_kw = ['education', 'learn', 'learning', 'course', 'student', 'school', 'university',
                  'college', 'study', 'teach', 'teaching', 'training', 'lesson', 'tutorial',
                  'academic', 'research', 'curriculum', 'degree']
        edu_score = sum(1 for w in edu_kw if w in text_lower)
        
        # News/Media keywords - PRIMARY purpose indicators (journalism)
        news_kw = ['news', 'article', 'report', 'story', 'journalist', 'journalism', 'breaking',
                   'latest', 'update', 'announced', 'revealed', 'press', 'media', 'coverage',
                   'headline', 'publish', 'editorial']
        news_score = sum(1 for w in news_kw if w in text_lower)
        
        # Entertainment/Streaming keywords - PRIMARY purpose indicators
        ent_kw = ['entertainment', 'movie', 'film', 'music', 'video', 'stream', 'streaming',
                  'watch', 'play', 'show', 'series', 'episode', 'artist', 'album', 'song',
                  'netflix', 'youtube', 'spotify', 'podcast']
        ent_score = sum(1 for w in ent_kw if w in text_lower)
        
        # Social Media/Networking keywords - PRIMARY purpose indicators
        social_kw = ['social', 'friend', 'follow', 'share', 'post', 'comment', 'like',
                     'message', 'chat', 'connect', 'community', 'profile', 'feed', 'timeline',
                     'network', 'social media']
        social_score = sum(1 for w in social_kw if w in text_lower)
        
        # Health/Medical keywords - PRIMARY purpose indicators
        health_kw = ['health', 'medical', 'doctor', 'physician', 'patient', 'hospital', 'clinic',
                     'treatment', 'medicine', 'wellness', 'fitness', 'care', 'symptoms',
                     'diagnosis', 'therapy', 'healthcare']
        health_score = sum(1 for w in health_kw if w in text_lower)
        
        # Finance/Banking keywords - PRIMARY purpose indicators
        finance_kw = ['bank', 'banking', 'financial', 'money', 'loan', 'credit', 'debit',
                      'account', 'transaction', 'payment', 'insurance', 'investment', 'trading',
                      'stock', 'fund', 'interest', 'mortgage', 'savings']
        finance_score = sum(1 for w in finance_kw if w in text_lower)
        
        # Travel/Booking keywords - PRIMARY purpose indicators
        travel_kw = ['travel', 'hotel', 'flight', 'booking', 'vacation', 'trip', 'tour',
                     'destination', 'resort', 'tourist', 'accommodation', 'reservation', 'journey']
        travel_score = sum(1 for w in travel_kw if w in text_lower)
        
        # Gaming keywords - PRIMARY purpose indicators
        gaming_kw = ['game', 'gaming', 'gamer', 'play', 'player', 'video game', 'console',
                     'steam', 'nintendo', 'xbox', 'playstation', 'gaming platform']
        gaming_score = sum(1 for w in gaming_kw if w in text_lower)
        
        # Sports keywords - PRIMARY purpose indicators
        sports_kw = ['sports', 'sport', 'athletic', 'athlete', 'team', 'match', 'game',
                    'football', 'basketball', 'baseball', 'soccer', 'score', 'league']
        sports_score = sum(1 for w in sports_kw if w in text_lower)
        
        # Food/Recipes keywords - PRIMARY purpose indicators
        food_kw = ['food', 'recipe', 'cooking', 'cook', 'restaurant', 'meal', 'dish',
                   'cuisine', 'ingredient', 'kitchen', 'dining', 'delivery']
        food_score = sum(1 for w in food_kw if w in text_lower)
        
        # Real Estate keywords - PRIMARY purpose indicators
        realestate_kw = ['real estate', 'property', 'house', 'home', 'apartment', 'rent',
                         'lease', 'mortgage', 'listing', 'realtor', 'buyer', 'seller']
        realestate_score = sum(1 for w in realestate_kw if w in text_lower)
        
        # Jobs/Careers keywords - PRIMARY purpose indicators
        jobs_kw = ['job', 'career', 'employment', 'hire', 'hiring', 'recruitment', 'resume',
                   'application', 'interview', 'position', 'opportunity', 'work']
        jobs_score = sum(1 for w in jobs_kw if w in text_lower)
        
        # Forums/Communities keywords - PRIMARY purpose indicators
        forum_kw = ['forum', 'discussion', 'community', 'qa', 'question', 'answer', 'thread',
                    'post', 'reply', 'discuss', 'debate']
        forum_score = sum(1 for w in forum_kw if w in text_lower)
        
        # Search Engine keywords - PRIMARY purpose indicators
        search_kw = ['search', 'query', 'results', 'index', 'crawl', 'engine', 'find']
        search_score = sum(1 for w in search_kw if w in text_lower)
        
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
            'productivity_score': productivity_score / norm,
            'ecommerce_score': ecom_score / norm,
            'education_score': edu_score / norm,
            'news_score': news_score / norm,
            'entertainment_score': ent_score / norm,
            'social_score': social_score / norm,
            'health_score': health_score / norm,
            'finance_score': finance_score / norm,
            'travel_score': travel_score / norm,
            'gaming_score': gaming_score / norm,
            'sports_score': sports_score / norm,
            'food_score': food_score / norm,
            'realestate_score': realestate_score / norm,
            'jobs_score': jobs_score / norm,
            'forum_score': forum_score / norm,
            'search_score': search_score / norm,
            'action_score': sum(1 for w in ['buy', 'sell', 'learn', 'read', 'watch'] if w in text_lower) / norm,
            'cta_score': sum(1 for w in ['free', 'now', 'join', 'get', 'start'] if w in text_lower) / norm
        })
    
    return pd.DataFrame(features)
