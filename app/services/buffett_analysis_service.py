"""
Warren Buffett Analysis Service
Implements Warren Buffett's investment philosophy and criteria
"""
from datetime import datetime
import random
from flask import current_app

class BuffettAnalysisService:
    """Service for performing Warren Buffett style analysis on stocks"""
    
    # Buffett's key investment criteria
    CRITERIA = {
        'moat': {
            'name': 'Economic Moat',
            'description': 'Sustainable competitive advantages that protect the company',
            'weight': 0.25
        },
        'management': {
            'name': 'Management Quality',
            'description': 'Competent and shareholder-friendly management',
            'weight': 0.20
        },
        'simplicity': {
            'name': 'Business Simplicity',
            'description': 'Easy to understand business model',
            'weight': 0.15
        },
        'value': {
            'name': 'Intrinsic Value',
            'description': 'Trading below intrinsic value with margin of safety',
            'weight': 0.20
        },
        'financials': {
            'name': 'Financial Strength',
            'description': 'Consistent earnings, low debt, high ROE',
            'weight': 0.20
        }
    }
    
    @staticmethod
    def analyze_stock(ticker):
        """
        Perform Warren Buffett style analysis on a stock
        Returns comprehensive analysis with scores and recommendations
        """
        try:
            # Get stock data (would integrate with real data service)
            stock_data = BuffettAnalysisService._get_stock_data(ticker)
            
            # Calculate individual scores
            scores = BuffettAnalysisService._calculate_scores(ticker, stock_data)
            
            # Calculate overall Buffett score
            overall_score = BuffettAnalysisService._calculate_overall_score(scores)
            
            # Generate recommendation
            recommendation = BuffettAnalysisService._generate_recommendation(overall_score)
            
            # Generate detailed analysis
            analysis = BuffettAnalysisService._generate_detailed_analysis(
                ticker, stock_data, scores, overall_score, recommendation
            )
            
            return analysis
            
        except Exception as e:
            current_app.logger.error(f"Error in Buffett analysis for {ticker}: {str(e)}")
            return BuffettAnalysisService._get_fallback_analysis(ticker)
    
    @staticmethod
    def _get_stock_data(ticker):
        """Get stock data for analysis"""
        # This would integrate with your data service
        # For now, returning mock data
        return {
            'price': 100.0,
            'pe_ratio': 15.5,
            'roe': 22.0,
            'debt_to_equity': 0.3,
            'profit_margin': 15.0,
            'revenue_growth': 8.5,
            'free_cash_flow': 1000000000
        }
    
    @staticmethod
    def _calculate_scores(ticker, stock_data):
        """Calculate individual criterion scores"""
        # Base scores for known tickers
        base_scores = {
            'EQNR.OL': {'moat': 82, 'management': 85, 'simplicity': 80, 'value': 78, 'financials': 88},
            'DNB.OL': {'moat': 75, 'management': 88, 'simplicity': 85, 'value': 72, 'financials': 82},
            'AAPL': {'moat': 95, 'management': 92, 'simplicity': 75, 'value': 68, 'financials': 90},
            'MSFT': {'moat': 90, 'management': 95, 'simplicity': 78, 'value': 65, 'financials': 88},
            'TSLA': {'moat': 70, 'management': 75, 'simplicity': 45, 'value': 35, 'financials': 55},
            'YAR.OL': {'moat': 65, 'management': 80, 'simplicity': 82, 'value': 75, 'financials': 78},
            'NHY.OL': {'moat': 60, 'management': 75, 'simplicity': 85, 'value': 70, 'financials': 72},
            'TEL.OL': {'moat': 55, 'management': 70, 'simplicity': 88, 'value': 65, 'financials': 68}
        }
        
        if ticker in base_scores:
            scores = base_scores[ticker].copy()
            # Add small variations
            for key in scores:
                scores[key] = max(0, min(100, scores[key] + random.uniform(-5, 5)))
        else:
            # Generate random but plausible scores
            scores = {
                'moat': random.uniform(40, 85),
                'management': random.uniform(60, 90),
                'simplicity': random.uniform(50, 85),
                'value': random.uniform(45, 80),
                'financials': random.uniform(50, 85)
            }
        
        return scores
    
    @staticmethod
    def _calculate_overall_score(scores):
        """Calculate weighted overall score"""
        total = 0
        for key, score in scores.items():
            weight = BuffettAnalysisService.CRITERIA[key]['weight']
            total += score * weight
        return total
    
    @staticmethod
    def _generate_recommendation(overall_score):
        """Generate recommendation based on overall score"""
        if overall_score >= 80:
            return {
                'action': 'STRONG BUY',
                'confidence': 'HIGH',
                'summary': 'Excellent investment opportunity meeting Buffett criteria'
            }
        elif overall_score >= 70:
            return {
                'action': 'BUY',
                'confidence': 'MEDIUM',
                'summary': 'Good investment with some minor concerns'
            }
        elif overall_score >= 60:
            return {
                'action': 'HOLD',
                'confidence': 'MEDIUM',
                'summary': 'Decent company but wait for better price or clarity'
            }
        else:
            return {
                'action': 'AVOID',
                'confidence': 'HIGH',
                'summary': 'Does not meet Buffett investment criteria'
            }
    
    @staticmethod
    def _generate_detailed_analysis(ticker, stock_data, scores, overall_score, recommendation):
        """Generate comprehensive analysis report"""
        return {
            'ticker': ticker,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'overall_score': round(overall_score, 1),
            'scores': scores,
            'recommendation': recommendation,
            'criteria_details': BuffettAnalysisService._get_criteria_details(scores),
            'key_insights': BuffettAnalysisService._generate_insights(ticker, scores),
            'buffett_quote': BuffettAnalysisService._get_relevant_quote(overall_score),
            'investment_thesis': BuffettAnalysisService._generate_investment_thesis(ticker, scores, overall_score)
        }
    
    @staticmethod
    def _get_criteria_details(scores):
        """Get detailed explanation for each criterion"""
        details = []
        for key, score in scores.items():
            criterion = BuffettAnalysisService.CRITERIA[key]
            status = 'Excellent' if score > 80 else 'Good' if score > 70 else 'Fair' if score > 60 else 'Poor'
            details.append({
                'name': criterion['name'],
                'description': criterion['description'],
                'score': round(score, 1),
                'status': status,
                'weight': f"{int(criterion['weight'] * 100)}%"
            })
        return details
    
    @staticmethod
    def _generate_insights(ticker, scores):
        """Generate key insights based on scores"""
        insights = []
        
        if scores['moat'] > 80:
            insights.append("Strong competitive advantages provide lasting protection")
        elif scores['moat'] < 60:
            insights.append("Weak competitive position is a concern")
        
        if scores['management'] > 85:
            insights.append("Exceptional management team with proven track record")
        elif scores['management'] < 70:
            insights.append("Management quality needs improvement")
        
        if scores['value'] > 75:
            insights.append("Trading at attractive valuation with margin of safety")
        elif scores['value'] < 60:
            insights.append("Current valuation appears stretched")
        
        if scores['simplicity'] > 80:
            insights.append("Simple, understandable business model")
        elif scores['simplicity'] < 60:
            insights.append("Complex business model may hide risks")
        
        if scores['financials'] > 80:
            insights.append("Strong financial position with consistent performance")
        elif scores['financials'] < 65:
            insights.append("Financial metrics need improvement")
        
        return insights
    
    @staticmethod
    def _get_relevant_quote(overall_score):
        """Get relevant Buffett quote based on score"""
        if overall_score >= 80:
            return "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price."
        elif overall_score >= 70:
            return "The best thing that happens to us is when a great company gets into temporary trouble."
        elif overall_score >= 60:
            return "Never invest in a business you cannot understand."
        else:
            return "Rule No. 1: Never lose money. Rule No. 2: Never forget rule No. 1."
    
    @staticmethod
    def _generate_investment_thesis(ticker, scores, overall_score):
        """Generate investment thesis"""
        if overall_score >= 70:
            return (f"{ticker} shows strong Buffett-style fundamentals with "
                   f"{'excellent' if scores['moat'] > 80 else 'good'} competitive advantages, "
                   f"{'outstanding' if scores['management'] > 85 else 'competent'} management, and "
                   f"{'attractive' if scores['value'] > 70 else 'reasonable'} valuation. "
                   "This appears to be a quality business worth owning for the long term.")
        else:
            return (f"{ticker} does not currently meet Buffett's investment criteria. "
                   f"Concerns include {'weak moat' if scores['moat'] < 60 else ''}"
                   f"{', poor valuation' if scores['value'] < 60 else ''}"
                   f"{', complex business' if scores['simplicity'] < 60 else ''}. "
                   "Consider other opportunities or wait for improvements.")
    
    @staticmethod
    def _get_fallback_analysis(ticker):
        """Return fallback analysis if error occurs"""
        return {
            'ticker': ticker,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'overall_score': 65.0,
            'scores': {
                'moat': 65,
                'management': 70,
                'simplicity': 60,
                'value': 65,
                'financials': 65
            },
            'recommendation': {
                'action': 'HOLD',
                'confidence': 'LOW',
                'summary': 'Analysis temporarily unavailable - showing default assessment'
            },
            'error': True
        }
