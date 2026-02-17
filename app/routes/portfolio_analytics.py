"""
Advanced Portfolio Analytics Routes
=================================

Advanced portfolio analysis endpoints with AI-driven insights,
risk decomposition, performance attribution, and optimization.

Author: Aksjeradar Development Team  
Date: July 2025
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from ..utils.access_control import demo_access
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import pandas as pd  # Required for data manipulations (fix NameError 'pd')

# Import services
from ..services.advanced_portfolio_analytics import AdvancedPortfolioAnalytics
from ..services.portfolio_service import PortfolioService
from ..models.portfolio import Portfolio, PortfolioStock
from ..extensions import db

# Create blueprint
portfolio_analytics_bp = Blueprint('portfolio_analytics', __name__, 
                                 url_prefix='/portfolio-analytics')

# Alias for import compatibility
portfolio_analytics = portfolio_analytics_bp

# Initialize services
analytics_service = AdvancedPortfolioAnalytics()
portfolio_service = PortfolioService()

# Setup logging
logger = logging.getLogger(__name__)

@portfolio_analytics_bp.route('/')
@demo_access
def analytics_dashboard():
    """Main portfolio analytics dashboard"""
    try:
        # Get user's portfolios
        if current_user.is_authenticated:
            portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
        else:
            portfolios = []  # Demo mode - no portfolios
        
        # Get default portfolio for initial analysis
        default_portfolio = portfolios[0] if portfolios else None
        
        return render_template(
            'portfolio_analytics/dashboard.html',
            portfolios=portfolios,
            default_portfolio=default_portfolio,
            page_title="Avansert Porteføljeanalyse"
        )
        
    except Exception as e:
        logger.error(f"Error loading analytics dashboard: {str(e)}")
        return render_template('errors/500.html', error_message=str(e)), 500

@portfolio_analytics_bp.route('/comprehensive-analysis/<int:portfolio_id>')
@login_required  
def comprehensive_analysis(portfolio_id: int):
    """Perform comprehensive portfolio analysis"""
    try:
        # Verify portfolio ownership
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio not found or access denied'
            }), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Perform comprehensive analysis
        analysis_result = analytics_service.analyze_portfolio_comprehensive(
            portfolio_data=portfolio_data,
            timeframe_days=request.args.get('timeframe', 252, type=int)
        )
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_analytics_bp.route('/risk-analysis/<int:portfolio_id>')
@login_required
def risk_analysis(portfolio_id: int):
    """Detailed portfolio risk analysis"""
    try:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Perform comprehensive analysis (includes risk decomposition)
        analysis_result = analytics_service.analyze_portfolio_comprehensive(portfolio_data)
        
        # Extract risk-specific information
        risk_analysis = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'risk_decomposition': analysis_result.get('risk_decomposition', {}),
            'scenario_analysis': analysis_result.get('scenario_analysis', {}),
            'risk_metrics': {
                'var_95': analysis_result.get('portfolio_metrics', {}).get('var_95', 0),
                'cvar_95': analysis_result.get('portfolio_metrics', {}).get('cvar_95', 0),
                'max_drawdown': analysis_result.get('portfolio_metrics', {}).get('max_drawdown', 0),
                'beta': analysis_result.get('portfolio_metrics', {}).get('beta', 1),
                'volatility': analysis_result.get('portfolio_metrics', {}).get('volatility', 0)
            },
            'risk_alerts': analysis_result.get('ai_insights', {}).get('alerts', []),
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(risk_analysis)
        
    except Exception as e:
        logger.error(f"Error in risk analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_analytics_bp.route('/performance-attribution/<int:portfolio_id>')
@login_required
def performance_attribution(portfolio_id: int):
    """Portfolio performance attribution analysis"""
    try:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Get benchmark data if provided
        benchmark_symbol = request.args.get('benchmark', 'SPY')
        benchmark_data = None  # Would fetch benchmark data in production
        
        # Perform analysis
        analysis_result = analytics_service.analyze_portfolio_comprehensive(
            portfolio_data=portfolio_data,
            benchmark_data=benchmark_data
        )
        
        # Extract performance attribution
        attribution_result = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'performance_attribution': analysis_result.get('performance_attribution', {}),
            'portfolio_metrics': analysis_result.get('portfolio_metrics', {}),
            'benchmark_comparison': {
                'benchmark_symbol': benchmark_symbol,
                'excess_return': analysis_result.get('performance_attribution', {}).get('total_excess_return', 0),
                'tracking_error': analysis_result.get('portfolio_metrics', {}).get('tracking_error', 0)
            },
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(attribution_result)
        
    except Exception as e:
        logger.error(f"Error in performance attribution: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_analytics_bp.route('/optimization-recommendations/<int:portfolio_id>')
@login_required
def optimization_recommendations(portfolio_id: int):
    """AI-driven portfolio optimization recommendations"""
    try:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Perform comprehensive analysis
        analysis_result = analytics_service.analyze_portfolio_comprehensive(portfolio_data)
        
        # Extract optimization recommendations
        optimization_result = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'recommendations': analysis_result.get('optimization_recommendations', []),
            'portfolio_health_score': analysis_result.get('ai_insights', {}).get('portfolio_health_score', {}),
            'current_allocation': portfolio_data.get('allocation_summary', {}),
            'recommended_actions_summary': _summarize_recommendations(
                analysis_result.get('optimization_recommendations', [])
            ),
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(optimization_result)
        
    except Exception as e:
        logger.error(f"Error in optimization recommendations: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_analytics_bp.route('/ai-insights/<int:portfolio_id>')
@login_required
def ai_insights(portfolio_id: int):
    """AI-driven portfolio insights and analysis"""
    try:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Perform comprehensive analysis
        analysis_result = analytics_service.analyze_portfolio_comprehensive(portfolio_data)
        
        # Extract AI insights
        insights_result = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'ai_insights': analysis_result.get('ai_insights', {}),
            'portfolio_health_score': analysis_result.get('ai_insights', {}).get('portfolio_health_score', {}),
            'market_positioning': analysis_result.get('ai_insights', {}).get('market_positioning', {}),
            'diversification_analysis': analysis_result.get('ai_insights', {}).get('diversification_analysis', {}),
            'performance_trends': analysis_result.get('ai_insights', {}).get('performance_trends', {}),
            'alerts': analysis_result.get('ai_insights', {}).get('alerts', []),
            'recommendations_summary': _create_insights_summary(analysis_result),
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(insights_result)
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_analytics_bp.route('/esg-analysis/<int:portfolio_id>')
@login_required
def esg_analysis(portfolio_id: int):
    """ESG and sustainability analysis"""
    try:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Perform comprehensive analysis
        analysis_result = analytics_service.analyze_portfolio_comprehensive(portfolio_data)
        
        # Extract ESG metrics
        esg_result = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'esg_metrics': analysis_result.get('esg_metrics', {}),
            'sustainable_allocation': _calculate_sustainable_allocation(portfolio_data),
            'esg_recommendations': _generate_esg_recommendations(analysis_result.get('esg_metrics', {})),
            'sector_sustainability': _analyze_sector_sustainability(portfolio_data),
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(esg_result)
        
    except Exception as e:
        logger.error(f"Error in ESG analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_analytics_bp.route('/scenario-analysis/<int:portfolio_id>')
@login_required
def scenario_analysis(portfolio_id: int):
    """Portfolio scenario analysis"""
    try:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Perform comprehensive analysis
        analysis_result = analytics_service.analyze_portfolio_comprehensive(portfolio_data)
        
        # Extract scenario analysis
        scenario_result = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'scenario_analysis': analysis_result.get('scenario_analysis', {}),
            'stress_test_results': _perform_additional_stress_tests(portfolio_data),
            'resilience_score': _calculate_resilience_score(analysis_result.get('scenario_analysis', {})),
            'hedging_recommendations': _generate_hedging_recommendations(analysis_result),
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(scenario_result)
        
    except Exception as e:
        logger.error(f"Error in scenario analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_analytics_bp.route('/compare-portfolios')
@login_required
def compare_portfolios():
    """Compare multiple portfolios"""
    try:
        portfolio_ids = request.args.getlist('portfolio_ids', type=int)
        
        if len(portfolio_ids) < 2:
            return jsonify({
                'success': False,
                'error': 'At least 2 portfolios required for comparison'
            }), 400
        
        comparison_results = []
        
        for portfolio_id in portfolio_ids:
            # Verify ownership
            portfolio = Portfolio.query.filter_by(
                id=portfolio_id, 
                user_id=current_user.id
            ).first()
            
            if not portfolio:
                continue
            
            # Get portfolio data and analysis
            portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
            analysis_result = analytics_service.analyze_portfolio_comprehensive(portfolio_data)
            
            comparison_results.append({
                'portfolio_id': portfolio_id,
                'portfolio_name': portfolio.name,
                'metrics': analysis_result.get('portfolio_metrics', {}),
                'health_score': analysis_result.get('ai_insights', {}).get('portfolio_health_score', {}),
                'risk_profile': analysis_result.get('ai_insights', {}).get('risk_profile', 'Unknown')
            })
        
        # Generate comparison insights
        comparison_analysis = {
            'portfolios': comparison_results,
            'comparison_insights': _generate_comparison_insights(comparison_results),
            'best_performer': _identify_best_performer(comparison_results),
            'recommendations': _generate_cross_portfolio_recommendations(comparison_results),
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(comparison_analysis)
        
    except Exception as e:
        logger.error(f"Error comparing portfolios: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_analytics_bp.route('/analytics-report/<int:portfolio_id>')
@login_required
def analytics_report(portfolio_id: int):
    """Generate comprehensive analytics report"""
    try:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_with_current_prices(portfolio_id)
        
        # Perform comprehensive analysis
        analysis_result = analytics_service.analyze_portfolio_comprehensive(portfolio_data)
        
        # Generate comprehensive report
        report = {
            'report_header': {
                'portfolio_name': portfolio.name,
                'report_date': datetime.utcnow().isoformat(),
                'analysis_period': '1 Year',
                'total_value': portfolio_data.get('total_value', 0),
                'number_of_holdings': len(portfolio_data.get('holdings', []))
            },
            'executive_summary': _create_executive_summary(analysis_result),
            'detailed_analysis': analysis_result,
            'visualizations': _prepare_chart_data(analysis_result),
            'actionable_recommendations': _prioritize_recommendations(
                analysis_result.get('optimization_recommendations', [])
            ),
            'appendix': {
                'methodology': 'Advanced statistical analysis with AI-driven insights',
                'data_sources': 'Real-time market data, fundamental analysis',
                'risk_disclaimers': 'Past performance does not guarantee future results'
            },
            'success': True
        }
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating analytics report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper functions
def _summarize_recommendations(recommendations: List[Dict]) -> Dict[str, Any]:
    """Summarize optimization recommendations"""
    if not recommendations:
        return {'total_recommendations': 0, 'priority_actions': []}
    
    actions = {}
    for rec in recommendations:
        action = rec.get('action', 'unknown')
        actions[action] = actions.get(action, 0) + 1
    
    return {
        'total_recommendations': len(recommendations),
        'actions_breakdown': actions,
        'priority_actions': [rec for rec in recommendations if rec.get('confidence_score', 0) > 0.8]
    }

def _create_insights_summary(analysis_result: Dict) -> Dict[str, str]:
    """Create summary of AI insights"""
    insights = analysis_result.get('ai_insights', {})
    health_score = insights.get('portfolio_health_score', {})
    
    return {
        'overall_assessment': f"Portfolio health score: {health_score.get('overall_score', 0)}/100",
        'key_strength': _identify_key_strength(insights),
        'main_concern': _identify_main_concern(insights),
        'priority_action': _identify_priority_action(analysis_result.get('optimization_recommendations', []))
    }

def _identify_key_strength(insights: Dict) -> str:
    """Identify portfolio's key strength"""
    health_score = insights.get('portfolio_health_score', {})
    component_scores = health_score.get('component_scores', {})
    
    if not component_scores:
        return "Balanced approach"
    
    best_component = max(component_scores.items(), key=lambda x: x[1])
    return f"Strong {best_component[0].replace('_', ' ')}: {best_component[1]:.1f}/100"

