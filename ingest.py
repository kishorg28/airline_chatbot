import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import os

async def get_dynamic_html_async(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        await page.goto(url, wait_until="networkidle")
        html = await page.content()
        await browser.close()
        return html

async def create_knowledge_base_async(bot_id: str, urls: list[str]) -> bool:
    print(f"Starting ingestion for bot_id: {bot_id}...")
    all_text = ""
    for url in urls:
        try:
            html = await get_dynamic_html_async(url)
            soup = BeautifulSoup(html, 'html.parser')
            all_text += soup.body.get_text(separator='\n', strip=True) + "\n\n"
            print(f"Successfully scraped {url}")
        except Exception as e:
            print(f"Warning: Could not scrape {url}. Error: {e}")

    if not all_text:
        print("No text was scraped. Aborting ingestion.")
        return False

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(all_text)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(texts, embeddings)

    save_path = os.path.join("faiss_indexes", bot_id)
    os.makedirs(save_path, exist_ok=True)
    vector_store.save_local(save_path)
    print(f"Ingestion complete! Index for '{bot_id}' saved to '{save_path}'")
    return True

# Helper synchronous wrapper for easier integration in sync APIs
# Remove the synchronous wrapper from ingest.py
# Only have:

async def create_knowledge_base_async(bot_id: str, urls: list[str]) -> bool:
    # existing async code ...
    return create_knowledge_base_async(bot_id, urls)

# Example usage:
if __name__ == "__main__":
    urls = [
        "https://www.jetblue.com/flying-with-us/our-fares",
        "https://www.jetblue.com/traveling-together/traveling-with-pets"
    ]
    asyncio.run(create_knowledge_base_async("jetblue_bot", urls))
