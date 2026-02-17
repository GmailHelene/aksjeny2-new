def get_sector_data():
    try:
        from flask_login import current_user
        import requests
        # If user is authenticated, fetch real sector data from API
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            try:
                from app.services.external_data import external_data_service
                overview = external_data_service.get_market_overview()
                if 'sector_performance' in overview:
                    sectors = []
                    for sector, data in overview['sector_performance'].items():
                        sectors.append({
                            'name': sector.title(),
                            'performance': data['performance'],
                            'trend': data['trend']
                        })
                    return sectors
            except ImportError:
                # external_data service not available, return demo data
                pass
            except Exception as api_error:
                pass  # Faller tilbake til demo-data
        # Non-authenticated users eller feil gir demo-data
        return generate_demo_sectors()
    except Exception as e:
        # If any error, return demo data
        return generate_demo_sectors()

def generate_demo_sectors():
    """Generate demo sector data for non-authenticated users"""
    return [
        {
            'name': 'Energy',
            'performance': 2.1,
            'trend': 'Up'
        },
        {
            'name': 'Technology',
            'performance': 1.5,
            'trend': 'Up'
        },
        {
            'name': 'Healthcare',
            'performance': 0.8,
            'trend': 'Up'
        },
        {
            'name': 'Finance',
            'performance': 0.3,
            'trend': 'Stable'
        },
        {
            'name': 'Shipping',
            'performance': -0.2,
            'trend': 'Down'
        }
    ]

def generate_demo_market_intelligence():
    """Generate demo market intelligence data for non-authenticated users"""
    return [
        {
            'title': 'OSEBX Index',
            'summary': 'OSEBX: 1,255.30 (+0.8%) - Positiv trend med økning i handelsvolum'
        },
        {
            'title': 'Top Insider Activity', 
            'summary': 'EQNR: Kjøp +250K, DNB: Kjøp +150K, TEL: Hold - Økt institusjonell interesse'
        },
        {
            'title': 'Analyst Upgrades',
            'summary': 'EQNR: BUY→STRONG BUY (DNB), NHY: HOLD→BUY (Pareto) - Positive revisjoner denne uken'
        },
        {
            'title': 'Sector Performance',
            'summary': 'Energy: +2.1%, Technology: +1.5%, Healthcare: +0.8% - Sektorrotasjon mot energi'
        },
        {
            'title': 'Market Sentiment',
            'summary': 'VIX: 18.2 (-5.1%) - Redusert volatilitet, økende risikoappetitt blant investorer'
        }
    ]

def get_market_intelligence_data(real=False):
    try:
        if real:
            try:
                from flask_login import current_user
                from app.services.external_data import external_data_service
                if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                    overview = external_data_service.get_market_overview()
                    # Format for template: convert dict to list of sections
                    result = []
                    if 'osebx_index' in overview:
                        result.append({'title': 'OSEBX Index', 'summary': f"Value: {overview['osebx_index']['value']}, Change: {overview['osebx_index']['change']} ({overview['osebx_index']['change_percent']}%), Trend: {overview['osebx_index']['trend']}"})
                    if 'top_insider_activity' in overview:
                        summary = ', '.join([f"{a['symbol']}: {a['net_activity']} (Confidence: {a['confidence']})" for a in overview['top_insider_activity']])
                        result.append({'title': 'Top Insider Activity', 'summary': summary})
                    if 'analyst_upgrades' in overview:
                        summary = ', '.join([f"{a['symbol']}: {a['from']}→{a['to']} ({a['firm']})" for a in overview['analyst_upgrades']])
                        result.append({'title': 'Analyst Upgrades', 'summary': summary})
                    if 'sector_performance' in overview:
                        summary = ', '.join([f"{s}: {d['performance']}% ({d['trend']})" for s, d in overview['sector_performance'].items()])
                        result.append({'title': 'Sector Performance', 'summary': summary})
                    if 'market_sentiment' in overview:
                        sentiment = overview['market_sentiment']
                        summary = f"Overall: {sentiment['overall']}, Fear/Greed: {sentiment['fear_greed_index']}, Volatility: {sentiment['volatility_index']}"
                        result.append({'title': 'Market Sentiment', 'summary': summary})
                    return result if result else generate_demo_market_intelligence()
                else:
                    return generate_demo_market_intelligence()
            except ImportError:
                # external_data service not available, return demo data
                return generate_demo_market_intelligence()
            except Exception as e:
                # Any other error, return demo data
                return generate_demo_market_intelligence()
        else:
            return generate_demo_market_intelligence()
    except Exception as e:
        # Fallback for any error
        return generate_demo_market_intelligence()

