"""
News and press release scraper for solar projects in India.
"""

import os
import pandas as pd
import requests
import time
import re
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils import setup_logger, clean_text
from config import DATA_SOURCES

class NewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("news")
        self.sources = DATA_SOURCES.get("news", [])
        self.search_terms = ["solar project", "solar power", "solar energy", "solar plant", "photovoltaic"]
        self.output_dir = os.path.join("data", "raw", "news")
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger = setup_logger("news_scraper")
        
        # Track scraped URLs to avoid duplicates
        self.scraped_urls = set()
        
        # Regex patterns for extracting project details
        self.patterns = {
            'capacity': r'(\d+(?:\.\d+)?)\s*(?:MW|mw|megawatt)',
            'location': r'(?:located\s+in|at|in)\s+([A-Za-z\s,]+(?:district|village|tehsil|city)?)',
            'commissioning_date': r'(?:commissioned|operational|COD|completed)(?:\s+on|\s+in|\s+by)?\s+(\w+\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})',
            'developer': r'(?:developed by|developer|owned by|promoter)\s+([A-Za-z\s]+)(?:Ltd\.?|Limited|Pvt\.?|Corporation|Corp\.?|Inc\.?)?',
        }
        
        # Headers to avoid bot detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
    def _standardize_date(self, date_str):
        """Standardize date format"""
        if not date_str:
            return None
            
        date_formats = [
            '%B %d, %Y',       # January 1, 2024
            '%d %B %Y',        # 1 January 2024
            '%Y-%m-%d',        # 2024-01-01
            '%d-%m-%Y',        # 01-01-2024
            '%d/%m/%Y',        # 01/01/2024
            '%B %Y',           # January 2024
            '%Y'               # 2024
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None

    def scrape(self):
        """Scrape solar project news from configured sources"""
        self.logger.info("Starting news scraping")
        
        all_articles = []
        all_projects = []
        
        for source in self.sources:
            try:
                self.logger.info(f"Scraping source: {source['name']}")
                articles = self._scrape_source(source)
                
                if articles:
                    # Process articles to extract project info
                    for article in articles:
                        projects = self._extract_project_info(article)
                        if projects:
                            all_projects.extend(projects)
                    
                    all_articles.extend(articles)
                    
                # Respect rate limits
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error scraping source {source['name']}: {str(e)}")
        
        # Save articles data
        if all_articles:
            articles_df = pd.DataFrame(all_articles)
            articles_file = os.path.join(self.output_dir, 'solar_news_articles.csv')
            articles_df.to_csv(articles_file, index=False)
            self.logger.info(f"Saved {len(articles_df)} articles to {articles_file}")
        
        # Save extracted projects data
        if all_projects:
            projects_df = pd.DataFrame(all_projects)
            projects_file = os.path.join(self.output_dir, 'news_extracted_projects.csv')
            projects_df.to_csv(projects_file, index=False)
            self.logger.info(f"Saved {len(projects_df)} projects to {projects_file}")
            return projects_df
        else:
            self.logger.warning("No projects extracted from news articles")
            return pd.DataFrame()

    def _scrape_source(self, source):
        """Scrape articles from a specific news source"""
        articles = []
        
        # Construct search URL
        base_url = source['url']
        search_url = source['search_pattern']
        
        # Search for each term
        for term in self.search_terms:
            try:
                url = search_url.format(term=term.replace(' ', '+'))
                self.logger.info(f"Searching: {url}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    self.logger.warning(f"Failed to fetch {url}, status code: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract article links based on source-specific selectors
                article_links = self._extract_article_links(soup, source)
                
                # Process each article
                for link in article_links[:5]:  # Limit to first 5 articles per search term
                    if link in self.scraped_urls:
                        continue
                    
                    self.scraped_urls.add(link)
                    article = self._scrape_article(link, source)
                    if article:
                        articles.append(article)
                    
                    # Respect rate limits
                    time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error searching {term} on {source['name']}: {str(e)}")
                
        return articles

    def _extract_article_links(self, soup, source):
        """Extract article links based on source-specific selectors"""
        links = []
        
        # Default generic approach
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Complete relative URLs
            if href.startswith('/'):
                href = source['url'] + href
                
            # Check if it looks like an article
            article_indicators = ['/article/', '/news/', '/press-release/', '/story/']
            if any(indicator in href for indicator in article_indicators):
                links.append(href)
                
        # Remove duplicates while preserving order
        unique_links = []
        for link in links:
            if link not in unique_links:
                unique_links.append(link)
                
        return unique_links

    def _scrape_article(self, url, source):
        """Scrape content from an article URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('h1')
            title_text = title.text.strip() if title else "No title"
            
            # Extract date - this is very site-specific and simplified here
            date = None
            date_patterns = [
                # Common date classes/IDs
                soup.find(class_=re.compile(r'(date|time|publish|post-date)')),
                soup.find(id=re.compile(r'(date|time|publish|post-date)')),
                # Look for time tag
                soup.find('time'),
                # Look for meta tags
                soup.find('meta', property='article:published_time'),
                soup.find('meta', itemprop='datePublished')
            ]
            
            for pattern in date_patterns:
                if pattern and (hasattr(pattern, 'text') or pattern.get('content')):
                    date_text = pattern.text.strip() if hasattr(pattern, 'text') else pattern.get('content', '')
                    date = self._standardize_date(date_text)
                    if date:
                        break
                        
            # If still no date, use current date
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract content - simplified
            content = ""
            main_content = soup.find(['article', 'main', 'div'], class_=re.compile(r'(content|article|story)'))
            if main_content:
                paragraphs = main_content.find_all('p')
                content = ' '.join([p.text.strip() for p in paragraphs])
            else:
                # Fallback to all paragraphs
                content = ' '.join([p.text.strip() for p in soup.find_all('p')[:20]])  # Limit to first 20
            
            return {
                'title': clean_text(title_text),
                'date': date,
                'content': clean_text(content),
                'url': url,
                'source': source['name'],
                'scrape_date': datetime.now().strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {str(e)}")
            return None

    def _extract_project_info(self, article):
        """Extract solar project information from an article"""
        if not article or not article.get('content'):
            return []
            
        content = article['content']
        projects = []
        
        # Look for capacity mentions (MW) as starting points for project identification
        capacity_matches = re.finditer(self.patterns['capacity'], content)
        
        for match in capacity_matches:
            # Extract a window of text around the capacity mention (500 chars)
            start_pos = max(0, match.start() - 250)
            end_pos = min(len(content), match.end() + 250)
            project_text = content[start_pos:end_pos]
            
            # Create project entry
            project = {
                'capacity': match.group(0),
                'capacity_mw': float(match.group(1)),  # The numeric part
                'source_type': 'news',
                'article_title': article['title'],
                'article_date': article['date'],
                'source': article['source'],
                'url': article['url'],
                'extraction_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Extract other fields
            for field, pattern in self.patterns.items():
                if field != 'capacity':  # Already extracted
                    field_match = re.search(pattern, project_text, re.IGNORECASE)
                    if field_match:
                        project[field] = clean_text(field_match.group(1))
            
            # Only include if we have enough information
            if 'location' in project or 'developer' in project:
                # Standardize commissioning date if present
                if 'commissioning_date' in project:
                    project['commissioning_date'] = self._standardize_date(project['commissioning_date'])
                projects.append(project)
        
        return projects