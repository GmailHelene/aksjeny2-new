from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging
import random
from ..utils.access_control import access_required, demo_access, premium_required
from ..extensions import csrf

investment_analyzer_bp = Blueprint('investment_analyzer', __name__, url_prefix='/investment-analyzer')
logger = logging.getLogger(__name__)

@investment_analyzer_bp.route('/')
@premium_required
def index():
    """Main investment analyzer page"""
    return render_template('investment_analyzer/index.html',
                         title='Investeringsanalyse - AI-drevet anbefalinger')

@investment_analyzer_bp.route('/analyze', methods=['POST'])
@csrf.exempt
def analyze_investments():
    """Perform investment analysis based on user criteria"""
    try:
        # Get user input parameters
        data = request.get_json()
        
        investment_amount = float(data.get('investment_amount', 10000))
        time_horizon = data.get('time_horizon', '1_month')  # 1_day, 1_week, 1_month, 3_months, 6_months, 1_year, 1_year_plus
        risk_level = data.get('risk_level', 'medium')  # low, medium, high, very_high
        asset_types = data.get('asset_types', ['stocks', 'crypto', 'currency'])
        
        # Check access level for result limiting
        is_premium = False
        if current_user.is_authenticated:
            if getattr(current_user, 'email', None) in ['testuser@aksjeradar.trade', 'helene721@gmail.com', 'eiriktollan.berntsen@gmail.com', 'tonjekit91@gmail.com']:
                is_premium = True
            elif hasattr(current_user, 'has_active_subscription') and current_user.has_active_subscription():
                is_premium = True
        
        # Analyze investments based on criteria
        recommendations = perform_investment_analysis(
            investment_amount, time_horizon, risk_level, asset_types
        )
        
        # Limit results for demo users
        if not is_premium:
            recommendations = recommendations[:3]  # Demo users get top 3 recommendations
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'analysis_summary': generate_analysis_summary(recommendations, investment_amount),
            'demo_mode': not is_premium
        })
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in investment analysis: {error_message}")
        
        # Provide more specific error message based on the type of error
        user_message = 'En feil oppstod under analysen. '
        if 'investment_amount' in error_message.lower():
            user_message += 'Vennligst sjekk at investeringsbeløpet er gyldig.'
        elif 'time_horizon' in error_message.lower():
            user_message += 'Vennligst velg en gyldig tidshorisont.'
        elif 'risk_level' in error_message.lower():
            user_message += 'Vennligst velg et gyldig risikonivå.'
        else:
            user_message += 'Prøv igjen senere eller kontakt support hvis problemet vedvarer.'
            
        return jsonify({
            'success': False,
            'error': user_message
        }), 500

def perform_investment_analysis(amount, time_horizon, risk_level, asset_types):
    """Core investment analysis logic"""
    
    # Mock data - in production, this would connect to real market data APIs
    all_assets = get_market_data_for_analysis()
    
    # Filter assets based on criteria
    filtered_assets = filter_assets_by_criteria(all_assets, time_horizon, risk_level, asset_types)
    
    # Score and rank assets
    scored_assets = score_assets(filtered_assets, amount, time_horizon, risk_level)
    
    # Return top 10 recommendations
    return scored_assets[:10]

