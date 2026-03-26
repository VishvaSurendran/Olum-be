from sqlalchemy.orm import Session
from app.models import models
from app.services import firecrawl_srv
from app.services.embedding_srv import process_and_embed_markdown

def crawl_and_embed_task(url: str, tenant_id: str, db: Session):
    print(f"Starting research for {url}...")
    
    try:
        # 1. Scrape with Firecrawl
        scrape_result = firecrawl_srv.research_website(url)
        
        # Safely extract markdown from the new v2 SDK response object
        if isinstance(scrape_result, dict):
            markdown_data = scrape_result.get('markdown', '')
        else:
            markdown_data = getattr(scrape_result, 'markdown', '')
            
        if not markdown_data:
            print("Scrape failed or returned no text data.")
            return

        # 2. Chunk and Embed
        print("Chunking and generating vectors...")
        chunked_data = process_and_embed_markdown(markdown_data)
        
        # 3. Save to Database
        for chunk, vector in chunked_data:
            new_kb_entry = models.KnowledgeBase(
                tenant_id=tenant_id,
                content=chunk,
                source_url=url,
                embedding=vector
            )
            db.add(new_kb_entry)
        
        db.commit()
        print(f"Successfully processed and stored data for {tenant_id}.")
        
    except Exception as e:
        print(f"An error occurred during background task: {e}")



def process_and_embed_document_task(extracted_text: str, filename: str, tenant_id: str, db: Session):
    print(f"Starting chunking and embedding for document: {filename}...")
    
    try:
        # 1. Chunk and Embed the raw text
        chunked_data = process_and_embed_markdown(extracted_text)
        
        # 2. Save to Database
        # We use a special prefix "doc:" so we know this came from a file, not a URL
        source_identifier = f"doc:{filename}"
        
        for chunk, vector in chunked_data:
            new_kb_entry = models.KnowledgeBase(
                tenant_id=tenant_id,
                content=chunk,
                source_url=source_identifier, 
                embedding=vector
            )
            db.add(new_kb_entry)
        
        db.commit()
        print(f"Successfully processed and stored document {filename} for {tenant_id}.")
        
    except Exception as e:
        print(f"An error occurred while processing document {filename}: {e}")