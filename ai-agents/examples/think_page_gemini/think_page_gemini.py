import argparse
import json
import os
from dotenv import load_dotenv
from extractor import extract_main_block
from think_page import preprocess_html  # 再利用
import google.generativeai as genai


def main():
    parser = argparse.ArgumentParser(description="Extract main content CSS selector from web pages (Gemini version)")
    parser.add_argument("url", help="Target web page URL")
    parser.add_argument("--format", choices=["css", "xpath"], default="css", help="Output format: CSS selector or XPath (default: css)")
    parser.add_argument("--explain", action="store_true", help="Include explanation of the selected element")
    args = parser.parse_args()

    load_dotenv()
    html = extract_main_block(args.url)
    if not html:
        print("[ERROR] Failed to extract HTML from URL")
        return

    processed_html = preprocess_html(html)

    format_instruction = "CSSセレクタ" if args.format == "css" else "XPath"
    format_examples = "main article, div#main article, .content" if args.format == "css" else "//main//article, //div[@id='main']//article"

    explain_instruction = ""
    if args.explain:
        explain_instruction = '\n- "explanation": "選択した理由の簡潔な説明"'

    prompt = f"""以下はWebページのHTMLです。記事本文（メインコンテンツ）が含まれるHTML要素を{format_instruction}で特定してください。

重要な条件:
- HTML構造内の要素パス（例: {format_examples}）を返してください
- CSSファイルのURLや外部リンクは絶対に返さないでください
- navigation、footer、sidebar以外の、記事本文を含む最適なブロックを選択してください
- 最も内容が豊富で構造的に意味のある要素を選んでください

HTML:
{processed_html}

回答形式（必ずJSONで）:
{{"path": "{format_instruction}"{explain_instruction}}}
"""

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()

    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        result = json.loads(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        import re

        json_match = re.search(r'\{"path":\s*"([^"]+)"[^}]*\}', text)
        if json_match:
            extracted = {"path": json_match.group(1)}
            if args.explain and "explanation" in text:
                exp_match = re.search(r'"explanation":\s*"([^"]+)"', text)
                if exp_match:
                    extracted["explanation"] = exp_match.group(1)
            print(json.dumps(extracted, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "Failed to parse response", "raw_output": text}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