def get_market_data_for_analysis():
    """Get comprehensive market data - mock implementation"""
    return {
        'stocks': [
            {
                'symbol': 'EQNR.OL',
                'name': 'Equinor ASA',
                'current_price': 285.40,
                'market_cap': 920000000000,
                'volatility': 0.25,
                'trend_score': 0.8,
                'technical_score': 0.75,
                'fundamental_score': 0.85,
                'momentum': 0.65,
                'volume_trend': 0.7,
                'sector': 'Energy',
                'beta': 1.2,
                'dividend_yield': 0.028
            },
            {
                'symbol': 'DNB.OL',
                'name': 'DNB Bank ASA',
                'current_price': 198.50,
                'market_cap': 280000000000,
                'volatility': 0.20,
                'trend_score': 0.75,
                'technical_score': 0.8,
                'fundamental_score': 0.9,
                'momentum': 0.7,
                'volume_trend': 0.75,
                'sector': 'Financial',
                'beta': 0.9,
                'dividend_yield': 0.052
            },
            {
                'symbol': 'MOWI.OL',
                'name': 'Mowi ASA',
                'current_price': 195.40,
                'market_cap': 102000000000,
                'volatility': 0.30,
                'trend_score': 0.85,
                'technical_score': 0.7,
                'fundamental_score': 0.75,
                'momentum': 0.8,
                'volume_trend': 0.65,
                'sector': 'Consumer Staples',
                'beta': 1.1,
                'dividend_yield': 0.035
            },
            {
                'symbol': 'YAR.OL',
                'name': 'Yara International',
                'current_price': 425.80,
                'market_cap': 108000000000,
                'volatility': 0.35,
                'trend_score': 0.9,
                'technical_score': 0.85,
                'fundamental_score': 0.7,
                'momentum': 0.85,
                'volume_trend': 0.8,
                'sector': 'Materials',
                'beta': 1.3,
                'dividend_yield': 0.019
            },
            {
                'symbol': 'TEL.OL',
                'name': 'Telenor ASA',
                'current_price': 115.20,
                'market_cap': 155000000000,
                'volatility': 0.18,
                'trend_score': 0.6,
                'technical_score': 0.65,
                'fundamental_score': 0.8,
                'momentum': 0.5,
                'volume_trend': 0.6,
                'sector': 'Communication',
                'beta': 0.7,
                'dividend_yield': 0.041
            }
        ],
        'crypto': [
            {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'current_price': 43245.67,
                'market_cap': 850000000000,
                'volatility': 0.80,
                'trend_score': 0.85,
                'technical_score': 0.8,
                'momentum': 0.9,
                'volume_trend': 0.85,
                'sector': 'Cryptocurrency',
                'correlation_stocks': 0.3
            },
            {
                'symbol': 'ETH',
                'name': 'Ethereum',
                'current_price': 2456.32,
                'market_cap': 295000000000,
                'volatility': 0.85,
                'trend_score': 0.8,
                'technical_score': 0.85,
                'momentum': 0.85,
                'volume_trend': 0.8,
                'sector': 'Cryptocurrency',
                'correlation_stocks': 0.35
            },
            {
                'symbol': 'SOL',
                'name': 'Solana',
                'current_price': 152.78,
                'market_cap': 71000000000,
                'volatility': 1.2,
                'trend_score': 0.95,
                'technical_score': 0.9,
                'momentum': 0.95,
                'volume_trend': 0.9,
                'sector': 'Cryptocurrency',
                'correlation_stocks': 0.25
            },
            {
                'symbol': 'ADA',
                'name': 'Cardano',
                'current_price': 0.456,
                'market_cap': 16000000000,
                'volatility': 1.0,
                'trend_score': 0.75,
                'technical_score': 0.7,
                'momentum': 0.8,
                'volume_trend': 0.7,
                'sector': 'Cryptocurrency',
                'correlation_stocks': 0.2
            }
        ],
        'currency': [
            {
                'symbol': 'EUR/USD',
                'name': 'Euro/US Dollar',
                'current_price': 1.0892,
                'volatility': 0.15,
                'trend_score': 0.6,
                'technical_score': 0.65,
                'momentum': 0.55,
                'volume_trend': 0.6,
                'sector': 'Currency',
                'carry_trade_potential': 0.3
            },
            {
                'symbol': 'GBP/USD',
                'name': 'British Pound/US Dollar',
                'current_price': 1.2745,
                'volatility': 0.18,
                'trend_score': 0.55,
                'technical_score': 0.6,
                'momentum': 0.5,
                'volume_trend': 0.55,
                'sector': 'Currency',
                'carry_trade_potential': 0.25
            },
            {
                'symbol': 'USD/NOK',
                'name': 'US Dollar/Norwegian Krone',
                'current_price': 10.6745,
                'volatility': 0.12,
                'trend_score': 0.7,
                'technical_score': 0.75,
                'momentum': 0.65,
                'volume_trend': 0.7,
                'sector': 'Currency',
                'carry_trade_potential': 0.4
            }
        ]
    }

