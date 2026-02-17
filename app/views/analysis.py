from flask import request, redirect, url_for

def init_analysis_routes(app):
    @app.route('/analysis/warren-buffett')
    def warren_buffett():
        """Legacy route kept for compatibility; redirect to blueprint implementation.

        EKTE-only policy: do not render demo/simulated data here.
        """
        try:
            # If blueprint endpoint exists, redirect there
            if 'analysis.warren_buffett' in app.view_functions:
                return redirect(url_for('analysis.warren_buffett'), code=302)
        except Exception:
            pass
        # Fallback: redirect to analysis index
        return redirect(url_for('analysis.index'), code=302)

    # This route has been moved to app/routes/analysis.py to fix blueprint routing
    # @app.route('/analysis/short-analysis', methods=['GET', 'POST'])
    # def short_analysis():
    #     try:
    #         if request.method == 'POST':
    #             ticker = request.form.get('ticker', '').upper()
    #         else:
    #             ticker = request.args.get('ticker', '').upper()
    #
    #         if ticker:
    #             data = get_stock_data(ticker)
    #             if not data:
    #                 data = generate_demo_data(ticker)
    #         else:
    #             data = None
    #         return render_template('analysis/short-analysis.html',
    #                              ticker=ticker,
    #                              stock_data=data,
    #                              error=False)
    #     except Exception as e:
    #         app.logger.error(f"Short analysis error: {str(e)}")
    #     return render_template('analysis/short-analysis.html',
    #                          ticker=ticker,
    #                          stock_data=None,
    #                          error=True)