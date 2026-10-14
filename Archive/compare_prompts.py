import requests
from newspaper import Article

def get_article_text(url):
    print("Downloading article...")
    article = Article(url)
    article.download()
    article.parse()
    print("Article downloaded. Title:", article.title)
    print("Text length:", len(article.text))
    return article.title, article.text

def generate_newsletter_draft_two_step(title, text):
    print("Sending to Ollama...")
    messages = [
        {"role": "user", "content": f"Title: {title}\n\nArticle: {text}"},
        {"role": "user", "content": "Summarise this in 3 sentences in English for a newsletter. Base your summary only on the article text provided above."}
    ]
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:7b",
            "messages": messages,
            "stream": False
        }
    )
    print("Ollama responded.")
    return response.json()["message"]["content"]

url = "https://www.hamk.fi/julkaisut/opiskeluhyvinvointi-ammattikorkeakoulussa-opiskelijoiden-kokemuksia-voimavaroista-ja-vaatimuksista/"
title, text = get_article_text(url)
text = text[:3000] 
draft = generate_newsletter_draft_two_step(title, text)
print("=== FINAL DRAFT ===")
print(draft)