def filter_assets_by_criteria(assets, time_horizon, risk_level, asset_types):
    """Filter assets based on user criteria"""
    filtered = []
    
    # Risk level mappings
    risk_thresholds = {
        'low': {'max_volatility': 0.25, 'min_market_cap': 50000000000},
        'medium': {'max_volatility': 0.50, 'min_market_cap': 10000000000},
        'high': {'max_volatility': 0.80, 'min_market_cap': 1000000000},
        'very_high': {'max_volatility': 2.0, 'min_market_cap': 100000000}
    }
    
    risk_config = risk_thresholds.get(risk_level, risk_thresholds['medium'])
    
    # Filter each asset type
    for asset_type in asset_types:
        if asset_type in assets:
            for asset in assets[asset_type]:
                # Check volatility constraint
                if asset['volatility'] <= risk_config['max_volatility']:
                    # Check market cap for stocks and crypto
                    if asset_type in ['stocks', 'crypto']:
                        if asset.get('market_cap', 0) >= risk_config['min_market_cap']:
                            asset['asset_type'] = asset_type
                            filtered.append(asset)
                    else:
                        # Currency pairs
                        asset['asset_type'] = asset_type
                        filtered.append(asset)
    
    return filtered

def score_assets(assets, amount, time_horizon, risk_level):
    """Score and rank assets based on analysis criteria"""
    
    # Time horizon weights
    horizon_weights = {
        '1_day': {'momentum': 0.4, 'technical': 0.4, 'trend': 0.2},
        '1_week': {'momentum': 0.35, 'technical': 0.35, 'trend': 0.3},
        '1_month': {'momentum': 0.3, 'technical': 0.3, 'trend': 0.4},
        '3_months': {'momentum': 0.25, 'technical': 0.25, 'trend': 0.35, 'fundamental': 0.15},
        '6_months': {'momentum': 0.2, 'technical': 0.2, 'trend': 0.3, 'fundamental': 0.3},
        '1_year': {'momentum': 0.15, 'technical': 0.15, 'trend': 0.25, 'fundamental': 0.45},
        '1_year_plus': {'momentum': 0.1, 'technical': 0.1, 'trend': 0.2, 'fundamental': 0.6}
    }
    
    weights = horizon_weights.get(time_horizon, horizon_weights['1_month'])
    
    scored_assets = []
    
    for asset in assets:
        # Calculate composite score
        score = 0
        
        # Basic scoring components
        if 'momentum' in weights:
            score += asset.get('momentum', 0) * weights['momentum']
        if 'technical' in weights:
            score += asset.get('technical_score', 0) * weights['technical']
        if 'trend' in weights:
            score += asset.get('trend_score', 0) * weights['trend']
        if 'fundamental' in weights:
            score += asset.get('fundamental_score', 0.5) * weights['fundamental']
        
        # Risk-adjusted scoring
        risk_multiplier = calculate_risk_multiplier(asset, risk_level)
        score *= risk_multiplier
        
        # Volume and liquidity bonus
        volume_bonus = asset.get('volume_trend', 0.5) * 0.1
        score += volume_bonus
        
        # Calculate potential returns and position size
        position_info = calculate_position_size(asset, amount, time_horizon)
        
        # Store scored asset
        scored_asset = {
            'symbol': asset['symbol'],
            'name': asset['name'],
            'asset_type': asset['asset_type'],
            'current_price': asset['current_price'],
            'score': round(score, 3),
            'risk_level': categorize_risk(asset['volatility']),
            'expected_return': calculate_expected_return(asset, time_horizon),
            'position_size': position_info['shares'],
            'position_value': position_info['value'],
            'stop_loss': position_info['stop_loss'],
            'take_profit': position_info['take_profit'],
            'reasoning': generate_reasoning(asset, score, time_horizon),
            'sector': asset.get('sector', 'Unknown'),
            'volatility': asset['volatility']
        }
        
        scored_assets.append(scored_asset)
    
    # Sort by score descending
    return sorted(scored_assets, key=lambda x: x['score'], reverse=True)

