#!/usr/bin/env python3
"""Scrape Friction article details from SciOpen."""
import requests, re, json, time, os, html as html_module

ARTICLES_FILE = 'D:/Claw/Friction/articles_parsed.json'
OUTPUT_FILE = 'D:/Claw/Friction/articles_details.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def extract_abstract(text):
    """Extract abstract from og:description meta tag."""
    m = re.search(r'<meta property="og:description" content="([^"]+)"', text)
    if not m:
        return ''
    abstract = m.group(1)
    # Decode HTML entities
    abstract = html_module.unescape(abstract)
    # Remove HTML tags
    abstract = re.sub(r'<[^>]+>', '', abstract)
    # Collapse whitespace
    abstract = re.sub(r'\s+', ' ', abstract).strip()
    # Remove leading "Abstract:" prefix
    abstract = re.sub(r'^Abstract\s*:\s*', '', abstract)
    return abstract

def extract_keywords(text):
    """Extract keywords from meta name="keywords"."""
    m = re.search(r'<meta name="keywords" content="([^"]+)"', text)
    if not m:
        return []
    kw_str = html_module.unescape(m.group(1))
    # Split by comma
    keywords = [k.strip() for k in kw_str.split(',') if k.strip()]
    return keywords

def extract_authors(text):
    """Extract authors from JSON object."""
    m = re.search(r'\{"authors":\[', text)
    if not m:
        return []
    # Find the JSON object containing authors
    start = m.start()
    # Find matching closing brace
    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start:i+1]
                try:
                    data = json.loads(json_str)
                    authors = []
                    for au in data.get('authors', []):
                        name = au.get('name', '')
                        # Remove HTML tags from name
                        name = re.sub(r'<[^>]+>', '', name).strip()
                        if name:
                            authors.append({'name': name})
                    return authors
                except json.JSONDecodeError:
                    return []
    return []

def extract_type(text):
    """Extract article type from .v4-art-info."""
    m = re.search(r'<span>\s*(Research Article|Editorial|Review Article|Review|Perspective|Cover Article|Letter|Brief Communication)\s*</span>', text)
    if m:
        t = m.group(1)
        if t == 'Review Article':
            t = 'Review'
        return t
    return ''

def extract_dates(text):
    """Extract dates from page text."""
    # Look for date patterns like "08 August 2024"
    dates = re.findall(r'(\d{1,2}\s+\w+\s+\d{4})', text)
    # Remove duplicates while preserving order
    seen = set()
    unique_dates = []
    for d in dates:
        if d not in seen:
            seen.add(d)
            unique_dates.append(d)
    return unique_dates

def extract_pdf_url(text):
    """Extract PDF URL from meta citation_pdf_url."""
    m = re.search(r'<meta name="citation_pdf_url" content="([^"]+)"', text)
    if m:
        return m.group(1)
    return ''

def extract_affiliation(authors_json):
    """Extract affiliations from authors JSON if available."""
    m = re.search(r'\{"authors":\[', text)
    if not m:
        return []
    start = m.start()
    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start:i+1]
                try:
                    data = json.loads(json_str)
                    affiliations = []
                    for au in data.get('authors', []):
                        affil = au.get('affiliation', '')
                        if affil:
                            affiliations.append(affil)
                    return affiliations
                except:
                    return []
    return []

def main():
    with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    print(f"Processing {len(articles)} articles...")
    
    results = []
    for i, art in enumerate(articles):
        doi = art['doi']
        url = f'https://www.sciopen.com/article/{doi}'
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.encoding = 'utf-8'
            text = resp.text
            
            detail = {
                'doi': doi,
                'title': art['title'],
                'abstract': extract_abstract(text),
                'keywords': extract_keywords(text),
                'authors': extract_authors(text),
                'type': extract_type(text),
                'dates': extract_dates(text),
                'pdf': extract_pdf_url(text),
                'publisher': '清华大学出版社',
                'issn': '2223-7690',
                'year': art['year'],
                'volume': art['volume'],
                'issue': art['issue'],
                'firstpage': art['firstpage'],
                'journalAndIssue': art['journalAndIssue'],
                'strPubTime': art['strPubTime'],
            }
            results.append(detail)
            
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(articles)} done")
            
            time.sleep(0.5)
        except Exception as e:
            print(f"  Error {doi}: {e}")
            results.append({
                'doi': doi,
                'title': art['title'],
                'abstract': '',
                'keywords': [],
                'authors': [],
                'type': art['type'],
                'dates': [],
                'pdf': '',
                'publisher': '清华大学出版社',
                'issn': '2223-7690',
                'year': art['year'],
                'volume': art['volume'],
                'issue': art['issue'],
                'firstpage': art['firstpage'],
                'journalAndIssue': art['journalAndIssue'],
                'strPubTime': art['strPubTime'],
            })
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(results)} articles to {OUTPUT_FILE}")
    
    # Print sample
    print("\nSample article:")
    print(json.dumps(results[0], ensure_ascii=False, indent=2)[:1500])

if __name__ == '__main__':
    main()
