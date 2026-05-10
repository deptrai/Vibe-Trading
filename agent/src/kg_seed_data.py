from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from src.kg_models import KGEvent, KGAsset
from src.kg_store import get_kg_store

logger = logging.getLogger(__name__)

def seed_knowledge_graph():
    store = get_kg_store()
    
    # Check if graph already has data
    if len(store.assets) > 0 or len(store.events) > 0:
        return

    logger.info("Seeding Knowledge Graph with initial data...")

    # Subtask 3.1: Top 20 crypto assets
    assets = [
        KGAsset(asset_id="BTC", symbol="BTC", name="Bitcoin"),
        KGAsset(asset_id="ETH", symbol="ETH", name="Ethereum"),
        KGAsset(asset_id="USDT", symbol="USDT", name="Tether"),
        KGAsset(asset_id="BNB", symbol="BNB", name="BNB"),
        KGAsset(asset_id="SOL", symbol="SOL", name="Solana"),
        KGAsset(asset_id="USDC", symbol="USDC", name="USD Coin"),
        KGAsset(asset_id="XRP", symbol="XRP", name="XRP"),
        KGAsset(asset_id="DOGE", symbol="DOGE", name="Dogecoin"),
        KGAsset(asset_id="TON", symbol="TON", name="Toncoin"),
        KGAsset(asset_id="ADA", symbol="ADA", name="Cardano"),
        KGAsset(asset_id="SHIB", symbol="SHIB", name="Shiba Inu"),
        KGAsset(asset_id="AVAX", symbol="AVAX", name="Avalanche"),
        KGAsset(asset_id="DOT", symbol="DOT", name="Polkadot"),
        KGAsset(asset_id="BCH", symbol="BCH", name="Bitcoin Cash"),
        KGAsset(asset_id="TRX", symbol="TRX", name="TRON"),
        KGAsset(asset_id="LINK", symbol="LINK", name="Chainlink"),
        KGAsset(asset_id="MATIC", symbol="MATIC", name="Polygon"),
        KGAsset(asset_id="NEAR", symbol="NEAR", name="NEAR Protocol"),
        KGAsset(asset_id="LTC", symbol="LTC", name="Litecoin"),
        KGAsset(asset_id="ICP", symbol="ICP", name="Internet Computer")
    ]

    for asset in assets:
        store.add_asset(asset)

    # Subtask 3.3: Pre-built asset correlations
    correlations = [
        ("BTC", "ETH", 0.85, "market_leaders"),
        ("SOL", "ETH", 0.75, "l1_competition"),
        ("SOL", "AVAX", 0.80, "l1_basket"),
        ("ADA", "DOT", 0.70, "l1_basket"),
        ("USDT", "USDC", 0.99, "stablecoins"),
        ("DOGE", "SHIB", 0.90, "memecoins"),
        ("MATIC", "ETH", 0.85, "l2_ecosystem"),
    ]
    
    for asset_a, asset_b, weight, category in correlations:
        store.add_correlation(asset_a, asset_b, weight, category)

    # Subtask 3.2: 10 historical crypto events
    now = datetime.now(timezone.utc)
    
    events_data = [
        {
            "id": "evt_btc_etf",
            "title": "SEC Approves Spot Bitcoin ETFs",
            "category": "regulation",
            "source": "Seed Data",
            "timestamp": now - timedelta(days=30),
            "summary": "The SEC has approved the first spot Bitcoin ETFs in the US.",
            "impacts": [("BTC", 0.9, "bullish", "Direct institutional inflow"), ("ETH", 0.6, "bullish", "Anticipation of ETH ETF")]
        },
        {
            "id": "evt_eth_dencun",
            "title": "Ethereum Dencun Upgrade Goes Live",
            "category": "upgrade",
            "source": "Seed Data",
            "timestamp": now - timedelta(days=25),
            "summary": "The Dencun upgrade significantly reduces L2 fees via proto-danksharding.",
            "impacts": [("ETH", 0.8, "bullish", "Network deflation and improved L2 economics"), ("MATIC", 0.7, "bullish", "Direct beneficiary of reduced L2 fees")]
        },
        {
            "id": "evt_sol_outage",
            "title": "Solana Network Experiences 5-Hour Outage",
            "category": "hack", # using hack/issue category
            "source": "Seed Data",
            "timestamp": now - timedelta(days=20),
            "summary": "Mainnet beta halted due to performance degradation.",
            "impacts": [("SOL", 0.8, "bearish", "Network instability concerns"), ("ETH", 0.4, "bullish", "Capital rotation to competing L1")]
        },
        {
            "id": "evt_btc_halving",
            "title": "Bitcoin Halving 2024 Completed",
            "category": "halving",
            "source": "Seed Data",
            "timestamp": now - timedelta(days=15),
            "summary": "Block reward reduced from 6.25 to 3.125 BTC.",
            "impacts": [("BTC", 0.9, "bullish", "Supply shock and historical post-halving performance")]
        },
        {
            "id": "evt_binance_sec",
            "title": "SEC Lawsuit Against Binance Intensifies",
            "category": "regulation",
            "source": "Seed Data",
            "timestamp": now - timedelta(days=10),
            "summary": "New allegations point to commingling of customer funds.",
            "impacts": [("BNB", 0.8, "bearish", "Regulatory risk for exchange token"), ("BTC", 0.3, "bearish", "General market FUD")]
        },
        {
            "id": "evt_usdc_depeg",
            "title": "USDC Briefly Depegs Following Bank Run",
            "category": "depeg",
            "source": "Seed Data",
            "timestamp": now - timedelta(days=5),
            "summary": "Circle reserves temporarily locked in distressed bank.",
            "impacts": [("USDC", 0.9, "bearish", "Loss of peg confidence"), ("USDT", 0.8, "bullish", "Flight to alternative stablecoin")]
        },
        {
            "id": "evt_doge_twitter",
            "title": "Twitter Replaces Logo with Doge Temporarily",
            "category": "partnership",
            "source": "Seed Data",
            "timestamp": now - timedelta(days=2),
            "summary": "Elon Musk temporarily changes Twitter UI to feature Dogecoin.",
            "impacts": [("DOGE", 0.9, "bullish", "Massive retail exposure and speculation"), ("SHIB", 0.5, "bullish", "Sympathetic memecoin pump")]
        },
        {
            "id": "evt_ada_smart_contracts",
            "title": "Cardano Deploys Plutus V3",
            "category": "upgrade",
            "source": "Seed Data",
            "timestamp": now - timedelta(days=1),
            "summary": "Major smart contract capability upgrade for Cardano.",
            "impacts": [("ADA", 0.7, "bullish", "Improved ecosystem capabilities")]
        },
        {
            "id": "evt_xrp_lawsuit",
            "title": "Ripple Scores Partial Victory Against SEC",
            "category": "regulation",
            "source": "Seed Data",
            "timestamp": now - timedelta(hours=12),
            "summary": "Judge rules programmatic sales of XRP are not securities.",
            "impacts": [("XRP", 0.9, "bullish", "Regulatory clarity"), ("ADA", 0.4, "bullish", "Positive precedent for other altcoins")]
        },
        {
            "id": "evt_link_ccip",
            "title": "Chainlink CCIP Goes Live on Mainnet",
            "category": "upgrade",
            "source": "Seed Data",
            "timestamp": now - timedelta(hours=2),
            "summary": "Cross-Chain Interoperability Protocol launched for enterprise users.",
            "impacts": [("LINK", 0.8, "bullish", "Major fundamental utility milestone")]
        }
    ]

    for data in events_data:
        event = KGEvent(
            event_id=data["id"],
            title=data["title"],
            category=data["category"],
            source=data["source"],
            timestamp=data["timestamp"],
            summary=data["summary"]
        )
        store.add_event(event)
        
        for asset_id, weight, direction, reason in data["impacts"]:
            store.add_impact(event.event_id, asset_id, weight, direction, reason)
            
    store.save()
    logger.info("Knowledge Graph seeded successfully.")
    
if __name__ == "__main__":
    seed_knowledge_graph()