def get_analyst_coverage_data(real=False):
    try:
        if real:
            try:
                from flask_login import current_user
                from app.services.external_data import external_data_service
                if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                    top_stocks = ['EQNR', 'DNB', 'TEL', 'AKER', 'MOWI']
                    analyst_coverage = {}
                    for symbol in top_stocks:
                        try:
                            analyst_data = external_data_service.get_norwegian_analyst_data(symbol)
                            consensus = analyst_data.get('consensus', {})
                            analyst_coverage[symbol] = {
                                'ratings': {
                                    'consensus': consensus.get('rating', 'HOLD'),
                                    'target_price': consensus.get('avg_target_price', 0),
                                    'num_analysts': consensus.get('num_analysts', 0)
                                },
                                'consensus': {
                                    'recommendation': consensus.get('rating', 'HOLD')
                                },
                                'technical': {
                                    'trend': 'Neutral',
                                    'support': None,
                                    'resistance': None
                                }
                            }
                        except Exception as e:
                            analyst_coverage[symbol] = {
                                'ratings': {'consensus': 'HOLD', 'target_price': 0, 'num_analysts': 0},
                                'consensus': {'recommendation': 'HOLD'},
                                'technical': {'trend': 'Neutral', 'support': None, 'resistance': None}
                            }
                    return analyst_coverage
                else:
                    return generate_demo_analyst_coverage_dict()
            except ImportError:
                # external_data service not available, return demo data
                return generate_demo_analyst_coverage_dict()
            except Exception as e:
                # Any other error, return demo data
                return generate_demo_analyst_coverage_dict()
        else:
            return generate_demo_analyst_coverage_dict()
    except Exception as e:
        # Fallback for any error
        return generate_demo_analyst_coverage_dict()

def generate_demo_analyst_coverage_dict():
    """Generate demo analyst coverage data in dict format for template"""
    demo_data = generate_demo_analyst_coverage()
    result = {}
    for item in demo_data:
        symbol = item['symbol']
        result[symbol] = {
            'ratings': {
                'consensus': item['recommendation'],
                'target_price': item['target_price'],
                'num_analysts': item.get('num_analysts', 8)
            },
            'consensus': {
                'recommendation': item['recommendation']
            },
            'technical': {
                'trend': 'Neutral',
                'support': None,
                'resistance': None
            }
        }
    return result

def generate_demo_analyst_coverage():
    """Generate demo analyst coverage data for non-authenticated users"""
    return [
        {'company': 'Equinor ASA', 'symbol': 'EQNR', 'recommendation': 'BUY', 'firm': 'DNB Markets', 'date': '2025-08-27', 'target_price': 320},
        {'company': 'DNB Bank ASA', 'symbol': 'DNB', 'recommendation': 'HOLD', 'firm': 'Pareto Securities', 'date': '2025-08-27', 'target_price': 195},
        {'company': 'Telenor ASA', 'symbol': 'TEL', 'recommendation': 'BUY', 'firm': 'SEB', 'date': '2025-08-26', 'target_price': 165},
        {'company': 'Aker Solutions', 'symbol': 'AKERSOL', 'recommendation': 'STRONG BUY', 'firm': 'SpareBank 1', 'date': '2025-08-25', 'target_price': 45},
        {'company': 'Mowi ASA', 'symbol': 'MOWI', 'recommendation': 'HOLD', 'firm': 'Carnegie', 'date': '2025-08-24', 'target_price': 220}
    ]
