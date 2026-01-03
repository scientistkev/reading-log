#!/usr/bin/env python3
"""
CLI tool for logging reading materials from URLs.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def fetch_url_content(url):
    """Fetch content from a URL and return the HTML."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='load', timeout=30000)
            # Wait a bit for any dynamic content to render
            page.wait_for_timeout(2000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        raise Exception(f"Failed to fetch URL: {e}")


def extract_text_from_html(html_content):
    """Extract readable text from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Try to find main content areas - check each and use the one with most content
    candidates = [
        soup.find('main'),
        soup.find('article'),
    ]
    # Find ALL divs matching content patterns and add them as candidates
    content_divs = soup.find_all('div', class_=re.compile(r'content|article|post|entry|text-block|transcript|body', re.I))
    candidates.extend(content_divs)
    
    text = ""
    for candidate in candidates:
        if candidate:
            candidate_text = candidate.get_text(separator=' ', strip=True)
            if len(candidate_text) > len(text):
                text = candidate_text
    
    # Fallback to body text if no good candidate found
    if len(text) < 100:
        text = soup.get_text(separator=' ', strip=True)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def count_words(text):
    """Count words in text."""
    if not text:
        return 0
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def extract_metadata(html_content, url):
    """Extract title and author from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title
    title = None
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    
    # Try to find article title in meta tags or h1
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title.get('content')
    
    h1_tag = soup.find('h1')
    if h1_tag and h1_tag.get_text(strip=True):
        title = h1_tag.get_text(strip=True)
    
    # Extract author
    author = None
    author_meta = soup.find('meta', {'name': re.compile(r'author', re.I)})
    if author_meta:
        author = author_meta.get('content')
    
    # Try to find author in common patterns
    author_tag = soup.find('span', class_=re.compile(r'author|byline', re.I))
    if author_tag:
        author = author_tag.get_text(strip=True)
    
    return title or "Untitled", author


def determine_type(word_count, url):
    """Determine if content is a book or article based on word count and URL."""
    # Books typically have much higher word counts (usually 50k+ words)
    # Articles are typically under 10k words
    # We'll use 20k as a threshold, but allow user override
    
    if word_count > 20000:
        return "book"
    else:
        return "article"


def get_file_path(content_type, base_dir="."):
    """Get the appropriate file path based on content type and current date.
    
    Checks for existing files in subdirectories (articles/, books/) first,
    then falls back to creating in the year directory.
    """
    now = datetime.now()
    year = now.year
    month_name = now.strftime("%B").lower()
    
    year_dir = Path(base_dir) / str(year)
    year_dir.mkdir(exist_ok=True)
    
    if content_type == "book":
        subdir = "books"
        filename = f"{month_name}-books.txt"
    else:
        subdir = "articles"
        filename = f"{month_name}-articles.txt"
    
    # Check if file exists in subdirectory first
    subdir_path = year_dir / subdir / filename
    if subdir_path.exists():
        return subdir_path
    
    # Check if subdirectory exists (use it even for new files)
    if (year_dir / subdir).is_dir():
        return subdir_path
    
    # Fallback to year directory
    return year_dir / filename


def format_entry(content_type, title, author, word_count, url, date, include_date_header=True):
    """Format entry according to existing file structure."""
    if content_type == "article":
        # Articles use full date format with year
        date_str = date.strftime("%B %d, %Y")
        entry = ""
        if include_date_header:
            entry = f"\n--- {date_str} ---\n\n"
        entry += f"-- Read: {title}\n"
        if author:
            entry += f"   by {author}\n"
        entry += f"   {word_count} words\n\n"
        entry += f"- {url}\n"
    else:  # book
        # Books use short date format without year
        date_str = date.strftime("%B %d")
        entry = f"\n{title}\n"
        if author:
            entry += f"   Author: {author}\n"
        entry += f"\n"
        entry += f"   Start: {date_str}\n"
        entry += f"   End: ?\n"
    
    return entry


def has_same_date_header(file_path, date_str):
    """Check if the file already contains the same date header near the end."""
    file_path = Path(file_path)
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Check the last 20 lines for the date header pattern
            # This should be enough to catch if the last entry already has this date
            pattern = f"--- {date_str} ---"
            for line in lines[-20:]:
                if pattern in line:
                    return True
            return False
    except Exception:
        return False


def append_to_file(file_path, entry):
    """Append entry to file, creating it if it doesn't exist."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and has content (for verification)
    file_exists = file_path.exists()
    existing_content_length = 0
    if file_exists:
        try:
            existing_content_length = file_path.stat().st_size
        except Exception:
            pass
    
    # Ensure entry starts with proper newline if file exists and has content
    if file_exists and existing_content_length > 0:
        # Check if file ends with newline, if not, add one before entry
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read last character to check for newline
                f.seek(max(0, existing_content_length - 1))
                last_char = f.read(1)
                if last_char and last_char != '\n':
                    # File doesn't end with newline, ensure entry starts with one
                    if not entry.startswith('\n'):
                        entry = '\n' + entry
        except Exception:
            # If we can't read, just proceed with append
            pass
    
    # Append to file using 'a' mode (append mode, creates file if it doesn't exist)
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    # Verify the file was appended to (not overwritten)
    if file_exists and existing_content_length > 0:
        try:
            new_size = file_path.stat().st_size
            if new_size < existing_content_length:
                raise Exception(f"File appears to have been truncated! Original size: {existing_content_length}, New size: {new_size}")
        except Exception as e:
            # Log warning but don't fail - the append should have worked
            print(f"Warning: Could not verify file append: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Log reading materials from URLs to your reading log.'
    )
    parser.add_argument(
        'url',
        help='URL of the article or book to log'
    )
    parser.add_argument(
        '--type',
        choices=['article', 'book'],
        help='Force content type (article or book). If not specified, will be determined automatically.'
    )
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory for reading log (default: current directory)'
    )
    
    args = parser.parse_args()
    
    print(f"Fetching content from: {args.url}")
    
    try:
        # Fetch content
        html_content = fetch_url_content(args.url)
        
        # Extract text
        text = extract_text_from_html(html_content)
        
        # Count words
        word_count = count_words(text)
        print(f"Word count: {word_count}")
        
        # Extract metadata
        title, author = extract_metadata(html_content, args.url)
        print(f"Title: {title}")
        if author:
            print(f"Author: {author}")
        
        # Determine type
        content_type = args.type or determine_type(word_count, args.url)
        print(f"Content type: {content_type}")
        
        # Get file path
        file_path = get_file_path(content_type, args.base_dir)
        print(f"Writing to: {file_path}")
        
        # Get current date
        current_date = datetime.now()
        date_str = current_date.strftime("%B %d, %Y")
        
        # Check if file already has the same date header (for articles)
        include_date_header = True
        if content_type == "article":
            include_date_header = not has_same_date_header(file_path, date_str)
        
        # Format entry
        entry = format_entry(
            content_type,
            title,
            author,
            word_count,
            args.url,
            current_date,
            include_date_header=include_date_header
        )
        
        # Append to file
        append_to_file(file_path, entry)
        
        print(f"\n✓ Successfully logged to {file_path}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
