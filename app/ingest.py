import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from langchain_community.vectorstores.faiss import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

def get_dynamic_html_selenium(url: str) -> str:
    options = Options()
    # Use the CLI headless flag instead of assigning to Options.headless to avoid type-check errors
    # Use "--headless=new" for modern Chrome; fallback to "--headless" if needed.
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Add user-agent to avoid bot blocks (optional but recommended)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        html = driver.page_source
    finally:
        driver.quit()
    return html


def create_knowledge_base_selenium(bot_id: str, urls: list[str]) -> bool:
    print(f"Starting ingestion for bot_id: {bot_id}...")
    all_text = ""
    for url in urls:
        try:
            html = get_dynamic_html_selenium(url)
            soup = BeautifulSoup(html, 'html.parser')
            if not soup.body:
                print(f"Warning: No body tag found in {url}. Skipping.")
                continue
            all_text += soup.body.get_text(separator='\n', strip=True) + "\n\n"
            print(f"Successfully scraped {url}")
            print(all_text[:500])  # Print first 500 characters for verification
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


# Example usage:
if __name__ == "__main__":
    urls = [
        "https://www.jetblue.com/flying-with-us/our-fares",
        "https://www.jetblue.com/traveling-together/traveling-with-pets"
    ]
    create_knowledge_base_selenium("jetblue_bot", urls)