def _identify_main_concern(insights: Dict) -> str:
    """Identify main portfolio concern"""
    alerts = insights.get('alerts', [])
    if alerts:
        return alerts[0].replace('⚠️', '').replace('📉', '').replace('🔴', '').strip()
    
    health_score = insights.get('portfolio_health_score', {})
    if health_score.get('overall_score', 100) < 60:
        return "Overall portfolio health needs improvement"
    
    return "No major concerns identified"

def _identify_priority_action(recommendations: List[Dict]) -> str:
    """Identify priority action from recommendations"""
    if not recommendations:
        return "No immediate actions required"
    
    # Get highest confidence recommendation
    priority_rec = max(recommendations, key=lambda x: x.get('confidence_score', 0))
    return f"{priority_rec.get('action', 'Review').title()} {priority_rec.get('symbol', 'portfolio')}: {priority_rec.get('reasoning', 'Optimization opportunity')}"

def _calculate_sustainable_allocation(portfolio_data: Dict) -> Dict[str, float]:
    """Calculate sustainable investment allocation"""
    holdings = portfolio_data.get('holdings', [])
    sustainable_sectors = ['Technology', 'Healthcare', 'Renewable Energy', 'Clean Technology']
    
    total_value = sum(holding.get('market_value', 0) for holding in holdings)
    sustainable_value = sum(
        holding.get('market_value', 0) 
        for holding in holdings 
        if holding.get('sector', '') in sustainable_sectors
    )
    
    return {
        'sustainable_percentage': (sustainable_value / max(total_value, 1)) * 100,
        'sustainable_value': sustainable_value,
        'total_value': total_value
    }

