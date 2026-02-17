#!/usr/bin/env python3
"""Quick Warren Buffett analysis test"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.services.buffett_analysis_service import BuffettAnalysisService
        
        print("Testing Warren Buffett analysis for AAPL...")
        result = BuffettAnalysisService.analyze_stock("AAPL")
        
        if result:
            print("✅ SUCCESS! Warren Buffett analysis working")
            print(f"Score: {result.get('score', 'N/A')}")
            print(f"Recommendation: {result.get('recommendation', {}).get('action', 'N/A')}")
        else:
            print("❌ FAILED! No result from analysis")
            
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