def calculate_risk_multiplier(asset, risk_level):
    """Calculate risk multiplier based on user risk tolerance"""
    volatility = asset['volatility']
    
    if risk_level == 'low':
        # Prefer low volatility assets
        return max(0.5, 1.5 - volatility)
    elif risk_level == 'medium':
        # Balanced approach
        return 1.0
    elif risk_level == 'high':
        # Slight preference for higher volatility
        return min(1.5, 1.0 + volatility * 0.3)
    else:  # very_high
        # Strong preference for high volatility
        return min(2.0, 1.0 + volatility * 0.5)

def calculate_position_size(asset, amount, time_horizon):
    """Calculate appropriate position size and risk management levels"""
    price = asset['current_price']
    shares = int(amount / price) if price > 0 else 0
    value = shares * price
    
    # Risk management based on volatility and time horizon
    volatility = asset['volatility']
    
    # Stop loss percentage (higher volatility = wider stops)
    stop_loss_pct = max(0.05, min(0.20, volatility * 0.8))
    
    # Take profit based on time horizon and expected returns
    horizon_multipliers = {
        '1_day': 1.5, '1_week': 2.0, '1_month': 2.5,
        '3_months': 3.0, '6_months': 4.0, '1_year': 5.0, '1_year_plus': 6.0
    }
    
    take_profit_pct = stop_loss_pct * horizon_multipliers.get(time_horizon, 2.5)
    
    return {
        'shares': shares,
        'value': round(value, 2),
        'stop_loss': round(price * (1 - stop_loss_pct), 2),
        'take_profit': round(price * (1 + take_profit_pct), 2)
    }

def calculate_expected_return(asset, time_horizon):
    """Calculate expected return based on asset characteristics and time horizon"""
    base_return = asset.get('trend_score', 0.5) * 0.3
    momentum_return = asset.get('momentum', 0.5) * 0.2
    technical_return = asset.get('technical_score', 0.5) * 0.1
    
    # Time horizon multipliers
    horizon_multipliers = {
        '1_day': 0.005, '1_week': 0.02, '1_month': 0.08,
        '3_months': 0.15, '6_months': 0.25, '1_year': 0.40, '1_year_plus': 0.60
    }
    
    expected_return = (base_return + momentum_return + technical_return) * \
                     horizon_multipliers.get(time_horizon, 0.08)
    
    return round(expected_return * 100, 1)  # Return as percentage

def categorize_risk(volatility):
    """Categorize risk level based on volatility"""
    if volatility <= 0.15:
        return 'Lav'
    elif volatility <= 0.30:
        return 'Middels'
    elif volatility <= 0.60:
        return 'Høy'
    else:
        return 'Svært høy'

def generate_reasoning(asset, score, time_horizon):
    """Generate human-readable reasoning for the recommendation"""
    reasons = []
    
    # Technical analysis reasoning
    if asset.get('technical_score', 0) > 0.7:
        reasons.append("Sterke tekniske signaler")
    elif asset.get('technical_score', 0) > 0.6:
        reasons.append("Positive tekniske indikatorer")
    
    # Momentum reasoning
    if asset.get('momentum', 0) > 0.8:
        reasons.append("Høy momentum")
    elif asset.get('momentum', 0) > 0.6:
        reasons.append("Positiv momentum")
    
    # Trend reasoning
    if asset.get('trend_score', 0) > 0.8:
        reasons.append("Sterk opptrend")
    elif asset.get('trend_score', 0) > 0.6:
        reasons.append("Positiv trend")
    
    # Fundamental reasoning (for stocks)
    if asset.get('fundamental_score', 0) > 0.8 and time_horizon in ['6_months', '1_year', '1_year_plus']:
        reasons.append("Sterke fundamentale faktorer")
    
    # Sector-specific reasoning
    sector = asset.get('sector', '')
    if sector == 'Energy' and asset.get('trend_score', 0) > 0.7:
        reasons.append("Energisektor viser styrke")
    elif sector == 'Financial' and asset.get('fundamental_score', 0) > 0.8:
        reasons.append("Solid finansiell posisjon")
    elif sector == 'Cryptocurrency' and asset.get('momentum', 0) > 0.8:
        reasons.append("Krypto-momentum")
    
    # Default reasoning
    if not reasons:
        reasons.append("Balansert risiko/avkastning-profil")
    
    return ", ".join(reasons)

