from firecrawl import Firecrawl
from app.core.config import FIRECRAWL_API_KEY

app_client = Firecrawl(api_key=FIRECRAWL_API_KEY)

def research_website(url: str):
    result = app_client.scrape(url, formats=['markdown'])
    return result