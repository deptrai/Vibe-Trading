from __future__ import annotations

import os
import requests
import hashlib
from datetime import datetime, timezone
import logging
from typing import List, Dict, Optional

from src.kg_models import KGEvent, KGAsset
from src.kg_store import get_kg_store
from celery import shared_task

logger = logging.getLogger(__name__)

# Fallback headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# Category heuristics
CATEGORIES = {
    "upgrade": ["upgrade", "hard fork", "mainnet", "launch", "release", "v2", "v3", "dencun"],
    "hack": ["hack", "exploit", "stolen", "breach", "drained", "outage", "halted"],
    "regulation": ["sec", "lawsuit", "sued", "regulation", "etf", "approved", "banned", "illegal"],
    "listing": ["listed", "listing", "binance", "coinbase", "kraken"],
    "halving": ["halving", "halvening"],
    "depeg": ["depeg", "loss of peg"],
    "partnership": ["partner", "partnership", "integrated", "integrates", "collaboration"]
}

def extract_entities(text: str, known_symbols: List[str]) -> List[str]:
    """Simple keyword extraction for known symbols."""
    words = text.replace(',', ' ').replace('.', ' ').split()
    words_upper = [w.upper() for w in words]
    found = set()
    for symbol in known_symbols:
        if symbol.upper() in words_upper:
            found.add(symbol.upper())
    return list(found)

def categorize_event(text: str) -> str:
    """Categorize event based on keywords."""
    text_lower = text.lower()
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return "general"

def determine_impact(category: str, title: str) -> tuple[float, str]:
    """Heuristics for impact weight and direction."""
    # Basic logic
    title_lower = title.lower()
    if category in ["hack", "depeg"]:
        return 0.8, "bearish"
    elif category in ["upgrade", "listing", "partnership", "halving"]:
        return 0.7, "bullish"
    elif category == "regulation":
        if any(w in title_lower for w in ["approved", "won", "victory", "allows"]):
            return 0.8, "bullish"
        else:
            return 0.7, "bearish"
    
    # general
    if any(w in title_lower for w in ["plunges", "drops", "crash", "bear", "down"]):
        return 0.5, "bearish"
    elif any(w in title_lower for w in ["surges", "jumps", "rally", "bull", "up"]):
        return 0.5, "bullish"
        
    return 0.3, "neutral"

def fetch_cryptocompare_news() -> List[dict]:
    """Fetch news from CryptoCompare API (Primary)."""
    try:
        api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        if api_key:
            url += f"&api_key={api_key}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Guard against Error response or non-list Data
        if data.get("Response") == "Error" or not isinstance(data.get("Data"), list):
            msg = data.get("Message", "Unknown error")
            logger.warning(f"CryptoCompare API returned error: {msg}")
            return []

        parsed_events = []
        for item in data.get("Data", [])[:20]:
            ts = datetime.fromtimestamp(item["published_on"], tz=timezone.utc)
            parsed_events.append({
                "id": f"cc_{item['id']}",
                "title": item["title"],
                "source": item["source_info"]["name"],
                "url": item["url"],
                "timestamp": ts,
                "summary": item["body"]
            })
        return parsed_events
    except Exception as e:
        logger.error(f"CryptoCompare API failed: {e}")
        return []

def fetch_coingecko_news() -> List[dict]:
    """Fetch news from CoinGecko API (Fallback).

    NOTE (Phase 1 stub): CoinGecko's /news endpoint requires a paid API key
    in most regions. This function currently returns an empty list as a
    documented stub. The fallback chain is:
    CryptoCompare → CoinGecko (stub) → seed data.
    TODO(Phase 2): Implement with CoinGecko Pro API key via env var.
    """
    try:
        url = "https://api.coingecko.com/api/v3/ping"
        requests.get(url, timeout=5)
        # Stub: CoinGecko /news requires paid key — return empty for Phase 1
        return []
    except Exception as e:
        logger.warning(f"CoinGecko API unreachable: {e}")
        return []

@shared_task(name="src.kg_crawler.sync_knowledge_graph")
def sync_knowledge_graph():
    """Celery task to fetch news and update KG."""
    logger.info("Starting Knowledge Graph sync...")
    
    store = get_kg_store()
    
    # 1. Fetch news
    events_data = fetch_cryptocompare_news()
    if not events_data:
        events_data = fetch_coingecko_news()
        
    if not events_data:
        logger.warning("All news APIs failed. Skipping sync.")
        return "failed"
        
    known_symbols = list(store.assets.keys())
    new_events_count = 0
    
    # 2. Process events
    for data in events_data:
        # Dedup: Check if already exists
        if data["id"] in store.events:
            continue
            
        full_text = f"{data['title']} {data['summary']}"
        
        category = categorize_event(full_text)
        symbols = extract_entities(full_text, known_symbols)
        
        # We only add the event if it mentions a known asset (or if we want to add macro events later)
        # For Phase 1, macro is disabled
        enable_macro = os.environ.get("ENABLE_MACRO_KG", "false").lower() == "true"
        
        if not symbols and not enable_macro:
            continue
            
        event = KGEvent(
            event_id=data["id"],
            title=data["title"],
            category=category,
            source=data["source"],
            url=data["url"],
            timestamp=data["timestamp"],
            summary=data["summary"]
        )
        
        store.add_event(event)
        new_events_count += 1
        
        # 3. Add impacts
        for symbol in symbols:
            weight, direction = determine_impact(category, data["title"])
            reason = f"Event categorized as '{category}' mentioning {symbol}."
            store.add_impact(event.event_id, symbol, weight, direction, reason)
            
    if new_events_count > 0:
        store.last_sync = datetime.now(timezone.utc)
        store.save()
        logger.info(f"KG sync complete. Added {new_events_count} new events.")
    else:
        logger.info("KG sync complete. No new relevant events found.")
        
    return f"processed {len(events_data)}, added {new_events_count}"
