def get_comparison_data(tickers):
    from flask_login import current_user
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        from app.services.data_service import DataService
        chart_data = {}
        current_prices = {}
        price_changes = {}
        volatility = {}
        volumes = {}
        correlations = {}
        betas = {}
        ticker_names = {}
        for ticker in tickers:
            try:
                stock_info = DataService.get_stock_info(ticker)
                if stock_info:
                    # Example: chart_data could be historical prices if available
                    chart_data[ticker] = stock_info.get('historical', [])
                    current_prices[ticker] = stock_info.get('last_price', 0)
                    price_changes[ticker] = stock_info.get('change_percent', 0)
                    volatility[ticker] = stock_info.get('volatility', 0)
                    volumes[ticker] = stock_info.get('volume', 0)
                    betas[ticker] = stock_info.get('beta', 0)
                    ticker_names[ticker] = stock_info.get('name', ticker)
                else:
                    chart_data[ticker] = []
                    current_prices[ticker] = 0
                    price_changes[ticker] = 0
                    volatility[ticker] = 0
                    volumes[ticker] = 0
                    betas[ticker] = 0
                    ticker_names[ticker] = ticker
            except Exception:
                chart_data[ticker] = []
                current_prices[ticker] = 0
                price_changes[ticker] = 0
                volatility[ticker] = 0
                volumes[ticker] = 0
                betas[ticker] = 0
                ticker_names[ticker] = ticker
        # Compute pairwise Pearson correlations from historical close prices if available
        try:
            # Build simple series dict {ticker: [close,...]}
            price_series = {}
            for t in tickers:
                hist = chart_data.get(t) or []
                # Expect list of dicts with 'close' key
                closes = [p.get('close') for p in hist if isinstance(p, dict) and isinstance(p.get('close'), (int, float))]
                # Require at least 2 data points
                if len(closes) >= 2:
                    price_series[t] = closes
            def pearson(a, b):
                n = min(len(a), len(b))
                if n < 2:
                    return 0.0
                # Align lengths (truncate to shortest)
                a = a[-n:]
                b = b[-n:]
                mean_a = sum(a)/n
                mean_b = sum(b)/n
                cov = sum((x-mean_a)*(y-mean_b) for x, y in zip(a, b))
                var_a = sum((x-mean_a)**2 for x in a)
                var_b = sum((y-mean_b)**2 for y in b)
                if var_a <= 0 or var_b <= 0:
                    return 0.0
                return max(min(cov / (var_a**0.5 * var_b**0.5), 1.0), -1.0)
            for i, t1 in enumerate(tickers):
                for t2 in tickers[i+1:]:
                    if t1 in price_series and t2 in price_series:
                        try:
                            corr = pearson(price_series[t1], price_series[t2])
                        except Exception:
                            corr = 0.0
                    else:
                        corr = 0.0
                    correlations[(t1, t2)] = corr
                    correlations[(t2, t1)] = corr
        except Exception:
            # Fallback to zeros if anything unexpected
            for t1 in tickers:
                for t2 in tickers:
                    if t1 != t2:
                        correlations[(t1, t2)] = 0.0
        return {
            'chart_data': chart_data,
            'current_prices': current_prices,
            'price_changes': price_changes,
            'volatility': volatility,
            'volumes': volumes,
            'correlations': correlations,
            'betas': betas,
            'ticker_names': ticker_names
        }
    else:
        return generate_demo_comparison(tickers)

def generate_demo_comparison(tickers):
    # Dummy implementation for demo mode
    # Return static demo data for non-authenticated users
    chart_data = {}
    current_prices = {}
    price_changes = {}
    volatility = {}
    volumes = {}
    correlations = {}
    betas = {}
    ticker_names = {}
    for ticker in tickers:
        chart_data[ticker] = [
            {'date': '2023-01-01', 'close': 100, 'volume': 1000},
            {'date': '2023-01-02', 'close': 105, 'volume': 1200},
            {'date': '2023-01-03', 'close': 110, 'volume': 1100},
            {'date': '2023-01-04', 'close': 115, 'volume': 1300},
            {'date': '2023-01-05', 'close': 120, 'volume': 1250}
        ]
        current_prices[ticker] = 120
        price_changes[ticker] = 5
        volatility[ticker] = 0.02
        volumes[ticker] = 1250
        betas[ticker] = 1.0
        ticker_names[ticker] = ticker
    for t1 in tickers:
        for t2 in tickers:
            if t1 != t2:
                correlations[(t1, t2)] = 0
    return {
        'chart_data': chart_data,
        'current_prices': current_prices,
        'price_changes': price_changes,
        'volatility': volatility,
        'volumes': volumes,
        'correlations': correlations,
        'betas': betas,
        'ticker_names': ticker_names
    }