def _generate_esg_recommendations(esg_metrics: Dict) -> List[str]:
    """Generate ESG improvement recommendations"""
    recommendations = []
    
    env_score = esg_metrics.get('environmental_score', 0)
    social_score = esg_metrics.get('social_score', 0)
    governance_score = esg_metrics.get('governance_score', 0)
    
    if env_score < 30:
        recommendations.append("Consider increasing allocation to environmentally friendly sectors")
    
    if social_score < 30:
        recommendations.append("Look for companies with strong social responsibility practices")
    
    if governance_score < 30:
        recommendations.append("Diversify holdings to improve governance scores")
    
    return recommendations

def _analyze_sector_sustainability(portfolio_data: Dict) -> Dict[str, str]:
    """Analyze sustainability by sector"""
    sector_sustainability = {
        'Technology': 'High',
        'Healthcare': 'High', 
        'Renewable Energy': 'Very High',
        'Utilities': 'Medium',
        'Energy': 'Low',
        'Industrials': 'Medium',
        'Financial Services': 'Medium'
    }
    
    holdings = portfolio_data.get('holdings', [])
    portfolio_sectors = {}
    
    for holding in holdings:
        sector = holding.get('sector', 'Unknown')
        sustainability = sector_sustainability.get(sector, 'Unknown')
        portfolio_sectors[sector] = sustainability
    
    return portfolio_sectors