def generate_analysis_summary(recommendations, investment_amount):
    """Generate analysis summary"""
    if not recommendations:
        return {
            'total_recommendations': 0,
            'avg_expected_return': 0,
            'risk_distribution': {},
            'asset_distribution': {}
        }
    
    # Calculate statistics
    total_recs = len(recommendations)
    avg_return = sum(rec['expected_return'] for rec in recommendations) / total_recs
    
    # Risk distribution
    risk_dist = {}
    for rec in recommendations:
        risk = rec['risk_level']
        risk_dist[risk] = risk_dist.get(risk, 0) + 1
    
    # Asset type distribution
    asset_dist = {}
    for rec in recommendations:
        asset_type = rec['asset_type']
        asset_dist[asset_type] = asset_dist.get(asset_type, 0) + 1
    
    return {
        'total_recommendations': total_recs,
        'avg_expected_return': round(avg_return, 1),
        'risk_distribution': risk_dist,
        'asset_distribution': asset_dist,
        'investment_amount': investment_amount
    }

@investment_analyzer_bp.route('/portfolio-optimization', methods=['POST'])
@access_required
def optimize_portfolio():
    """Optimize portfolio allocation across recommended assets"""
    try:
        data = request.get_json()
        selected_assets = data.get('selected_assets', [])
        investment_amount = float(data.get('investment_amount', 10000))
        risk_level = data.get('risk_level', 'medium')
        
        # Perform portfolio optimization
        optimized_portfolio = perform_portfolio_optimization(
            selected_assets, investment_amount, risk_level
        )
        
        return jsonify({
            'success': True,
            'optimized_portfolio': optimized_portfolio
        })
        
    except Exception as e:
        logger.error(f"Error in portfolio optimization: {e}")
        return jsonify({
            'success': False,
            'error': 'Feil ved porteføljeoptimalisering.'
        }), 500

def perform_portfolio_optimization(assets, total_amount, risk_level):
    """Simple portfolio optimization based on risk parity and expected returns"""
    if not assets:
        return []
    
    # Risk-based allocation weights
    risk_weights = []
    for asset in assets:
        volatility = asset.get('volatility', 0.3)
        # Inverse volatility weighting (lower vol = higher weight for risk parity)
        risk_weight = 1 / max(volatility, 0.01)
        risk_weights.append(risk_weight)
    
    # Normalize weights
    total_risk_weight = sum(risk_weights)
    normalized_weights = [w / total_risk_weight for w in risk_weights]
    
    # Adjust weights based on expected returns and user risk level
    optimized_assets = []
    for i, asset in enumerate(assets):
        base_weight = normalized_weights[i]
        
        # Return-based adjustment
        expected_return = asset.get('expected_return', 5.0)
        return_multiplier = 1 + (expected_return / 100) * 0.5
        
        # Risk level adjustment
        if risk_level == 'low':
            # Conservative: reduce high-risk asset weights
            if asset.get('volatility', 0) > 0.4:
                return_multiplier *= 0.7
        elif risk_level == 'high' or risk_level == 'very_high':
            # Aggressive: increase high-return asset weights
            if expected_return > 10:
                return_multiplier *= 1.3
        
        final_weight = base_weight * return_multiplier
        allocation = total_amount * final_weight
        
        optimized_asset = asset.copy()
        optimized_asset.update({
            'allocation_weight': round(final_weight * 100, 1),
            'allocation_amount': round(allocation, 2),
            'shares_to_buy': int(allocation / asset['current_price']),
            'actual_allocation': round(int(allocation / asset['current_price']) * asset['current_price'], 2)
        })
        
        optimized_assets.append(optimized_asset)
    
    return optimized_assets
