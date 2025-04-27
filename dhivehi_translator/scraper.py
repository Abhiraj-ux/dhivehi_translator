import requests
from bs4 import BeautifulSoup
import re
import uuid
import concurrent.futures
import time

def scrape_website(url, preserve_html=False, timeout=10, content_type=None):
    """
    Scrape text content from any website, with special handling for Dhivehi content.
    
    Args:
        url (str): URL of the website to scrape
        preserve_html (bool): Whether to preserve HTML structure for in-place translation
        timeout (int): Timeout for the request in seconds
        content_type (str, optional): Type of content to scrape (e.g., 'academic')
        
    Returns:
        dict: Dictionary containing title, paragraphs, and HTML content if requested
    """
    try:
        # Send a GET request to the website with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the title
        title = soup.title.text.strip() if soup.title else "No title found"
        
        # Extract the main content based on common content containers
        content_containers = [
            # Wikipedia specific
            soup.find('div', {'id': 'mw-content-text'}),
            # Common content containers
            soup.find('main'),
            soup.find('article'),
            soup.find('div', {'id': 'content'}),
            soup.find('div', {'class': re.compile('content|main|article|body', re.I)}),
            # Try to find content by common class names
            soup.find('div', {'class': re.compile('post|entry|text|blog', re.I)}),
            # Fallback to body if no specific container is found
            soup.body
        ]
        
        # Use the first valid container
        content_div = next((container for container in content_containers if container), soup.body)
        
        # Get all paragraphs and headings with text content
        paragraphs = []
        for element in content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div.paragraph']):
            # Skip elements that are likely navigation, footer, etc.
            if element.parent and element.parent.name in ['nav', 'footer', 'header', 'aside']:
                continue
                
            # Skip elements with certain classes
            if element.get('class') and any(c in str(element.get('class')).lower() for c in ['nav', 'menu', 'footer', 'header', 'sidebar']):
                continue
                
            text = element.get_text().strip()
            if text and len(text) > 10:  # Only include non-empty paragraphs with reasonable length
                paragraphs.append(text)
        
        # If no paragraphs found or too few, try a more aggressive approach
        if len(paragraphs) <= 1:
            # Look for text in div elements
            for div in content_div.find_all('div'):
                # Skip elements that are likely navigation, footer, etc.
                if div.parent and div.parent.name in ['nav', 'footer', 'header', 'aside']:
                    continue
                    
                # Skip elements with certain classes
                if div.get('class') and any(c in str(div.get('class')).lower() for c in ['nav', 'menu', 'footer', 'header', 'sidebar']):
                    continue
                
                # Get direct text content (not from child elements)
                text = div.get_text().strip()
                if text and len(text) > 20 and not any(p in text for p in paragraphs):
                    paragraphs.append(text)
        
        # If still no paragraphs, get all text nodes
        if len(paragraphs) <= 1:
            for element in content_div.find_all(text=True):
                if element.parent.name not in ['script', 'style', 'meta', 'link', 'noscript']:
                    text = element.strip()
                    if text and len(text) > 20 and not any(p in text for p in paragraphs):
                        paragraphs.append(text)
        
        result = {
            'title': title,
            'paragraphs': paragraphs,
            'url': url
        }
        
        # If HTML preservation is requested, add HTML content
        if preserve_html:
            # Add unique IDs to all text elements for later translation
            html_elements = []
            
            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'a', 'button', 'li']):
                if element.string and element.string.strip():
                    element_id = f"translate-{uuid.uuid4()}"
                    element['data-translate-id'] = element_id
                    html_elements.append({
                        'id': element_id,
                        'text': element.string.strip(),
                        'tag': element.name
                    })
            
            result['html'] = str(soup)
            result['html_elements'] = html_elements
        
        return result
    
    except Exception as e:
        return {
            'error': str(e),
            'url': url
        }

def get_random_wikipedia_article():
    """
    Get a random Wikipedia article.
    
    Returns:
        str: URL of a random Wikipedia article
    """
    # For Dhivehi Wikipedia
    random_url = "https://dv.wikipedia.org/wiki/Special:Random"
    try:
        response = requests.get(random_url, allow_redirects=True, timeout=5)
        return response.url
    except:
        return "https://dv.wikipedia.org/wiki/%DE%89%DE%A6%DE%87%DE%A8_%DE%9E%DE%A6%DE%8A%DE%B0%DE%99%DE%A7"

def is_dhivehi_text(text):
    """
    Check if text contains Dhivehi characters.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains Dhivehi characters, False otherwise
    """
    # Dhivehi Unicode range (approximate)
    dhivehi_pattern = re.compile(r'[\u0780-\u07BF]')
    return bool(dhivehi_pattern.search(text))