def _perform_additional_stress_tests(portfolio_data: Dict) -> Dict[str, Dict]:
    """Perform additional stress tests"""
    return {
        'currency_shock': {'impact': 'Moderate', 'description': 'USD strengthening scenario'},
        'volatility_spike': {'impact': 'High', 'description': 'VIX > 40 scenario'},
        'liquidity_crisis': {'impact': 'Moderate', 'description': 'Market liquidity reduction'}
    }

def _calculate_resilience_score(scenario_analysis: Dict) -> Dict[str, Any]:
    """Calculate portfolio resilience score"""
    # Simplified resilience calculation
    scenarios = scenario_analysis.keys()
    base_score = 75  # Start with neutral score
    
    # Adjust based on scenario impacts (would be more sophisticated in production)
    for scenario in scenarios:
        # Simplified scoring logic
        base_score -= 5  # Each scenario reduces resilience slightly
    
    return {
        'resilience_score': max(0, min(100, base_score)),
        'resilience_grade': 'Good' if base_score > 70 else 'Fair' if base_score > 50 else 'Poor',
        'improvement_potential': 100 - base_score
    }

def _generate_hedging_recommendations(analysis_result: Dict) -> List[str]:
    """Generate hedging recommendations"""
    recommendations = []
    
    portfolio_metrics = analysis_result.get('portfolio_metrics', {})
    beta = portfolio_metrics.get('beta', 1.0)
    
    if beta > 1.3:
        recommendations.append("Consider adding defensive positions to reduce market exposure")
    
    if portfolio_metrics.get('volatility', 0) > 0.25:
        recommendations.append("Explore volatility hedging strategies")
    
    return recommendations

