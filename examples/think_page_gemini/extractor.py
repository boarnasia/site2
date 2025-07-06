# src/extractor.py
import requests
from bs4 import BeautifulSoup


def extract_main_block(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.prettify()
    except Exception as e:
        print(f"[ERROR] extract_main_block failed: {e}")
        return ""
