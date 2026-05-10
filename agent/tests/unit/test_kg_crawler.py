import pytest
from src.kg_crawler import extract_entities, categorize_event, determine_impact

def test_extract_entities():
    known_symbols = ["BTC", "ETH", "SOL"]
    text = "BTC surges past new all time high while eth lags behind. solana is not mentioned directly as SOL."
    
    entities = extract_entities(text, known_symbols)
    assert set(entities) == {"BTC", "ETH", "SOL"}

def test_categorize_event():
    assert categorize_event("Ethereum Dencun upgrade goes live") == "upgrade"
    assert categorize_event("Massive exchange hack drains millions") == "hack"
    assert categorize_event("SEC files lawsuit against exchange") == "regulation"
    assert categorize_event("Binance listing for new token") == "listing"
    assert categorize_event("Just some general market movement today") == "general"

def test_determine_impact():
    weight, direction = determine_impact("hack", "Exchange hacked")
    assert direction == "bearish"
    assert weight == 0.8
    
    weight, direction = determine_impact("upgrade", "Network upgrade")
    assert direction == "bullish"
    assert weight == 0.7
    
    weight, direction = determine_impact("general", "Market plunges")
    assert direction == "bearish"
    
    weight, direction = determine_impact("general", "Market surges")
    assert direction == "bullish"