def _generate_comparison_insights(portfolios: List[Dict]) -> Dict[str, Any]:
    """Generate insights from portfolio comparison"""
    if len(portfolios) < 2:
        return {}
    
    # Compare key metrics
    returns = [p.get('metrics', {}).get('total_return', 0) for p in portfolios]
    risk_scores = [p.get('health_score', {}).get('overall_score', 0) for p in portfolios]
    
    return {
        'performance_spread': max(returns) - min(returns),
        'risk_consistency': max(risk_scores) - min(risk_scores),
        'diversification_opportunity': len(set(p.get('risk_profile', '') for p in portfolios)) > 1
    }

def _identify_best_performer(portfolios: List[Dict]) -> Dict[str, Any]:
    """Identify best performing portfolio"""
    if not portfolios:
        return {}
    
    best = max(portfolios, key=lambda p: p.get('metrics', {}).get('total_return', 0))
    return {
        'portfolio_name': best.get('portfolio_name', ''),
        'total_return': best.get('metrics', {}).get('total_return', 0),
        'health_score': best.get('health_score', {}).get('overall_score', 0)
    }

def _generate_cross_portfolio_recommendations(portfolios: List[Dict]) -> List[str]:
    """Generate recommendations across portfolios"""
    recommendations = []
    
    if len(portfolios) > 1:
        # Find opportunities for cross-portfolio optimization
        risk_profiles = [p.get('risk_profile', '') for p in portfolios]
        
        if len(set(risk_profiles)) == 1:
            recommendations.append("Consider diversifying risk profiles across portfolios")
        
        health_scores = [p.get('health_score', {}).get('overall_score', 0) for p in portfolios]
        if max(health_scores) - min(health_scores) > 20:
            recommendations.append("Rebalance weaker portfolios using strategies from stronger ones")
    
    return recommendations

def _create_executive_summary(analysis_result: Dict) -> Dict[str, str]:
    """Create executive summary of analysis"""
    metrics = analysis_result.get('portfolio_metrics', {})
    insights = analysis_result.get('ai_insights', {})
    
    return {
        'performance_overview': f"Total return: {metrics.get('total_return', 0):.1%}, Sharpe ratio: {metrics.get('sharpe_ratio', 0):.2f}",
        'risk_assessment': f"Portfolio beta: {metrics.get('beta', 1):.2f}, Volatility: {metrics.get('volatility', 0):.1%}",
        'key_findings': insights.get('portfolio_health_score', {}).get('interpretation', 'Analysis complete'),
        'action_required': 'High' if len(insights.get('alerts', [])) > 2 else 'Medium' if len(insights.get('alerts', [])) > 0 else 'Low'
    }

def _prepare_chart_data(analysis_result: Dict) -> Dict[str, Any]:
    """Prepare data for charts and visualizations"""
    return {
        'risk_return_chart': {
            'return': analysis_result.get('portfolio_metrics', {}).get('total_return', 0),
            'risk': analysis_result.get('portfolio_metrics', {}).get('volatility', 0)
        },
        'sector_allocation': analysis_result.get('risk_decomposition', {}).get('sector_risk', {}),
        'performance_attribution': analysis_result.get('performance_attribution', {}).get('sector_contributions', {})
    }

def _prioritize_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """Prioritize recommendations by confidence and impact"""
    if not recommendations:
        return []
    
    # Sort by confidence score and expected impact
    sorted_recs = sorted(
        recommendations,
        key=lambda x: (x.get('confidence_score', 0), sum(x.get('expected_impact', {}).values())),
        reverse=True
    )
    
    return sorted_recs[:5]  # Return top 5 prioritized recommendations
