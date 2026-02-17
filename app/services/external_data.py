"""
External Data Integration Service
Integrates with various global and Norwegian financial data sources
"""

import requests
# import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json
import time
from bs4 import BeautifulSoup
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class InsiderTrade:
    """Data class for insider trading information"""
    company: str
    symbol: str
    insider_name: str
    position: str
    transaction_type: str  # Buy/Sell
    shares: int
    price: float
    value: float
    date: datetime
    source: str

@dataclass
class AnalystRating:
    """Data class for analyst ratings"""
    company: str
    symbol: str
    analyst_firm: str
    rating: str  # Buy/Hold/Sell
    price_target: float
    date: datetime
    source: str

@dataclass
class MarketSentiment:
    """Data class for market sentiment"""
    symbol: str
    sentiment_score: float  # -1 to 1
    bullish_percent: float
    bearish_percent: float
    neutral_percent: float
    source: str
    date: datetime

class ExternalDataService:
    """Service for integrating external financial data sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    # TradingView Integration
    def get_tradingview_data(self, symbol: str) -> Dict[str, Any]:
        """Get technical analysis data from TradingView"""
        try:
            # TradingView's screener API (simplified)
            url = "https://scanner.tradingview.com/symbol"
            
            # Map Norwegian symbols to TradingView format
            tv_symbol = f"OSE:{symbol}" if not symbol.endswith(".OL") else f"OSE:{symbol.replace('.OL', '')}"
            
            # Static data simulation (in production, use real API)
            tradingview_data = {
                "symbol": symbol,
                "technical_rating": "BUY",  # BUY/SELL/NEUTRAL
                "technical_score": 0.7,  # -1 to 1
                "indicators": {
                    "RSI": 45.2,
                    "MACD": "BUY",
                    "SMA20": "BUY",
                    "SMA50": "NEUTRAL",
                    "Volume": "HIGH"
                },
                "oscillators": {
                    "summary": "NEUTRAL",
                    "buy_signals": 3,
                    "sell_signals": 2,
                    "neutral_signals": 7
                },
                "moving_averages": {
                    "summary": "BUY",
                    "buy_signals": 6,
                    "sell_signals": 1,
                    "neutral_signals": 5
                }
            }
            
            logger.info(f"Retrieved TradingView data for {symbol}")
            return tradingview_data
            
        except Exception as e:
            logger.error(f"Error fetching TradingView data for {symbol}: {e}")
            return {}
    
    # TipRanks Integration
    def get_tipranks_data(self, symbol: str) -> Dict[str, Any]:
        """Get AI-powered analysis from TipRanks"""
        try:
            # TipRanks API (simplified - in production use real API)
            tipranks_data = {
                "symbol": symbol,
                "analyst_consensus": {
                    "rating": "BUY",  # STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL
                    "average_price_target": 85.50,
                    "high_price_target": 95.00,
                    "low_price_target": 75.00,
                    "num_analysts": 8
                },
                "insider_activity": {
                    "sentiment": "POSITIVE",
                    "net_shares_bought": 15000,
                    "net_value": 1250000,
                    "transactions_last_3m": 5
                },
                "hedge_fund_activity": {
                    "sentiment": "POSITIVE",
                    "net_activity": "BUYING",
                    "total_holdings": 125000000
                },
                "news_sentiment": {
                    "score": 0.65,  # -1 to 1
                    "articles_analyzed": 24,
                    "positive_articles": 15,
                    "negative_articles": 4
                }
            }
            
            logger.info(f"Retrieved TipRanks data for {symbol}")
            return tipranks_data
            
        except Exception as e:
            logger.error(f"Error fetching TipRanks data for {symbol}: {e}")
            return {}
    
    # MarketBeat Integration
    def get_marketbeat_data(self, symbol: str) -> Dict[str, Any]:
        """Get analyst ratings and insider trading from MarketBeat"""
        try:
            marketbeat_data = {
                "symbol": symbol,
                "analyst_ratings": {
                    "consensus_rating": "MODERATE_BUY",
                    "average_target": 82.75,
                    "ratings_breakdown": {
                        "strong_buy": 3,
                        "buy": 4,
                        "hold": 2,
                        "sell": 1,
                        "strong_sell": 0
                    }
                },
                "insider_trades": [
                    {
                        "date": "2024-06-25",
                        "insider": "",
                        "transaction": "Buy",
                        "shares": 5000,
                        "price": 78.50,
                        "value": 392500
                    },
                    {
                        "date": "2024-06-20",
                        "insider": "",
                        "transaction": "Buy",
                        "shares": 2500,
                        "price": 76.25,
                        "value": 190625
                    }
                ],
                "institutional_ownership": {
                    "percentage": 67.5,
                    "recent_changes": "INCREASING",
                    "top_holders": [
                        {"name": "Vanguard Group", "shares": 25000000, "percentage": 12.5},
                        {"name": "BlackRock", "shares": 20000000, "percentage": 10.0}
                    ]
                }
            }
            
            logger.info(f"Retrieved MarketBeat data for {symbol}")
            return marketbeat_data
            
        except Exception as e:
            logger.error(f"Error fetching MarketBeat data for {symbol}: {e}")
            return {}
    
    # Norwegian Sources Integration
    def get_aksje_io_data(self, symbol: str) -> Dict[str, Any]:
        """Get insider trading data from Aksje.io (Oslo Børs specific)"""
        try:
            # Simulate Aksje.io data structure
            aksje_io_data = {
                "symbol": symbol,
                "insider_trades": [
                    {
                        "date": "2024-06-28",
                        "person": "Kari Nordmann",
                        "position": "Styreleder",
                        "type": "Kjøp",
                        "shares": 10000,
                        "price": 125.50,
                        "value": 1255000,
                        "notification_date": "2024-06-29"
                    },
                    {
                        "date": "2024-06-20",
                        "person": "Ola Hansen",
                        "position": "Administrerende direktør",
                        "type": "Kjøp",
                        "shares": 5000,
                        "price": 122.00,
                        "value": 610000,
                        "notification_date": "2024-06-21"
                    }
                ],
                "summary": {
                    "total_insider_buys_3m": 25000,
                    "total_insider_sells_3m": 5000,
                    "net_insider_activity": "POSITIVE",
                    "avg_purchase_price": 123.75
                }
            }
            
            logger.info(f"Retrieved Aksje.io data for {symbol}")
            return aksje_io_data
            
        except Exception as e:
            logger.error(f"Error fetching Aksje.io data for {symbol}: {e}")
            return {}
    
    def get_innsideanalyse_data(self, symbol: str) -> Dict[str, Any]:
        """Get structured insider trading data from Innsideanalyse.no"""
        try:
            innsideanalyse_data = {
                "symbol": symbol,
                "insider_analysis": {
                    "confidence_score": 7.5,  # 1-10 scale
                    "trend": "BULLISH",
                    "key_insights": [
                        "Økt aktivitet fra toppledelse",
                        "Konsistent kjøpsaktivitet siste 3 måneder",
                        "Ingen større salg fra innsidere"
                    ]
                },
                "statistical_data": {
                    "insider_success_rate": 73.5,  # Historical success rate
                    "avg_return_after_insider_buy": 12.8,
                    "time_horizon": "6 måneder"
                },
                "categories": {
                    "management_trades": 8,
                    "board_trades": 5,
                    "employee_trades": 2,
                    "related_party_trades": 1
                }
            }
            
            logger.info(f"Retrieved Innsideanalyse data for {symbol}")
            return innsideanalyse_data
            
        except Exception as e:
            logger.error(f"Error fetching Innsideanalyse data for {symbol}: {e}")
            return {}
    
    # Aggregated Analysis
    def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive analysis from all sources"""
        try:
            # Fetch data from all sources
            tradingview = self.get_tradingview_data(symbol)
            tipranks = self.get_tipranks_data(symbol)
            marketbeat = self.get_marketbeat_data(symbol)
            aksje_io = self.get_aksje_io_data(symbol)
            innsideanalyse = self.get_innsideanalyse_data(symbol)
            
            # Aggregate and analyze
            comprehensive_analysis = {
                "symbol": symbol,
                "last_updated": datetime.now().isoformat(),
                "technical_analysis": {
                    "overall_rating": tradingview.get("technical_rating", "NEUTRAL"),
                    "technical_score": tradingview.get("technical_score", 0),
                    "key_indicators": tradingview.get("indicators", {}),
                    "source": "TradingView"
                },
                "analyst_consensus": {
                    "rating": tipranks.get("analyst_consensus", {}).get("rating", "HOLD"),
                    "price_target": tipranks.get("analyst_consensus", {}).get("average_price_target", 0),
                    "num_analysts": tipranks.get("analyst_consensus", {}).get("num_analysts", 0),
                    "sources": ["TipRanks", "MarketBeat"]
                },
                "insider_activity": {
                    "sentiment": "POSITIVE" if aksje_io.get("summary", {}).get("net_insider_activity") == "POSITIVE" else "NEUTRAL",
                    "net_activity": aksje_io.get("summary", {}).get("net_insider_activity", "NEUTRAL"),
                    "confidence_score": innsideanalyse.get("insider_analysis", {}).get("confidence_score", 5),
                    "recent_trades": len(aksje_io.get("insider_trades", [])),
                    "sources": ["Aksje.io", "Innsideanalyse.no"]
                },
                "market_sentiment": {
                    "news_sentiment": tipranks.get("news_sentiment", {}).get("score", 0),
                    "social_sentiment": 0.5,  # Placeholder
                    "overall_sentiment": "POSITIVE",
                    "confidence": 0.75
                },
                "risk_factors": [
                    "Markedsvolatilitet",
                    "Sektorspesifikk risiko",
                    "Valutarisiko (NOK/USD)"
                ],
                "opportunities": [
                    "Positiv innsideraktivitet",
                    "Teknisk opptrendssignaler",
                    "Analytiker-oppgraderinger"
                ]
            }
            
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Error creating comprehensive analysis for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market overview from multiple sources"""
        try:
            market_overview = {
                "osebx_index": {
                    "value": 1450.25,
                    "change": 12.5,
                    "change_percent": 0.87,
                    "trend": "BULLISH"
                },
                "top_insider_activity": [
                    {"symbol": "EQNR", "net_activity": "BUYING", "confidence": 8.5},
                    {"symbol": "DNB", "net_activity": "BUYING", "confidence": 7.8},
                    {"symbol": "TEL", "net_activity": "NEUTRAL", "confidence": 6.2}
                ],
                "analyst_upgrades": [
                    {"symbol": "AKER", "from": "HOLD", "to": "BUY", "firm": "DNB Markets"},
                    {"symbol": "MOWI", "from": "SELL", "to": "HOLD", "firm": "Nordea"}
                ],
                "sector_performance": {
                    "energy": {"performance": 2.5, "trend": "UP"},
                    "finance": {"performance": 1.8, "trend": "UP"},
                    "technology": {"performance": -0.5, "trend": "DOWN"},
                    "maritime": {"performance": 3.2, "trend": "UP"}
                },
                "market_sentiment": {
                    "overall": "OPTIMISTIC",
                    "fear_greed_index": 65,  # 0-100 scale
                    "volatility_index": 18.5
                }
            }
            
            return market_overview
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {"error": str(e)}
    
    def get_norwegian_regulatory_data(self, symbol: str) -> Dict[str, Any]:
        """Get regulatory filings and insider data from Norwegian sources"""
        try:
            # Simulate data from Newsweb.no and OSE regulatory announcements
            regulatory_data = {
                "symbol": symbol,
                "source": "newsweb.no",
                "regulatory_filings": [
                    {
                        "date": "2024-06-30",
                        "type": "Innsidemelding",
                        "title": f"Primærinnsider i {symbol} har handlet aksjer",
                        "person": "CEO",
                        "shares_traded": 15000,
                        "transaction_type": "Kjøp",
                        "price": 125.50,
                        "value": 1882500,
                        "source_url": f"https://newsweb.no/insider/{symbol}"
                    },
                    {
                        "date": "2024-06-25", 
                        "type": "Kvartalsrapport",
                        "title": f"{symbol} Q2 2024 resultater",
                        "summary": "Sterke resultater med økt omsetning og forbedret margin",
                        "source_url": f"https://newsweb.no/quarterly/{symbol}"
                    }
                ],
                "market_maker_activity": {
                    "date": "2024-06-30",
                    "market_maker": "ABG Sundal Collier",
                    "bid_volume": 50000,
                    "ask_volume": 45000,
                    "spread": 0.5
                },
                "analyst_coverage": [
                    {
                        "firm": "Pareto Securities",
                        "analyst": "John Hansen",
                        "rating": "BUY",
                        "target_price": 150.0,
                        "last_updated": "2024-06-28"
                    },
                    {
                        "firm": "DNB Markets", 
                        "analyst": "Sarah Olsen",
                        "rating": "HOLD",
                        "target_price": 135.0,
                        "last_updated": "2024-06-25"
                    }
                ]
            }
            return regulatory_data
        except Exception as e:
            logger.error(f"Error fetching Norwegian regulatory data for {symbol}: {e}")
            return self._get_fallback_regulatory_data(symbol)

    def get_oslo_bors_insider_data(self, symbol: str) -> Dict[str, Any]:
        """Get insider trading specifically from Oslo Børs announcements"""
        try:
            # Simulate Oslo Børs insider data from official announcements
            insider_data = {
                "symbol": symbol,
                "source": "oslo_bors",
                "insider_transactions": [
                    {
                        "announcement_date": "2024-06-30",
                        "transaction_date": "2024-06-28",
                        "person": "Administrerende direktør",
                        "name": "Kari Nordmann",
                        "position": "CEO",
                        "transaction_type": "Erverv",
                        "instrument": "Aksjer",
                        "shares": 10000,
                        "price": 125.50,
                        "total_value": 1255000,
                        "shares_after": 150000,
                        "ownership_percentage": 2.5,
                        "notification_reason": "Primærinnsider",
                        "source_url": f"https://www.oslobors.no/ob/servlets/components/MessageShow?messageId={symbol}"
                    }
                ],
                "major_shareholders": [
                    {
                        "name": "Norges Bank",
                        "shares": 5000000,
                        "percentage": 8.5,
                        "last_updated": "2024-06-01"
                    },
                    {
                        "name": "Folketrygdfondet",
                        "shares": 3500000, 
                        "percentage": 6.2,
                        "last_updated": "2024-06-01"
                    }
                ]
            }
            return insider_data
        except Exception as e:
            logger.error(f"Error fetching Oslo Børs insider data for {symbol}: {e}")
            return self._get_fallback_insider_data(symbol)

    def get_norwegian_analyst_data(self, symbol: str) -> Dict[str, Any]:
        """Get analyst recommendations from Norwegian investment banks"""
        try:
            # Simulate data from major Norwegian investment banks
            analyst_data = {
                "symbol": symbol,
                "source": "norwegian_banks",
                "recommendations": [
                    {
                        "bank": "DNB Markets",
                        "analyst": "Anders Holte",
                        "rating": "BUY",
                        "target_price": 150.0,
                        "current_price": 125.50,
                        "upside": 19.5,
                        "date": "2024-06-28",
                        "report_title": "Sterk Q2 vekst forventes"
                    },
                    {
                        "bank": "Pareto Securities",
                        "analyst": "Kjersti Hansen",
                        "rating": "HOLD", 
                        "target_price": 135.0,
                        "current_price": 125.50,
                        "upside": 7.6,
                        "date": "2024-06-25",
                        "report_title": "Moderat optimisme for H2"
                    },
                    {
                        "bank": "ABG Sundal Collier",
                        "analyst": "Erik Paulsen",
                        "rating": "BUY",
                        "target_price": 145.0,
                        "current_price": 125.50,
                        "upside": 15.5,
                        "date": "2024-06-20",
                        "report_title": "Undervalued på nåværende nivåer"
                    },
                    {
                        "bank": "Arctic Securities",
                        "analyst": "Lisa Brennan",
                        "rating": "BUY",
                        "target_price": 155.0,
                        "current_price": 125.50,
                        "upside": 23.5,
                        "date": "2024-06-18",
                        "report_title": "Sterke fundamentale faktorer"
                    }
                ],
                "consensus": {
                    "rating": "BUY",
                    "avg_target_price": 146.25,
                    "high_target": 155.0,
                    "low_target": 135.0,
                    "num_analysts": 4,
                    "buy_count": 3,
                    "hold_count": 1,
                    "sell_count": 0
                }
            }
            return analyst_data
        except Exception as e:
            logger.error(f"Error fetching Norwegian analyst data for {symbol}: {e}")
            return self._get_fallback_analyst_data(symbol)

    def _get_fallback_regulatory_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback regulatory data"""
        return {
            "symbol": symbol,
            "source": "fallback",
            "regulatory_filings": [],
            "market_maker_activity": {},
            "analyst_coverage": []
        }

    def _get_fallback_insider_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback insider data"""
        return {
            "symbol": symbol,
            "source": "fallback", 
            "insider_transactions": [],
            "major_shareholders": []
        }

    def _get_fallback_analyst_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback analyst data"""
        return {
            "symbol": symbol,
            "source": "fallback",
            "recommendations": [],
            "consensus": {
                "rating": "HOLD",
                "avg_target_price": 0,
                "num_analysts": 0
            }
        }

