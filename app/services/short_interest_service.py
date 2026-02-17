"""Utilities for collecting real short interest metrics from public sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .simple_cache import simple_cache

logger = logging.getLogger(__name__)


@dataclass
class ShortInterestSnapshot:
    """Normalized snapshot of short-interest metrics for a specific settlement date."""

    settlement_date: datetime
    short_interest: Optional[int]
    avg_daily_volume: Optional[int]
    days_to_cover: Optional[float]
    short_float_percent: Optional[float]
    short_ratio: Optional[float]
    source: str


class ShortInterestService:
    """Fetches short-interest information from Nasdaq and Finviz."""

    NASDAQ_ENDPOINT = (
        "https://api.nasdaq.com/api/quote/{symbol}/short-interest?assetclass=stocks"
    )
    NASDAQ_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nasdaq.com/",
        "Origin": "https://www.nasdaq.com",
        "Accept-Language": "en-US,en;q=0.9",
    }
    FINVIZ_ENDPOINT = "https://finviz.com/quote.ashx?t={symbol}"
    FINVIZ_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://finviz.com/",
    }
    CACHE_PREFIX = "short_interest_v2::"

    def __init__(self) -> None:
        self.session = requests.Session()

    def get_short_interest(self, symbol: str) -> Dict[str, Any]:
        ticker = (symbol or "").upper().strip()
        cache_key = f"{self.CACHE_PREFIX}{ticker}"
        cached = simple_cache.get(cache_key, cache_type="stock_data")
        if cached:
            return cached

        result: Dict[str, Any] = {
            "symbol": ticker,
            "current": None,
            "previous": None,
            "trend": None,
            "history": [],
            "sources": [],
            "warnings": [],
        }

        try:
            nasdaq_data = self._fetch_from_nasdaq(ticker)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning("Nasdaq short interest fetch failed for %s: %s", ticker, exc)
            nasdaq_data = None

        if not nasdaq_data and "." in ticker:
            alt_symbol = ticker.split(".", 1)[0]
            try:
                nasdaq_data = self._fetch_from_nasdaq(alt_symbol)
                if nasdaq_data:
                    nasdaq_data.setdefault("warnings", []).append(
                        "Nasdaq does not list the instrument directly; using U.S. ticker lookup."
                    )
                    result["warnings"].append(
                        "Nasdaq data fetched using fallback ticker %s." % alt_symbol
                    )
                    result["sources"].append("Nasdaq (fallback ticker)")
            except Exception as exc:  # pragma: no cover
                logger.warning("Nasdaq fallback lookup failed for %s: %s", ticker, exc)
                nasdaq_data = None

        if nasdaq_data:
            result.update({k: nasdaq_data.get(k) for k in ("current", "previous", "trend", "history")})
            result["sources"].append("Nasdaq short interest")
            if nasdaq_data.get("warnings"):
                result["warnings"].extend(nasdaq_data["warnings"])

        try:
            finviz_data = self._fetch_from_finviz(ticker)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning("Finviz scrape failed for %s: %s", ticker, exc)
            finviz_data = None

        if not finviz_data and "." in ticker:
            finviz_alt = ticker.split(".", 1)[0]
            try:
                finviz_data = self._fetch_from_finviz(finviz_alt)
                if finviz_data:
                    result["warnings"].append(
                        "Finviz does not cover suffix ticker; using base symbol %s." % finviz_alt
                    )
            except Exception as exc:  # pragma: no cover
                logger.warning("Finviz fallback lookup failed for %s: %s", ticker, exc)
                finviz_data = None

        if finviz_data:
            # Ensure current dict exists
            if result.get("current") is None:
                result["current"] = {}
            result["current"].update({
                "short_float_percent": finviz_data.get("short_float_percent"),
                "short_ratio": finviz_data.get("short_ratio"),
                "finviz_short_interest": finviz_data.get("short_interest_shares"),
            })
            result.setdefault("sources", []).append("Finviz fundamentals")
            if finviz_data.get("warnings"):
                result["warnings"].extend(finviz_data["warnings"])

        if result.get("current"):
            simple_cache.set(cache_key, result, cache_type="stock_data")
        else:
            result["warnings"].append("Ingen pålitelige short interest-data funnet for denne tickeren.")
            simple_cache.set(cache_key, result, cache_type="stock_data")

        return result

    def _fetch_from_nasdaq(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not symbol:
            return None
        url = self.NASDAQ_ENDPOINT.format(symbol=symbol)
        response = self.session.get(url, headers=self.NASDAQ_HEADERS, timeout=20)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        if not data:
            message = payload.get("message")
            logger.info("Nasdaq short interest unavailable for %s: %s", symbol, message)
            return None
        table = data.get("shortInterestTable") or {}
        rows = table.get("rows") or []
        if not rows:
            return None

        parsed_history: List[Dict[str, Any]] = []
        for raw in rows:
            snapshot = self._parse_nasdaq_row(raw)
            if snapshot:
                parsed_history.append(snapshot)

        if not parsed_history:
            return None

        current = parsed_history[0]
        previous = parsed_history[1] if len(parsed_history) > 1 else None
        trend = None
        if previous and current.get("short_interest") is not None and previous.get("short_interest") not in (None, 0):
            change = current["short_interest"] - previous["short_interest"]
            change_pct = (change / previous["short_interest"] * 100) if previous["short_interest"] else None
            trend = {
                "change": change,
                "change_percent": round(change_pct, 2) if change_pct is not None else None,
                "direction": (
                    "up" if change > 0 else "down" if change < 0 else "flat"
                ),
                "previous_settlement": previous.get("settlement_date"),
            }

        return {
            "current": current,
            "previous": previous,
            "trend": trend,
            "history": parsed_history[:12],
            "warnings": [],
        }

    def _parse_nasdaq_row(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            settlement_raw = row.get("settlementDate")
            settlement_date = (
                datetime.strptime(settlement_raw, "%m/%d/%Y") if settlement_raw else None
            )
            short_interest = self._parse_int(row.get("interest"))
            avg_volume = self._parse_int(row.get("avgDailyShareVolume"))
            days_to_cover = row.get("daysToCover")
            days_value: Optional[float]
            if isinstance(days_to_cover, (int, float)):
                days_value = float(days_to_cover)
            else:
                days_value = float(days_to_cover) if days_to_cover not in (None, "", "N/A") else None
            return {
                "settlement_date": settlement_date.date().isoformat() if settlement_date else None,
                "short_interest": short_interest,
                "avg_daily_volume": avg_volume,
                "days_to_cover": round(days_value, 3) if days_value is not None else None,
                "short_float_percent": None,
                "short_ratio": days_value,
                "source": "Nasdaq",
            }
        except Exception as exc:  # pragma: no cover
            logger.debug("Failed to parse Nasdaq row %s: %s", row, exc)
            return None

    def _fetch_from_finviz(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not symbol:
            return None
        url = self.FINVIZ_ENDPOINT.format(symbol=symbol)
        response = self.session.get(url, headers=self.FINVIZ_HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        snapshot = soup.find("table", {"class": "snapshot-table2"})
        if not snapshot:
            return None
        cells = snapshot.find_all("td")
        metrics: Dict[str, str] = {}
        for idx in range(0, len(cells), 2):
            key = cells[idx].get_text(strip=True)
            if not key:
                continue
            value = cells[idx + 1].get_text(strip=True) if idx + 1 < len(cells) else ""
            metrics[key] = value
        short_float = self._parse_percent(metrics.get("Short Float"))
        short_ratio = self._parse_float(metrics.get("Short Ratio"))
        short_interest_shares = self._parse_shares(metrics.get("Short Interest"))
        return {
            "short_float_percent": short_float,
            "short_ratio": short_ratio,
            "short_interest_shares": short_interest_shares,
            "warnings": [],
        }

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        if value in (None, "", "N/A", "NA"):
            return None
        if isinstance(value, (int, float)):
            return int(value)
        cleaned = str(value).replace(",", "").strip()
        if not cleaned:
            return None
        try:
            return int(float(cleaned))
        except ValueError:
            return None

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        if value in (None, "", "N/A", "-", "NA"):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = str(value).replace(",", "").strip().rstrip("%").strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def _parse_percent(cls, value: Any) -> Optional[float]:
        number = cls._parse_float(value)
        return number if number is None else round(number, 2)

    @staticmethod
    def _parse_shares(value: Any) -> Optional[int]:
        if value in (None, "", "N/A", "-", "NA"):
            return None
        cleaned = str(value).replace(",", "").strip().upper()
        multiplier = 1
        if cleaned.endswith("M"):
            multiplier = 1_000_000
            cleaned = cleaned[:-1]
        elif cleaned.endswith("B"):
            multiplier = 1_000_000_000
            cleaned = cleaned[:-1]
        try:
            return int(float(cleaned) * multiplier)
        except ValueError:
            return None
