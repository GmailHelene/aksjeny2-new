from flask import Blueprint, render_template, request
from flask_login import current_user
# import yfinance as yf  # Disabled for demo stability
# import pandas as pd
# import numpy as np
from ..utils.access_control import access_required
import logging

logger = logging.getLogger(__name__)

# Force demo mode to avoid Yahoo Finance rate limiting
DEMO_MODE = True

class BuffettAnalyzer:
    """Warren Buffett style investment analysis"""
    
    @staticmethod
    def analyze_stock(symbol):
        """Perform comprehensive Buffett analysis on a stock"""
        if not symbol:
            logger.error("No symbol provided for Buffett analysis")
            return None
            
        try:
            # Normalize symbol
            symbol = symbol.strip().upper()
            if not symbol.replace('.', '').replace('-', '').isalnum():
                logger.error(f"Invalid symbol format: {symbol}")
                return None
                
            logger.info(f"Performing Buffett analysis for {symbol}")
            
            # Always use stable demo data implementation
            analysis = BuffettAnalyzer._get_demo_analysis(symbol)
            
            # Validate the analysis result
            if not analysis or not isinstance(analysis, dict):
                logger.error(f"Invalid analysis result for {symbol}")
                return None
                
            # Make sure required fields are present
            required_fields = ['buffett_score', 'metrics', 'scores']
            if not all(field in analysis for field in required_fields):
                logger.error(f"Missing required fields in analysis for {symbol}")
                return None
                
            # Validate all numeric values are proper numbers
            numeric_fields = [
                analysis['buffett_score'],
                *analysis['metrics'].values(),
                *analysis['scores'].values()
            ]
            
            if not all(isinstance(x, (int, float)) for x in numeric_fields):
                logger.error(f"Invalid numeric values in analysis for {symbol}")
                return None
                
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing Buffett analysis for {symbol}: {e}")
            return None
    
    @staticmethod
    def _get_demo_analysis(symbol):
        """Generate demo Buffett analysis data"""
        import random
        from datetime import datetime
        
        # Use symbol to generate consistent pseudo-random data
        random.seed(sum(ord(c) for c in symbol))
        
        # Define base metrics by company type
        base_metrics = {
            # Technology companies
            'TECH': {
                'base_pe': 25.0,
                'base_roe': 20.0,
                'base_debt': 0.25,
                'base_margin': 25.0,
                'base_growth': 15.0
            },
            # Oil & Energy companies
            'ENERGY': {
                'base_pe': 12.0,
                'base_roe': 12.0,
                'base_debt': 0.40,
                'base_margin': 15.0,
                'base_growth': 8.0
            },
            # Financial companies
            'FINANCE': {
                'base_pe': 15.0,
                'base_roe': 15.0,
                'base_debt': 0.50,
                'base_margin': 20.0,
                'base_growth': 10.0
            },
            # Consumer goods
            'CONSUMER': {
                'base_pe': 20.0,
                'base_roe': 18.0,
                'base_debt': 0.35,
                'base_margin': 12.0,
                'base_growth': 7.0
            }
        }
        
        # Determine company type from symbol
        if symbol in ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA']:
            company_type = 'TECH'
        elif symbol in ['EQNR.OL', 'XOM', 'CVX', 'BP.L']:
            company_type = 'ENERGY'
        elif symbol in ['DNB.OL', 'JPM', 'BAC', 'GS']:
            company_type = 'FINANCE'
        else:
            company_type = 'CONSUMER'
            
        # Get base metrics for this company type
        base = base_metrics[company_type]
        
        # Calculate key metrics with controlled randomization
        def random_variation(base_value, variation_pct=0.15):
            variation = base_value * variation_pct
            return base_value + random.uniform(-variation, variation)
            
        metrics = {
            'pe_ratio': round(random_variation(base['base_pe']), 1),
            'price_to_book': round(random_variation(3.0), 2),
            'debt_to_equity': round(random_variation(base['base_debt']), 2),
            'current_ratio': round(random_variation(1.8), 2),
            'roe': round(random_variation(base['base_roe']), 1),
            'roa': round(random_variation(base['base_roe'] * 0.6), 1),
            'profit_margin': round(random_variation(base['base_margin']), 1),
            'operating_margin': round(random_variation(base['base_margin'] * 1.2), 1),
            'revenue_growth': round(random_variation(base['base_growth']), 1),
            'earnings_growth': round(random_variation(base['base_growth'] * 1.1), 1),
            'free_cash_flow': round(random_variation(base['base_margin'] * 0.8), 1),
            'dividend_yield': round(max(0, random_variation(3.0)), 2),
            'payout_ratio': round(max(0, random_variation(45.0)), 1),
            'interest_coverage': round(max(2, random_variation(8.0)), 1)
        }
        
        # Calculate Buffett-style score components (0-100 for each)
        scores = {}
        
        # Business Understanding Score (Qualitative)
        # Based on sector and operating metrics
        business_score = 0
        if metrics['operating_margin'] > 20:  # Strong margins indicate simple, understandable business
            business_score = 100
        elif metrics['operating_margin'] > 15:
            business_score = 80
        elif metrics['operating_margin'] > 10:
            business_score = 60
        elif metrics['operating_margin'] > 5:
            business_score = 40
        else:
            business_score = 20
        scores['business'] = business_score
        
        # Competitive Advantage (Moat) Score
        moat_score = 0
        # High margins and returns indicate strong moat
        if (metrics['operating_margin'] > 20 and metrics['roe'] > 15 and
            metrics['profit_margin'] > 15):
            moat_score = 100
        elif (metrics['operating_margin'] > 15 and metrics['roe'] > 12 and
              metrics['profit_margin'] > 10):
            moat_score = 80
        elif (metrics['operating_margin'] > 10 and metrics['roe'] > 10 and
              metrics['profit_margin'] > 8):
            moat_score = 60
        elif (metrics['operating_margin'] > 5 and metrics['roe'] > 8 and
              metrics['profit_margin'] > 5):
            moat_score = 40
        else:
            moat_score = 20
        scores['moat'] = moat_score
        
        # Management Quality Score
        management_score = 0
        # Based on capital allocation and returns
        if (metrics['roe'] > 15 and metrics['roa'] > 7 and
            metrics['debt_to_equity'] < 0.5 and metrics['payout_ratio'] < 75):
            management_score = 100
        elif (metrics['roe'] > 12 and metrics['roa'] > 5 and
              metrics['debt_to_equity'] < 0.8 and metrics['payout_ratio'] < 85):
            management_score = 80
        elif (metrics['roe'] > 10 and metrics['roa'] > 4 and
              metrics['debt_to_equity'] < 1.0):
            management_score = 60
        elif (metrics['roe'] > 8 and metrics['roa'] > 3):
            management_score = 40
        else:
            management_score = 20
        scores['management'] = management_score
        
        # Financial Health Score
        fin_health_score = 0
        # Conservative financial position
        if (metrics['debt_to_equity'] < 0.3 and metrics['current_ratio'] > 2 and
            metrics['interest_coverage'] > 10):
            fin_health_score = 100
        elif (metrics['debt_to_equity'] < 0.5 and metrics['current_ratio'] > 1.5 and
              metrics['interest_coverage'] > 8):
            fin_health_score = 80
        elif (metrics['debt_to_equity'] < 0.8 and metrics['current_ratio'] > 1.2 and
              metrics['interest_coverage'] > 5):
            fin_health_score = 60
        elif (metrics['debt_to_equity'] < 1.2 and metrics['current_ratio'] > 1.0 and
              metrics['interest_coverage'] > 3):
            fin_health_score = 40
        else:
            fin_health_score = 20
        scores['financial_health'] = fin_health_score
        
        # Growth Prospects Score
        growth_score = 0
        # Consistent earnings growth
        if (metrics['earnings_growth'] > 12 and metrics['revenue_growth'] > 10 and
            metrics['free_cash_flow'] > 12):
            growth_score = 100
        elif (metrics['earnings_growth'] > 8 and metrics['revenue_growth'] > 7 and
              metrics['free_cash_flow'] > 8):
            growth_score = 80
        elif (metrics['earnings_growth'] > 5 and metrics['revenue_growth'] > 5 and
              metrics['free_cash_flow'] > 5):
            growth_score = 60
        elif (metrics['earnings_growth'] > 3 and metrics['revenue_growth'] > 3):
            growth_score = 40
        else:
            growth_score = 20
        scores['growth'] = growth_score
        
        # Valuation Score
        valuation_score = 0
        # Conservative valuation metrics
        if (metrics['pe_ratio'] < 15 and metrics['price_to_book'] < 1.5):
            valuation_score = 100
        elif (metrics['pe_ratio'] < 20 and metrics['price_to_book'] < 2.5):
            valuation_score = 80
        elif (metrics['pe_ratio'] < 25 and metrics['price_to_book'] < 3.5):
            valuation_score = 60
        elif (metrics['pe_ratio'] < 30 and metrics['price_to_book'] < 4.5):
            valuation_score = 40
        else:
            valuation_score = 20
        scores['valuation'] = valuation_score
        
        # Calculate overall Buffett score (weighted average)
        # Weights based on Buffett's investment philosophy
        weights = {
            'business': 0.15,      # Simple, understandable business
            'moat': 0.25,          # Strong competitive advantage
            'management': 0.15,    # Good management
            'financial_health': 0.20,  # Strong financials
            'growth': 0.15,        # Consistent growth
            'valuation': 0.10      # Fair price
        }
        
        # Calculate overall Buffett score
        buffett_score = sum(scores[k] * weights[k] for k in weights)
        
        # Generate insights based on scores
        strengths = []
        weaknesses = []
        insights = []
        
        # Business Understanding
        if scores['business'] >= 70:
            strengths.append('Enkel og forståelig forretningsmodell')
            insights.append('Selskapet har en klar og transparent forretningsmodell')
        elif scores['business'] < 40:
            weaknesses.append('Kompleks eller uklar forretningsmodell')
            insights.append('Forretningsmodellen er kompleks og kan være vanskelig å forstå')
            
        # Competitive Advantage
        if scores['moat'] >= 70:
            strengths.append('Sterk konkurransemessig fordel')
            insights.append('Selskapet har en solid markedsposisjon med høye marginer')
        elif scores['moat'] < 40:
            weaknesses.append('Svak konkurranseposisjon')
            insights.append('Selskapet mangler tydelige konkurransefortrinn')
            
        # Management
        if scores['management'] >= 70:
            strengths.append('Dyktig ledelse med god kapitalallokering')
            insights.append('Ledelsen viser god evne til å generere avkastning på investert kapital')
        elif scores['management'] < 40:
            weaknesses.append('Svak avkastning på investert kapital')
            insights.append('Ledelsen har ikke vist god evne til effektiv kapitalallokering')
            
        # Financial Health
        if scores['financial_health'] >= 70:
            strengths.append('Solid finansiell posisjon')
            insights.append('Selskapet har en konservativ finansiell struktur med lav gjeld')
        elif scores['financial_health'] < 40:
            weaknesses.append('Svak finansiell posisjon')
            insights.append('Den finansielle posisjonen gir grunn til bekymring')
            
        # Growth
        if scores['growth'] >= 70:
            strengths.append('Stabil og lønnsom vekst')
            insights.append('Selskapet viser konsistent vekst i inntjening og kontantstrøm')
        elif scores['growth'] < 40:
            weaknesses.append('Svak eller ustabil vekst')
            insights.append('Veksten er enten for lav eller for uforutsigbar')
            
        # Valuation
        if scores['valuation'] >= 70:
            strengths.append('Attraktiv verdsettelse')
            insights.append('Aksjen handles til en fornuftig pris i forhold til verdien')
        elif scores['valuation'] < 40:
            weaknesses.append('Høy verdsettelse')
            insights.append('Aksjen virker dyr basert på fundamentale faktorer')
        
        # Generate Buffett-style recommendation
        if buffett_score >= 80:
            recommendation = {
                'action': 'STRONG BUY',
                'norwegian': 'STERKT KJØP',
                'reasoning': 'Selskapet oppfyller de fleste av Warren Buffetts investeringskriterier',
                'confidence': 90
            }
        elif buffett_score >= 70:
            recommendation = {
                'action': 'BUY',
                'norwegian': 'KJØP',
                'reasoning': 'Selskapet oppfyller mange viktige investeringskriterier',
                'confidence': 75
            }
        elif buffett_score >= 60:
            recommendation = {
                'action': 'HOLD',
                'norwegian': 'HOLD',
                'reasoning': 'Selskapet har både styrker og svakheter som investor bør vurdere',
                'confidence': 60
            }
        else:
            recommendation = {
                'action': 'AVOID',
                'norwegian': 'UNNGÅ',
                'reasoning': 'Selskapet oppfyller ikke tilstrekkelig mange av Buffetts kriterier',
                'confidence': 50
            }
        
        # Define company info
        company_types = {
            'TECH': {
                'sector': 'Teknologi',
                'industry': 'Programvare og Tjenester'
            },
            'ENERGY': {
                'sector': 'Energi',
                'industry': 'Olje og Gass'
            },
            'FINANCE': {
                'sector': 'Finans',
                'industry': 'Bank og Forsikring'
            },
            'CONSUMER': {
                'sector': 'Forbruksvarer',
                'industry': 'Detaljhandel'
            }
        }
        
        company_info = company_types.get(company_type, {
            'sector': 'Annet',
            'industry': 'Diversifisert'
        })
            
        # Return comprehensive analysis
        return {
            'ticker': symbol,
            'company_name': f"{symbol} {'ASA' if symbol.endswith('.OL') else 'Corporation'}",
            'sector': company_info['sector'],
            'industry': company_info['industry'],
            'buffett_score': round(buffett_score, 1),
            'scores': {k: round(v, 1) for k, v in scores.items()},
            'metrics': {k: round(v, 2) for k, v in metrics.items()},
            'strengths': strengths,
            'weaknesses': weaknesses,
            'insights': insights,
            'recommendation': recommendation,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'metrics_description': {
                'pe_ratio': 'Pris/Fortjeneste forhold',
                'price_to_book': 'Pris/Bok forhold',
                'debt_to_equity': 'Gjeld/Egenkapital forhold',
                'current_ratio': 'Likviditetsgrad',
                'roe': 'Egenkapitalavkastning (%)',
                'roa': 'Totalkapitalavkastning (%)',
                'profit_margin': 'Profittmargin (%)',
                'operating_margin': 'Driftsmargin (%)',
                'revenue_growth': 'Inntektsvekst (%)',
                'earnings_growth': 'Resultatvekst (%)',
                'free_cash_flow': 'Fri kontantstrøm (%)',
                'dividend_yield': 'Direkteavkastning (%)',
                'payout_ratio': 'Utbytteandel (%)',
                'interest_coverage': 'Rentedekningsgrad'
            }
        }