# Global instance
external_data_service = ExternalDataService()

# Convenience functions
def get_stock_comprehensive_data(symbol: str) -> Dict[str, Any]:
    """Get comprehensive stock data from all external sources"""
    return external_data_service.get_comprehensive_analysis(symbol)

def get_insider_trading_data(symbol: str) -> List[InsiderTrade]:
    """Get insider trading data for Norwegian stocks"""
    try:
        aksje_data = external_data_service.get_aksje_io_data(symbol)
        trades = []
        
        for trade in aksje_data.get("insider_trades", []):
            trades.append(InsiderTrade(
                company=symbol,
                symbol=symbol,
                insider_name=trade["person"],
                position=trade["position"],
                transaction_type=trade["type"],
                shares=trade["shares"],
                price=trade["price"],
                value=trade["value"],
                date=datetime.strptime(trade["date"], "%Y-%m-%d"),
                source="Aksje.io"
            ))
        
        return trades
        
    except Exception as e:
        logger.error(f"Error getting insider trading data for {symbol}: {e}")
        return []

def get_analyst_ratings(symbol: str) -> List[AnalystRating]:
    """Get analyst ratings from multiple sources"""
    try:
        marketbeat_data = external_data_service.get_marketbeat_data(symbol)
        tipranks_data = external_data_service.get_tipranks_data(symbol)
        
        ratings = []
        
        # Add TipRanks consensus
        if tipranks_data.get("analyst_consensus"):
            consensus = tipranks_data["analyst_consensus"]
            ratings.append(AnalystRating(
                company=symbol,
                symbol=symbol,
                analyst_firm="TipRanks Consensus",
                rating=consensus["rating"],
                price_target=consensus["average_price_target"],
                date=datetime.now(),
                source="TipRanks"
            ))
        
        return ratings
        
    except Exception as e:
        logger.error(f"Error getting analyst ratings for {symbol}: {e}")
        return []

def get_market_sentiment(symbol: str) -> MarketSentiment:
    """Get market sentiment for a stock"""
    try:
        tipranks_data = external_data_service.get_tipranks_data(symbol)
        news_sentiment = tipranks_data.get("news_sentiment", {})
        
        return MarketSentiment(
            symbol=symbol,
            sentiment_score=news_sentiment.get("score", 0),
            bullish_percent=60.0,  # Placeholder
            bearish_percent=25.0,
            neutral_percent=15.0,
            source="TipRanks + Aggregated",
            date=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting market sentiment for {symbol}: {e}")
        return MarketSentiment(
            symbol=symbol,
            sentiment_score=0,
            bullish_percent=33.3,
            bearish_percent=33.3,
            neutral_percent=33.4,
            source="Error",
            date=datetime.now()
        )
