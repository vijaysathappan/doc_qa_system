from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def load_and_chunk_pdf(file_path:str) -> list[dict]:
    """Load a PDF, split it into overlapping chunks 
    and return list of dicts with chunk_text , page_number and chunk_index ."""
    #step 1: load the PDF
    # PyPDFLoader reads the PDF and returns list of Document objects
    #Each Document = one page with page_content and metadata (like page number)
    loader=PyPDFLoader(file_path)
    pages=loader.load()
    #step 2: split each page into smaller chunks
    #chunk_size= max characters per chunk
    # chunk_overlap= how many characters to overlap between chunks (for context)
    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,
                                            chunk_overlap=200,
                                            length_function=len)
    chunks=splitter.split_documents(pages)
    # step 3: Format chunks for storage
    result=[]
    for index, chunk in enumerate(chunks):
        result.append({
            "chunk_text":chunk.page_content,
            "page_number":chunk.metadata.get("page",0)+1,
            "chunk_index":index
        })
    return result