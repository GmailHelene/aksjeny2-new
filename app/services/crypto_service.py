"""Crypto service for fetching cryptocurrency data"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CryptoService:
    """Service for handling cryptocurrency data"""
    
    @staticmethod
    def _get_default_crypto_data() -> Dict[str, Any]:
        """Get default crypto data as fallback"""
        return {
            'BTC': {
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'price': 43500.00,
                'change': 1040.50,
                'change_percent': 2.45,
                'volume': 15820000000,
                'market_cap': 850000000000,
                'circulating_supply': 19500000,
                'last_update': datetime.now().isoformat()
            },
            'ETH': {
                'name': 'Ethereum',
                'symbol': 'ETH',
                'price': 2650.00,
                'change': 47.30,
                'change_percent': 1.82,
                'volume': 8920000000,
                'market_cap': 318000000000,
                'circulating_supply': 120000000,
                'last_update': datetime.now().isoformat()
            },
            'SOL': {
                'name': 'Solana',
                'symbol': 'SOL',
                'price': 98.50,
                'change': 3.90,
                'change_percent': 4.12,
                'volume': 1820000000,
                'market_cap': 44000000000,
                'circulating_supply': 446000000,
                'last_update': datetime.now().isoformat()
            }
        }

# Initialize crypto service
crypto_service = CryptoService()
