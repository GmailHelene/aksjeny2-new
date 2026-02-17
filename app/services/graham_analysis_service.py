"""
Enhanced Benjamin Graham Analysis Service
Implements Benjamin Graham's value investing principles with modern enhancements
"""
from datetime import datetime
import random
import math
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class GrahamAnalysisService:
    """Enhanced service for performing Benjamin Graham style analysis on stocks"""
    
    # Enhanced Graham's key investment criteria with modern metrics
    CRITERIA = {
        'pe_ratio': {
            'name': 'P/E Ratio',
            'description': 'Should be less than 15 for defensive stocks',
            'threshold': 15,
            'type': 'maximum',
            'weight': 0.15,
            'category': 'Valuation'
        },
        'pb_ratio': {
            'name': 'P/B Ratio', 
            'description': 'Price-to-Book should indicate undervaluation',
            'threshold': 1.5,
            'type': 'maximum',
            'weight': 0.12,
            'category': 'Valuation'
        },
        'graham_number': {
            'name': 'Graham Number',
            'description': 'P/E × P/B should be less than 22.5',
            'threshold': 22.5,
            'type': 'combined',
            'weight': 0.18,
            'category': 'Valuation'
        },
        'current_ratio': {
            'name': 'Current Ratio',
            'description': 'Current assets should be at least 2x current liabilities',
            'threshold': 2.0,
            'type': 'minimum',
            'weight': 0.10,
            'category': 'Financial Strength'
        },
        'earnings_growth': {
            'name': 'Earnings Growth',
            'description': 'Positive earnings growth over past 5 years',
            'threshold': 0,
            'type': 'minimum',
            'weight': 0.12,
            'category': 'Growth'
        },
        'dividend_history': {
            'name': 'Dividend History',
            'description': 'Consistent dividend payments',
            'threshold': 5,
            'type': 'years',
            'weight': 0.08,
            'category': 'Stability'
        },
        'debt_ratio': {
            'name': 'Debt to Equity',
            'description': 'Conservative debt levels',
            'threshold': 0.5,
            'type': 'maximum',
            'weight': 0.10,
            'category': 'Financial Strength'
        },
        'roe': {
            'name': 'Return on Equity',
            'description': 'Should be above 10% consistently',
            'threshold': 10.0,
            'type': 'minimum',
            'weight': 0.10,
            'category': 'Profitability'
        },
        'margin_of_safety': {
            'name': 'Margin of Safety',
            'description': 'Price should be below intrinsic value',
            'threshold': 20.0,
            'type': 'margin',
            'weight': 0.15,
            'category': 'Valuation'
        }
    }
    
    @staticmethod
    def analyze_stock(ticker):
        """
        Perform enhanced Benjamin Graham style analysis on a stock
        Returns comprehensive value analysis with modern enhancements
        """
        try:
            logger.info(f"Starting Graham analysis for {ticker}")
            
            # Get enhanced stock data
            stock_data = GrahamAnalysisService._get_enhanced_stock_data(ticker)
            
            # Evaluate Graham criteria with detailed scoring
            criteria_results = GrahamAnalysisService._evaluate_enhanced_criteria(ticker, stock_data)
            
            # Calculate comprehensive Graham score
            graham_score = GrahamAnalysisService._calculate_enhanced_graham_score(criteria_results)
            
            # Calculate multiple intrinsic value methods
            valuation_methods = GrahamAnalysisService._calculate_multiple_valuations(stock_data)
            
            # Generate enhanced recommendation with risk assessment
            recommendation = GrahamAnalysisService._generate_enhanced_recommendation(
                graham_score, stock_data, valuation_methods, criteria_results
            )
            
            # Generate comprehensive analysis report
            analysis = GrahamAnalysisService._generate_comprehensive_analysis(
                ticker, stock_data, criteria_results, graham_score, 
                valuation_methods, recommendation
            )
            
            logger.info(f"Graham analysis completed for {ticker} with score: {graham_score}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in Graham analysis for {ticker}: {str(e)}")
            return GrahamAnalysisService._get_enhanced_fallback_analysis(ticker)
    
    @staticmethod
    def _get_enhanced_stock_data(ticker):
        """Get enhanced stock data for comprehensive analysis"""
        # Enhanced mock data with more realistic Norwegian and international stocks
        enhanced_data = {
            'EQNR.OL': {
                'price': 342.55, 'pe': 8.5, 'pb': 1.8, 'current_ratio': 1.9, 
                'debt_equity': 0.4, 'roe': 12.5, 'roa': 8.2, 'eps': 40.3,
                'book_value': 190.3, 'revenue_growth': 15.2, 'earnings_growth': 8.5,
                'dividend_yield': 2.1, 'payout_ratio': 35.0, 'beta': 1.2,
                'sector': 'Energy', 'market_cap': 1089000, 'debt_to_assets': 0.25,
                'interest_coverage': 12.5, 'working_capital': 45000,
                'free_cash_flow': 125000, 'revenue': 890000
            },
            'DNB.OL': {
                'price': 212.80, 'pe': 11.2, 'pb': 1.2, 'current_ratio': 2.8, 
                'debt_equity': 0.2, 'roe': 11.8, 'roa': 1.2, 'eps': 19.0,
                'book_value': 177.3, 'revenue_growth': 8.5, 'earnings_growth': 6.2,
                'dividend_yield': 4.2, 'payout_ratio': 45.0, 'beta': 1.1,
                'sector': 'Financial Services', 'market_cap': 330000, 'debt_to_assets': 0.15,
                'interest_coverage': 8.5, 'working_capital': 25000,
                'free_cash_flow': 35000, 'revenue': 145000
            },
            'AAPL': {
                'price': 185.24, 'pe': 28.5, 'pb': 42.1, 'current_ratio': 0.9, 
                'debt_equity': 1.8, 'roe': 150.0, 'roa': 22.5, 'eps': 6.5,
                'book_value': 4.4, 'revenue_growth': 11.0, 'earnings_growth': 7.8,
                'dividend_yield': 0.5, 'payout_ratio': 15.0, 'beta': 1.3,
                'sector': 'Technology', 'market_cap': 2900000, 'debt_to_assets': 0.3,
                'interest_coverage': 28.0, 'working_capital': -2000,
                'free_cash_flow': 92000, 'revenue': 383000
            },
            'MSFT': {
                'price': 338.21, 'pe': 32.8, 'pb': 8.2, 'current_ratio': 1.8, 
                'debt_equity': 0.4, 'roe': 38.5, 'roa': 15.2, 'eps': 10.3,
                'book_value': 41.2, 'revenue_growth': 12.1, 'earnings_growth': 10.5,
                'dividend_yield': 0.8, 'payout_ratio': 25.0, 'beta': 0.9,
                'sector': 'Technology', 'market_cap': 2500000, 'debt_to_assets': 0.2,
                'interest_coverage': 45.0, 'working_capital': 15000,
                'free_cash_flow': 65000, 'revenue': 211000
            }
        }
        
        # Generate semi-realistic data for other tickers
        if ticker not in enhanced_data:
            hash_seed = hash(ticker) % 1000
            random.seed(hash_seed)
            
            enhanced_data[ticker] = {
                'price': random.uniform(50, 500),
                'pe': random.uniform(8, 35),
                'pb': random.uniform(0.8, 8.0),
                'current_ratio': random.uniform(0.8, 4.0),
                'debt_equity': random.uniform(0.1, 2.0),
                'roe': random.uniform(5, 25),
                'roa': random.uniform(2, 15),
                'eps': random.uniform(2, 25),
                'book_value': random.uniform(20, 200),
                'revenue_growth': random.uniform(-5, 20),
                'earnings_growth': random.uniform(-10, 15),
                'dividend_yield': random.uniform(0, 6),
                'payout_ratio': random.uniform(10, 80),
                'beta': random.uniform(0.5, 2.0),
                'sector': random.choice(['Technology', 'Financial Services', 'Healthcare', 'Energy', 'Consumer', 'Industrial']),
                'market_cap': random.uniform(1000, 500000),
                'debt_to_assets': random.uniform(0.1, 0.6),
                'interest_coverage': random.uniform(2, 50),
                'working_capital': random.uniform(-5000, 50000),
                'free_cash_flow': random.uniform(1000, 100000),
                'revenue': random.uniform(10000, 1000000)
            }
        
        return enhanced_data[ticker]
    
    @staticmethod
    def _evaluate_enhanced_criteria(ticker, stock_data):
        """Enhanced evaluation of Graham criteria with detailed scoring"""
        results = {}
        
        for criterion_key, criterion in GrahamAnalysisService.CRITERIA.items():
            try:
                if criterion_key == 'pe_ratio':
                    value = stock_data['pe']
                    passed = value <= criterion['threshold']
                    score = max(0, (criterion['threshold'] - value) / criterion['threshold'] * 100) if value > 0 else 0
                    
                elif criterion_key == 'pb_ratio':
                    value = stock_data['pb']
                    passed = value <= criterion['threshold']
                    score = max(0, (criterion['threshold'] - value) / criterion['threshold'] * 100) if value > 0 else 0
                    
                elif criterion_key == 'graham_number':
                    pe_pb_product = stock_data['pe'] * stock_data['pb']
                    value = pe_pb_product
                    passed = pe_pb_product <= criterion['threshold']
                    score = max(0, (criterion['threshold'] - pe_pb_product) / criterion['threshold'] * 100) if pe_pb_product > 0 else 0
                    
                elif criterion_key == 'current_ratio':
                    value = stock_data['current_ratio']
                    passed = value >= criterion['threshold']
                    score = min(100, (value / criterion['threshold']) * 100) if value > 0 else 0
                    
                elif criterion_key == 'earnings_growth':
                    value = stock_data['earnings_growth']
                    passed = value > criterion['threshold']
                    score = min(100, max(0, value * 5)) if value >= 0 else 0
                    
                elif criterion_key == 'dividend_history':
                    # Simulate dividend history based on dividend yield and sector
                    dividend_yield = stock_data['dividend_yield']
                    years = 5 if dividend_yield > 2 else 3 if dividend_yield > 0 else 0
                    value = years
                    passed = years >= criterion['threshold']
                    score = min(100, (years / criterion['threshold']) * 100)
                    
                elif criterion_key == 'debt_ratio':
                    value = stock_data['debt_equity']
                    passed = value <= criterion['threshold']
                    score = max(0, (criterion['threshold'] - value) / criterion['threshold'] * 100) if value >= 0 else 100
                    
                elif criterion_key == 'roe':
                    value = stock_data['roe']
                    passed = value >= criterion['threshold']
                    score = min(100, (value / criterion['threshold']) * 100) if value > 0 else 0
                    
                elif criterion_key == 'margin_of_safety':
                    # Calculate margin of safety based on intrinsic value estimate
                    estimated_fair_value = stock_data['book_value'] * 1.5  # Simple estimate
                    margin = ((estimated_fair_value - stock_data['price']) / estimated_fair_value) * 100
                    value = max(0, margin)
                    passed = margin >= criterion['threshold']
                    score = min(100, max(0, margin))
                
                else:
                    value = 0
                    passed = False
                    score = 0
                
                results[criterion_key] = {
                    'criterion': criterion,
                    'value': round(value, 2),
                    'passed': passed,
                    'score': round(score, 1),
                    'weight': criterion['weight'],
                    'weighted_score': round(score * criterion['weight'], 2)
                }
                
            except Exception as e:
                logger.warning(f"Error evaluating {criterion_key} for {ticker}: {e}")
                results[criterion_key] = {
                    'criterion': criterion,
                    'value': 0,
                    'passed': False,
                    'score': 0,
                    'weight': criterion['weight'],
                    'weighted_score': 0
                }
        
        return results
    
    @staticmethod
    def _calculate_enhanced_graham_score(criteria_results):
        """Calculate weighted Graham score"""
        total_weighted_score = sum(result['weighted_score'] for result in criteria_results.values())
        max_possible_score = sum(result['weight'] * 100 for result in criteria_results.values())
        
        if max_possible_score > 0:
            graham_score = (total_weighted_score / max_possible_score) * 100
        else:
            graham_score = 0
            
        return round(graham_score, 1)
    
    @staticmethod
    def _calculate_multiple_valuations(stock_data):
        """Calculate intrinsic value using multiple methods"""
        try:
            methods = {}
            
            # 1. Graham's conservative formula
            eps = stock_data['eps']
            pe = stock_data['pe']
            growth_rate = max(0, min(stock_data['earnings_growth'], 20))  # Cap at 20%
            
            # Graham Formula: V = EPS × (8.5 + 2g) where g is growth rate
            graham_value = eps * (8.5 + 2 * growth_rate)
            methods['graham_formula'] = round(graham_value, 2)
            
            # 2. Book Value Method
            book_value = stock_data['book_value']
            pb_ratio = stock_data['pb']
            # Conservative book value estimate
            book_value_estimate = book_value * 1.1  # 10% buffer
            methods['book_value'] = round(book_value_estimate, 2)
            
            # 3. Earnings Power Value (EPV)
            # EPV = Normalized Earnings / Cost of Capital (assume 10%)
            normalized_earnings = stock_data['eps']
            epv = normalized_earnings / 0.10
            methods['earnings_power'] = round(epv, 2)
            
            # 4. Asset Value Method
            # Conservative asset valuation
            asset_value = book_value * 0.8  # 20% discount to book value
            methods['asset_value'] = round(asset_value, 2)
            
            # 5. Dividend Discount Model (simplified)
            dividend_per_share = stock_data['price'] * (stock_data['dividend_yield'] / 100)
            if dividend_per_share > 0:
                # Assume 3% growth, 8% required return
                ddm_value = dividend_per_share * 1.03 / (0.08 - 0.03)
                methods['dividend_discount'] = round(ddm_value, 2)
            else:
                methods['dividend_discount'] = 0
                
            # Average valuation (excluding outliers)
            valid_values = [v for v in methods.values() if v > 0 and v < stock_data['price'] * 3]
            if valid_values:
                average_value = sum(valid_values) / len(valid_values)
                methods['average_intrinsic'] = round(average_value, 2)
            else:
                methods['average_intrinsic'] = round(graham_value, 2)
            
            return methods
            
        except Exception as e:
            logger.error(f"Error calculating valuations: {e}")
    
    @staticmethod
    def _generate_enhanced_recommendation(graham_score, stock_data, valuation_methods, criteria_results):
        """Generate enhanced recommendation with risk assessment"""
        try:
            current_price = stock_data['price']
            average_intrinsic = valuation_methods['average_intrinsic']
            
            # Calculate margin of safety
            margin_of_safety = ((average_intrinsic - current_price) / average_intrinsic) * 100 if average_intrinsic > 0 else -50
            
            # Risk factors
            risk_factors = []
            if stock_data['debt_equity'] > 1.0:
                risk_factors.append("High debt levels")
            if stock_data['current_ratio'] < 1.5:
                risk_factors.append("Weak liquidity position")
            if stock_data['earnings_growth'] < 0:
                risk_factors.append("Declining earnings")
            if stock_data['pe'] > 25:
                risk_factors.append("High valuation multiple")
            if stock_data['beta'] > 1.5:
                risk_factors.append("High volatility")
            
            # Positive factors
            positive_factors = []
            if stock_data['roe'] > 15:
                positive_factors.append("Strong return on equity")
            if stock_data['current_ratio'] > 2.0:
                positive_factors.append("Strong liquidity")
            if stock_data['dividend_yield'] > 2:
                positive_factors.append("Attractive dividend yield")
            if stock_data['pe'] < 15:
                positive_factors.append("Reasonable valuation")
            if stock_data['debt_equity'] < 0.3:
                positive_factors.append("Conservative debt levels")
            
            # Generate recommendation
            if graham_score >= 80 and margin_of_safety >= 20:
                recommendation = "STRONG BUY"
                confidence = "High"
                reasoning = "Excellent Graham score with significant margin of safety"
            elif graham_score >= 70 and margin_of_safety >= 10:
                recommendation = "BUY"
                confidence = "Medium-High"
                reasoning = "Good value characteristics with adequate safety margin"
            elif graham_score >= 60 and margin_of_safety >= 0:
                recommendation = "HOLD"
                confidence = "Medium"
                reasoning = "Decent fundamentals but limited upside"
            elif graham_score >= 50:
                recommendation = "WEAK HOLD"
                confidence = "Low-Medium"
                reasoning = "Mixed signals, proceed with caution"
            else:
                recommendation = "AVOID"
                confidence = "Low"
                reasoning = "Poor Graham characteristics, high risk"
            
            return {
                'action': recommendation,
                'confidence': confidence,
                'reasoning': reasoning,
                'margin_of_safety': round(margin_of_safety, 1),
                'risk_factors': risk_factors,
                'positive_factors': positive_factors,
                'target_price': round(average_intrinsic, 2),
                'upside_potential': round(margin_of_safety, 1) if margin_of_safety > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {
                'action': "HOLD",
                'confidence': "Low",
                'reasoning': "Analysis incomplete",
                'margin_of_safety': 0,
                'risk_factors': ["Insufficient data"],
                'positive_factors': [],
                'target_price': stock_data['price'],
                'upside_potential': 0
            }
    
    @staticmethod
    def _generate_comprehensive_analysis(ticker, stock_data, criteria_results, graham_score, valuation_methods, recommendation):
        """Generate comprehensive analysis report"""
        try:
            # Get company name
            company_names = {
                'EQNR.OL': 'Equinor ASA',
                'DNB.OL': 'DNB Bank ASA',
                'AAPL': 'Apple Inc.',
                'MSFT': 'Microsoft Corporation'
            }
            
            company_name = company_names.get(ticker, f"Company {ticker}")
            
            # Create analysis timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate key metrics
            pe_pb_product = stock_data['pe'] * stock_data['pb']
            debt_to_total_capital = stock_data['debt_equity'] / (1 + stock_data['debt_equity'])
            
            analysis = {
                'timestamp': timestamp,
                'ticker': ticker,
                'company_name': company_name,
                'current_price': stock_data['price'],
                'sector': stock_data['sector'],
                'market_cap': stock_data['market_cap'],
                
                # Graham scoring
                'graham_score': graham_score,
                'criteria_results': criteria_results,
                
                # Valuation methods
                'valuation_methods': valuation_methods,
                'intrinsic_value': valuation_methods['average_intrinsic'],
                
                # Key metrics
                'key_metrics': {
                    'pe_ratio': stock_data['pe'],
                    'pb_ratio': stock_data['pb'],
                    'pe_pb_product': round(pe_pb_product, 2),
                    'current_ratio': stock_data['current_ratio'],
                    'debt_equity': stock_data['debt_equity'],
                    'debt_to_total_capital': round(debt_to_total_capital * 100, 1),
                    'roe': stock_data['roe'],
                    'roa': stock_data['roa'],
                    'dividend_yield': stock_data['dividend_yield'],
                    'earnings_growth': stock_data['earnings_growth'],
                    'revenue_growth': stock_data['revenue_growth'],
                    'beta': stock_data['beta']
                },
                
                # Financial strength indicators
                'financial_strength': {
                    'interest_coverage': stock_data['interest_coverage'],
                    'working_capital': stock_data['working_capital'],
                    'free_cash_flow': stock_data['free_cash_flow'],
                    'debt_to_assets': stock_data['debt_to_assets']
                },
                
                # Recommendation
                'recommendation': recommendation,
                
                # Summary insights
                'summary': {
                    'strengths': _get_strengths(stock_data, criteria_results),
                    'weaknesses': _get_weaknesses(stock_data, criteria_results),
                    'graham_grade': _get_graham_grade(graham_score),
                    'investment_type': _classify_investment_type(stock_data, criteria_results)
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {e}")
            return GrahamAnalysisService._get_enhanced_fallback_analysis(ticker)
    
    @staticmethod
    def _get_enhanced_fallback_analysis(ticker):
        """Enhanced fallback analysis when main analysis fails"""
        # Create mock criteria_results to prevent AttributeError
        mock_criteria_results = {
            'pe_ratio': {'met': False, 'weight': 15, 'weighted_score': 0},
            'pb_ratio': {'met': False, 'weight': 10, 'weighted_score': 0},
            'current_ratio': {'met': True, 'weight': 10, 'weighted_score': 10},
            'debt_equity': {'met': True, 'weight': 15, 'weighted_score': 15},
            'earnings_growth': {'met': False, 'weight': 20, 'weighted_score': 0}
        }
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ticker': ticker,
            'company_name': f"Company {ticker}",
            'current_price': 100.0,
            'sector': 'Unknown',
            'market_cap': 10000,
            'graham_score': 50.0,
            'criteria_results': mock_criteria_results,
            'valuation_methods': {
                'graham_formula': 95.0,
                'average_intrinsic': 95.0
            },
            'intrinsic_value': 95.0,
            'key_metrics': {},
            'financial_strength': {},
            'recommendation': {
                'action': 'HOLD',
                'confidence': 'Low',
                'reasoning': 'Insufficient data for analysis',
                'margin_of_safety': 0,
                'risk_factors': ['Data unavailable'],
                'positive_factors': [],
                'target_price': 100.0,
                'upside_potential': 0
            },
            'summary': {
                'strengths': ['Analysis pending'],
                'weaknesses': ['Insufficient data'],
                'graham_grade': 'C',
                'investment_type': 'Unknown'
            },
            'error': 'Analysis data unavailable'
        }

def _get_strengths(stock_data, criteria_results):
    """Identify investment strengths"""
    strengths = []
    
    if stock_data['pe'] < 15:
        strengths.append("Attractive P/E ratio under 15")
    if stock_data['current_ratio'] > 2:
        strengths.append("Strong liquidity position")
    if stock_data['roe'] > 15:
        strengths.append("Excellent return on equity")
    if stock_data['debt_equity'] < 0.5:
        strengths.append("Conservative debt levels")
    if stock_data['dividend_yield'] > 2:
        strengths.append("Attractive dividend yield")
    if stock_data['earnings_growth'] > 5:
        strengths.append("Solid earnings growth")
    
    return strengths if strengths else ["Conservative investment approach"]

def _get_weaknesses(stock_data, criteria_results):
    """Identify investment weaknesses"""
    weaknesses = []
    
    if stock_data['pe'] > 25:
        weaknesses.append("High P/E ratio indicates expensive valuation")
    if stock_data['current_ratio'] < 1.5:
        weaknesses.append("Weak liquidity position")
    if stock_data['debt_equity'] > 1:
        weaknesses.append("High debt levels")
    if stock_data['roe'] < 10:
        weaknesses.append("Below-average return on equity")
    if stock_data['earnings_growth'] < 0:
        weaknesses.append("Declining earnings trend")
    if stock_data['pb'] > 3:
        weaknesses.append("Trading well above book value")
    
    return weaknesses if weaknesses else ["Minor concerns only"]

def _get_graham_grade(graham_score):
    """Convert Graham score to letter grade"""
    if graham_score >= 85:
        return "A+"
    elif graham_score >= 80:
        return "A"
    elif graham_score >= 75:
        return "A-"
    elif graham_score >= 70:
        return "B+"
    elif graham_score >= 65:
        return "B"
    elif graham_score >= 60:
        return "B-"
    elif graham_score >= 55:
        return "C+"
    elif graham_score >= 50:
        return "C"
    elif graham_score >= 45:
        return "C-"
    elif graham_score >= 40:
        return "D"
    else:
        return "F"

def _classify_investment_type(stock_data, criteria_results):
    """Classify the type of investment based on characteristics"""
    if stock_data['dividend_yield'] > 3 and stock_data['pe'] < 15:
        return "Income Value Play"
    elif stock_data['pe'] < 12 and stock_data['pb'] < 1.5:
        return "Deep Value"
    elif stock_data['earnings_growth'] > 10 and stock_data['pe'] < 20:
        return "Growth at Reasonable Price (GARP)"
    elif stock_data['current_ratio'] > 2 and stock_data['debt_equity'] < 0.3:
        return "Defensive Value"
    elif stock_data['pe'] > 20:
        return "Growth Stock"
    else:
        return "Balanced Investment"
    
    def _get_fallback_data(self, ticker: str) -> Dict:
        """Generate fallback data for testing purposes"""
        import random
        
        # Base data for some well-known stocks
        base_data = {
            'EQNR.OL': {'price': 305.60, 'pe': 8.5, 'pb': 1.8, 'current_ratio': 2.1, 'debt_equity': 0.3},
            'DNB.OL': {'price': 198.20, 'pe': 12.2, 'pb': 1.2, 'current_ratio': 1.1, 'debt_equity': 4.5},
            'AAPL': {'price': 185.70, 'pe': 28.5, 'pb': 35.2, 'current_ratio': 1.1, 'debt_equity': 1.5},
            'MSFT': {'price': 390.20, 'pe': 32.1, 'pb': 13.8, 'current_ratio': 1.9, 'debt_equity': 0.7}
        }
        
        if ticker in base_data:
            data = base_data[ticker].copy()
        else:
            data = {
                'price': random.uniform(50, 500),
                'pe': random.uniform(10, 30),
                'pb': random.uniform(1, 5),
                'current_ratio': random.uniform(1.5, 3),
                'debt_equity': random.uniform(0.2, 1.5)
            }
        
        # Add additional fields
        data.update({
            'earnings_growth': random.uniform(-5, 15),
            'dividend_years': random.randint(0, 30),
            'book_value_growth': random.uniform(0, 10),
            'earnings_per_share': data['price'] / data['pe'] if data['pe'] > 0 else 0
        })
        
        return data
    
    @staticmethod
    def _evaluate_criteria(ticker, stock_data):
        """Evaluate stock against Graham criteria"""
        results = {}
        
        # P/E Ratio test
        results['pe_ratio'] = {
            'passed': stock_data['pe'] < 15,
            'value': stock_data['pe'],
            'threshold': 15,
            'score': min(100, (15 / stock_data['pe']) * 100) if stock_data['pe'] > 0 else 100
        }
        
        # P/E × P/B test
        pe_pb_product = stock_data['pe'] * stock_data['pb']
        results['pb_ratio'] = {
            'passed': pe_pb_product < 22.5,
            'value': pe_pb_product,
            'threshold': 22.5,
            'score': min(100, (22.5 / pe_pb_product) * 100) if pe_pb_product > 0 else 100
        }
        
        # Current Ratio test
        results['current_ratio'] = {
            'passed': stock_data['current_ratio'] >= 2.0,
            'value': stock_data['current_ratio'],
            'threshold': 2.0,
            'score': min(100, (stock_data['current_ratio'] / 2.0) * 100)
        }
        
        # Earnings Growth test
        results['earnings_growth'] = {
            'passed': stock_data['earnings_growth'] > 0,
            'value': stock_data['earnings_growth'],
            'threshold': 0,
            'score': min(100, max(0, stock_data['earnings_growth'] * 10))
        }
        
        # Dividend History test
        results['dividend_history'] = {
            'passed': stock_data['dividend_years'] >= 20,
            'value': stock_data['dividend_years'],
            'threshold': 20,
            'score': min(100, (stock_data['dividend_years'] / 20) * 100)
        }
        
        # Debt Ratio test
        results['debt_ratio'] = {
            'passed': stock_data['debt_equity'] < 1.0,
            'value': stock_data['debt_equity'],
            'threshold': 1.0,
            'score': min(100, (1.0 / max(0.1, stock_data['debt_equity'])) * 100)
        }
        
        # Book Value Growth test
        results['book_value_growth'] = {
            'passed': stock_data['book_value_growth'] >= 5.0,
            'value': stock_data['book_value_growth'],
            'threshold': 5.0,
            'score': min(100, (stock_data['book_value_growth'] / 5.0) * 100)
        }
        
        return results
    
    @staticmethod
    def _calculate_graham_score(criteria_results):
        """Calculate overall Graham score"""
        total_score = 0
        criteria_count = len(criteria_results)
        
        for result in criteria_results.values():
            total_score += result['score']
        
        return total_score / criteria_count
    
    @staticmethod
    def _calculate_intrinsic_value(stock_data):
        """Calculate intrinsic value using Graham formula"""
        # Graham Formula: V = EPS × (8.5 + 2g)
        # Where g is expected growth rate
        eps = stock_data.get('earnings_per_share', 10)
        growth_rate = min(stock_data.get('earnings_growth', 5), 15)  # Cap at 15%
        
        intrinsic_value = eps * (8.5 + 2 * growth_rate)
        
        # Apply margin of safety
        return intrinsic_value * 0.75
    
    @staticmethod
    def _generate_recommendation(graham_score, current_price, intrinsic_value):
        """Generate recommendation based on Graham analysis"""
        margin_of_safety = ((intrinsic_value - current_price) / current_price) * 100
        
        if graham_score >= 70 and margin_of_safety > 25:
            return {
                'action': 'STRONG BUY',
                'confidence': 'HIGH',
                'summary': 'Excellent value opportunity with significant margin of safety'
            }
        elif graham_score >= 60 and margin_of_safety > 10:
            return {
                'action': 'BUY',
                'confidence': 'MEDIUM',
                'summary': 'Good value investment with adequate margin of safety'
            }
        elif graham_score >= 50 or margin_of_safety > 0:
            return {
                'action': 'HOLD',
                'confidence': 'MEDIUM',
                'summary': 'Fair value - consider accumulating on dips'
            }
        else:
            return {
                'action': 'AVOID',
                'confidence': 'HIGH',
                'summary': 'Overvalued or fails to meet Graham criteria'
            }
    
    @staticmethod
    def _generate_detailed_analysis(ticker, stock_data, criteria_results, 
                                   graham_score, intrinsic_value, recommendation):
        """Generate comprehensive Graham analysis report"""
        margin_of_safety = ((intrinsic_value - stock_data['price']) / stock_data['price']) * 100
        
        # Get company name mapping
        company_names = {
            'EQNR.OL': 'Equinor ASA',
            'DNB.OL': 'DNB Bank ASA', 
            'TEL.OL': 'Telenor ASA',
            'YAR.OL': 'Yara International ASA',
            'NHY.OL': 'Norsk Hydro ASA',
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.'
        }
        
        return {
            'ticker': ticker,
            'company_name': company_names.get(ticker, f"Selskap {ticker}"),
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'current_price': stock_data['price'],
            'intrinsic_value': round(intrinsic_value, 2),
            'margin_of_safety': round(margin_of_safety, 1),
            'graham_score': round(graham_score, 1),
            'value_score': GrahamAnalysisService._get_value_score(graham_score),
            'criteria': GrahamAnalysisService._format_criteria_for_template(criteria_results, stock_data),
            'recommendation': recommendation['action'],
            'confidence': recommendation['confidence'],
            'summary': recommendation['summary'],
            'key_metrics': {
                'pe_ratio': stock_data['pe'],
                'pb_ratio': stock_data['pb'],
                'current_ratio': stock_data['current_ratio'],
                'debt_equity': stock_data['debt_equity'],
                'earnings_growth': f"{stock_data['earnings_growth']:.1f}%",
                'dividend_years': stock_data['dividend_years']
            },
            'investment_thesis': GrahamAnalysisService._generate_investment_thesis(
                ticker, graham_score, margin_of_safety, criteria_results
            ),
            'graham_principles': GrahamAnalysisService._get_applicable_principles(graham_score)
        }
    
    @staticmethod
    def _get_value_score(graham_score):
        """Get value score label based on Graham score"""
        if graham_score >= 80:
            return 'Excellent Value'
        elif graham_score >= 70:
            return 'Good Value'
        elif graham_score >= 60:
            return 'Fair Value'
        else:
            return 'Poor Value'
    
    @staticmethod
    def _format_criteria_for_template(criteria_results, stock_data):
        """Format criteria results for template display"""
        return {
            'pe_ratio': stock_data['pe'],
            'pb_ratio': stock_data['pb'], 
            'current_ratio': stock_data['current_ratio'],
            'debt_ratio': stock_data['debt_equity'],
            'eps_growth': stock_data['earnings_growth'],
            'dividend_years': stock_data['dividend_years'],
            'book_value_growth': stock_data['book_value_growth']
        }

    @staticmethod
    def _format_criteria_results(criteria_results):
        """Format criteria results for display"""
        formatted = []
        for key, result in criteria_results.items():
            criterion = GrahamAnalysisService.CRITERIA[key]
            formatted.append({
                'name': criterion['name'],
                'description': criterion['description'],
                'passed': result['passed'],
                'value': f"{result['value']:.2f}",
                'threshold': result['threshold'],
                'score': round(result['score'], 1)
            })
        return formatted
    
    @staticmethod
    def _generate_investment_thesis(ticker, graham_score, margin_of_safety, criteria_results):
        """Generate investment thesis based on Graham principles"""
        passed_criteria = sum(1 for r in criteria_results.values() if r['passed'])
        total_criteria = len(criteria_results)
        
        if graham_score >= 70 and margin_of_safety > 25:
            return (f"{ticker} is a classic Graham value play, passing {passed_criteria}/{total_criteria} criteria "
                   f"with a {margin_of_safety:.1f}% margin of safety. This represents a compelling opportunity "
                   "for patient value investors seeking capital preservation with upside potential.")
        elif graham_score >= 60:
            return (f"{ticker} shows reasonable value characteristics, passing {passed_criteria}/{total_criteria} criteria. "
                   f"With a {margin_of_safety:.1f}% margin of safety, it may be suitable for conservative investors "
                   "but should be monitored for better entry points.")
        else:
            return (f"{ticker} fails to meet Graham's strict value criteria, passing only {passed_criteria}/{total_criteria} tests. "
                   f"The {'negative' if margin_of_safety < 0 else 'insufficient'} margin of safety suggests "
                   "waiting for a significant price correction before considering investment.")
    
    @staticmethod
    def _get_applicable_principles(graham_score):
        """Get relevant Graham principles based on score"""
        if graham_score >= 70:
            return [
                "Buy when others are fearful",
                "Margin of safety is paramount",
                "Focus on intrinsic value, not market price",
                "Patience is the value investor's greatest virtue"
            ]
        else:
            return [
                "Never compromise on margin of safety",
                "Price is what you pay, value is what you get",
                "In the short run, the market is a voting machine",
                "The intelligent investor is a realist who sells to optimists"
            ]
    
    @staticmethod
    def _get_fallback_analysis(ticker):
        """Return fallback analysis if error occurs"""
        company_names = {
            'EQNR.OL': 'Equinor ASA',
            'DNB.OL': 'DNB Bank ASA', 
            'TEL.OL': 'Telenor ASA',
            'YAR.OL': 'Yara International ASA',
            'NHY.OL': 'Norsk Hydro ASA',
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.'
        }
        
        return {
            'ticker': ticker,
            'company_name': company_names.get(ticker, f"Selskap {ticker}"),
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'graham_score': 50.0,
            'value_score': 'Fair Value',
            'current_price': 100.0,
            'intrinsic_value': 100.0,
            'margin_of_safety': 0.0,
            'recommendation': 'HOLD',
            'confidence': 'LOW',
            'summary': 'Analyse midlertidig utilgjengelig - viser standard vurdering',
            'criteria': {
                'pe_ratio': 15.0,
                'pb_ratio': 1.5,
                'current_ratio': 2.0,
                'debt_ratio': 0.5,
                'eps_growth': 5.0,
                'dividend_years': 10,
                'book_value_growth': 5.0
            },
            'error': True
        }
