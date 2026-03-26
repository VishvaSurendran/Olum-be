from langchain_text_splitters import MarkdownTextSplitter
from sentence_transformers import SentenceTransformer

# Downloads once and runs locally
model = SentenceTransformer('all-MiniLM-L6-v2')

def process_and_embed_markdown(markdown_text: str):
    """Chunks markdown and returns a list of (chunk_text, vector) tuples."""
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(markdown_text)
    embeddings = model.encode(chunks).tolist()
    
    return list(zip(chunks, embeddings))