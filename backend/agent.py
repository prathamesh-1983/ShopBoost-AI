from pathlib import Path
import json
import os
import re

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

api_key = os.getenv("OPENAI_API_KEY")

print("ENV FILE:", BASE_DIR / ".env")
print("API KEY LOADED:", bool(api_key))

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY was not found. Check backend/.env"
    )

from openai import OpenAI

client = OpenAI(api_key=api_key)

PRODUCTS_PATH = BASE_DIR.parent / "data" / "products.json"

with open(PRODUCTS_PATH, encoding="utf-8") as f:
    PRODUCTS = json.load(f)


def get_product(product_id):
    if not product_id:
        return None
    for product in PRODUCTS:
        if product.get("id") == product_id:
            return product
    return None


def extract_budget(query):
    patterns = [
        r"(?:under|below|less than)\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)",
        r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                return None
    return None


def search_products(query):
    query_lower = query.lower()
    query_words = re.findall(r"[a-z0-9]+", query_lower)
    budget = extract_budget(query_lower)
    results = []

    for product in PRODUCTS:
        name = str(product.get("name", ""))
        category = str(product.get("category", ""))
        description = str(product.get("description", ""))
        tags = " ".join(str(tag) for tag in product.get("tags", []))
        searchable_text = f"{name} {category} {description} {tags}".lower()

        score = 0

        for word in query_words:
            if len(word) >= 3 and word in searchable_text:
                score += 1

        if category.lower() in query_lower:
            score += 3

        for tag in product.get("tags", []):
            if str(tag).lower() in query_lower:
                score += 2

        try:
            price = float(product.get("price", 0))
        except (TypeError, ValueError):
            price = 0

        if budget is not None:
            if price <= budget:
                score += 4
            else:
                score -= 10

        if score > 0:
            results.append((score, product))

    results.sort(
        key=lambda item: (
            -item[0],
            -float(item[1].get("rating", 0))
        )
    )

    return [product for score, product in results[:5]]


def clean_json_output(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def run_agent(user_message):
    products = search_products(user_message)

    if not products:
        return {
            "success": False,
            "message": "I could not find a suitable product in the catalog."
        }

    product_text = json.dumps(
        products,
        indent=2,
        ensure_ascii=False
    )

    prompt = f"""
You are ShopBoost AI, an AI shopping and revenue-growth agent.

Your job is to help customers find products and increase merchant revenue
through relevant upselling.

IMPORTANT RULES:
1. Recommend only products from the supplied catalog.
2. Never invent products or prices.
3. Respect the customer's explicit budget when one is provided.
4. Never make a payment automatically.
5. Payment must always require explicit customer approval.
6. Recommend an upsell only when it is genuinely relevant.
7. Keep recommendations concise.
8. Explain why the recommendation is useful.
9. If no supplied product satisfies the customer's request, do not invent one.

Customer request:
{user_message}

Available products:
{product_text}

Return ONLY valid JSON in exactly this structure:

{{
    "recommended_product_id": "P001",
    "reason": "Why this product matches the customer",
    "upsell_product_id": "P004",
    "upsell_reason": "Why the upsell is relevant",
    "confidence": 0.95
}}
"""

    try:
        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )
        raw_output = clean_json_output(response.output_text)
    except Exception as error:
        print("OPENAI API ERROR:", repr(error))
        return {
            "success": False,
            "message": f"AI service error: {str(error)}"
        }

    try:
        result = json.loads(raw_output)
    except json.JSONDecodeError:
        print("INVALID AI JSON:", raw_output)
        return {
            "success": False,
            "message": "The AI returned an invalid response."
        }

    recommended = get_product(result.get("recommended_product_id"))
    upsell = get_product(result.get("upsell_product_id"))

    if not recommended:
        return {
            "success": False,
            "message": "AI selected an invalid product."
        }

    return {
        "success": True,
        "product": recommended,
        "reason": result.get(
            "reason",
            "This product matches your requirements."
        ),
        "upsell": upsell,
        "upsell_reason": result.get("upsell_reason", ""),
        "confidence": result.get("confidence", 0)
    }
