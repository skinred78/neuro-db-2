"""
PubMed E-utilities API Client

Provides search and fetch capabilities for PubMed literature.
Includes date filtering for "last N days" queries.
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class PubMedClient:
    """Client for NCBI E-utilities API (PubMed)."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: str = "lexstream@example.com", tool: str = "lexstream-poc"):
        """
        Initialize PubMed client.
        
        Args:
            email: Contact email (recommended by NCBI for tracking)
            tool: Tool name for NCBI logs
        """
        self.email = email
        self.tool = tool
    
    def search(
        self, 
        query: str, 
        retmax: int = 20, 
        days: Optional[int] = 60,
        sort: str = "relevance"
    ) -> Dict:
        """
        Search PubMed with optional date filter.
        
        Args:
            query: PubMed query string (supports field tags like [MeSH], [tiab])
            retmax: Maximum number of results to return
            days: Filter to papers published in last N days (None for no filter)
            sort: Sort order - "relevance", "pub_date", "first_author"
            
        Returns:
            {
                'count': int,  # Total matching papers
                'pmids': List[str],  # PMIDs of returned papers
                'query_translation': str  # How PubMed interpreted the query
            }
        """
        endpoint = f"{self.BASE_URL}/esearch.fcgi"
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "retmode": "json",
            "sort": sort,
            "email": self.email,
            "tool": self.tool
        }
        
        # Add date filter if specified
        if days:
            date_to = datetime.now().strftime("%Y/%m/%d")
            date_from = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
            params["datetype"] = "pdat"  # Publication date
            params["mindate"] = date_from
            params["maxdate"] = date_to
        
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json().get('esearchresult', {})
        
        return {
            'count': int(data.get('count', 0)),
            'pmids': data.get('idlist', []),
            'query_translation': data.get('querytranslation', query)
        }
    
    def fetch_abstracts(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch article details for given PMIDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of article dictionaries with title, abstract, authors, date
        """
        if not pmids:
            return []
        
        endpoint = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "email": self.email,
            "tool": self.tool
        }
        
        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        
        # Parse XML
        articles = []
        try:
            root = ET.fromstring(response.text)
            
            for article in root.findall('.//PubmedArticle'):
                pmid = article.findtext('.//PMID', '')
                title = article.findtext('.//ArticleTitle', '')
                
                # Get abstract (may have multiple parts)
                abstract_parts = article.findall('.//AbstractText')
                abstract = ' '.join(
                    (part.attrib.get('Label', '') + ': ' if part.attrib.get('Label') else '') + 
                    (part.text or '')
                    for part in abstract_parts
                )
                
                # Get authors
                authors = []
                for author in article.findall('.//Author'):
                    last = author.findtext('LastName', '')
                    first = author.findtext('ForeName', '')
                    if last:
                        authors.append(f"{last} {first}".strip())
                
                # Get publication date
                pub_date = article.findtext('.//PubDate/Year', '')
                month = article.findtext('.//PubDate/Month', '')
                if month:
                    pub_date = f"{pub_date} {month}"
                
                # Get journal
                journal = article.findtext('.//Journal/Title', '')
                
                articles.append({
                    'pmid': pmid,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'pub_date': pub_date,
                    'journal': journal
                })
        
        except ET.ParseError as e:
            print(f"XML parse error: {e}")
        
        return articles
    
    def search_and_fetch(
        self, 
        query: str, 
        retmax: int = 20, 
        days: Optional[int] = 60
    ) -> Dict:
        """
        Convenience method: search and fetch abstracts in one call.
        
        Args:
            query: PubMed query string
            retmax: Maximum results
            days: Date filter (last N days)
            
        Returns:
            {
                'count': int,
                'query_translation': str,
                'articles': List[Dict]
            }
        """
        search_result = self.search(query, retmax=retmax, days=days)
        articles = self.fetch_abstracts(search_result['pmids'])
        
        return {
            'count': search_result['count'],
            'query_translation': search_result['query_translation'],
            'articles': articles
        }


# Quick test
if __name__ == "__main__":
    client = PubMedClient()
    
    # Test search
    print("PubMed Search Test")
    print("=" * 60)
    
    # Simple MeSH search
    result = client.search("multiple sclerosis[MeSH]", retmax=5, days=60)
    print(f"\nQuery: multiple sclerosis[MeSH]")
    print(f"  Total hits: {result['count']}")
    print(f"  Returned: {len(result['pmids'])} PMIDs")
    print(f"  Query translation: {result['query_translation']}")
    
    # Fetch abstracts
    if result['pmids']:
        articles = client.fetch_abstracts(result['pmids'][:3])
        print(f"\nSample articles:")
        for art in articles:
            print(f"  - {art['title'][:60]}...")
            print(f"    PMID: {art['pmid']}, Date: {art['pub_date']}")
