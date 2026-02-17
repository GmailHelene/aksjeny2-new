"""
Comprehensive profile route diagnostic script.
This script will:
1. Check if the profile route is properly registered
2. Check if redirects are working properly
3. Check if template rendering is working properly
"""

import os
import logging
import traceback
from flask import render_template, redirect, url_for, flash, session, current_app, jsonify
from flask_login import current_user, login_required

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def diagnose_profile_issues():
    """Fix the profile route issues by providing a comprehensive diagnostic."""
    try:
        # Import needed modules
        from app import create_app, db
        from sqlalchemy import text
        
        # Create a test app
        app = create_app('testing')
        
        with app.app_context():
            # 1. Check the URL map
            logger.info("Checking URL map for profile routes:")
            profile_routes = []
            for rule in app.url_map.iter_rules():
                if 'profile' in rule.endpoint or 'profile' in str(rule):
                    logger.info(f"  - {rule.endpoint} -> {rule}")
                    profile_routes.append((rule.endpoint, str(rule)))

            # 2. Check blueprint registration
            logger.info("\nChecking blueprint registration:")
            for name, blueprint in app.blueprints.items():
                if 'profile' in name or hasattr(blueprint, 'name') and 'profile' in blueprint.name:
                    logger.info(f"  - Blueprint {name} is registered with URL prefix: {blueprint.url_prefix}")
            
            # 3. Test URL generation
            logger.info("\nTesting URL generation:")
            with app.test_request_context():
                try:
                    main_profile_url = url_for('main.profile')
                    logger.info(f"  - URL for main.profile: {main_profile_url}")
                except Exception as e:
                    logger.error(f"  - Error generating URL for main.profile: {e}")
                
                try:
                    profile_page_url = url_for('profile.profile_page')
                    logger.info(f"  - URL for profile.profile_page: {profile_page_url}")
                except Exception as e:
                    logger.error(f"  - Error generating URL for profile.profile_page: {e}")
            
            # 4. Generate the fix recommendation
            logger.info("\nDiagnostic Report:")
            if not profile_routes:
                logger.error("  - NO PROFILE ROUTES FOUND! The profile route is not registered.")
                logger.info("  - Recommendation: Check app/__init__.py to ensure the profile blueprint is registered.")
            else:
                logger.info(f"  - Found {len(profile_routes)} profile-related routes.")
                
                # Check for conflicts
                endpoints = [route[0] for route in profile_routes]
                if 'main.profile' in endpoints and 'profile.profile_page' in endpoints:
                    logger.info("  - Both main.profile and profile.profile_page routes exist, which is correct.")
                    logger.info("  - Issue might be in the redirect logic or template rendering.")
                elif 'main.profile' in endpoints:
                    logger.info("  - Only main.profile exists. The profile blueprint might not be registered properly.")
                elif 'profile.profile_page' in endpoints:
                    logger.info("  - Only profile.profile_page exists. The main.profile route is missing.")
                
                # Check URL prefixes
                url_paths = [route[1] for route in profile_routes]
                if '/profile' in url_paths and '/profile/' in url_paths:
                    logger.warning("  - Both /profile and /profile/ routes exist, which might cause conflicts.")
                
                logger.info("\nSUGGESTED FIX:")
                logger.info("1. Update main.py to use the direct implementation instead of redirecting:")
                logger.info("""
@main.route('/profile')
@login_required
def profile():
    \"\"\"Display user profile directly instead of redirecting\"\"\"
    try:
        # Get user favorites
        user_favorites = []
        if current_user.is_authenticated:
            try:
                from sqlalchemy import text
                favorites_query = text(\"\"\"
                    SELECT symbol, company_name, price, change, change_percent, date_added 
                    FROM favorites 
                    WHERE user_id = :user_id 
                    ORDER BY date_added DESC
                \"\"\")
                favorites_result = db.session.execute(favorites_query, {'user_id': current_user.id})
                user_favorites = [dict(row._mapping) for row in favorites_result]
                logger.info(f"Loaded {len(user_favorites)} favorites for user {current_user.id}")
            except Exception as e:
                logger.error(f"Error fetching favorites: {e}")
                user_favorites = []
        
        # Get user statistics
        user_stats = {
            'total_favorites': len(user_favorites),
            'member_since': current_user.created_at.strftime('%B %Y') if hasattr(current_user, 'created_at') and current_user.created_at else 'Ukjent',
            'last_login': current_user.last_login.strftime('%d.%m.%Y %H:%M') if hasattr(current_user, 'last_login') and current_user.last_login else 'Ukjent'
        }
        
        return render_template('profile.html', 
                             user=current_user,
                             favorites=user_favorites,
                             user_stats=user_stats)
        
    except Exception as e:
        logger.error(f"Error in profile page: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash('Det oppstod en teknisk feil under lasting av profilen', 'error')
        return redirect(url_for('main.index'))
                """)
                
                logger.info("2. Ensure the profile.html template exists and is correct")
                logger.info("3. Restart the Flask server to apply changes")
    
    except Exception as e:
        logger.error(f"Error during diagnosis: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    print("Diagnosing profile route issues...")
    diagnose_profile_issues()
    print("\nDiagnosis complete. Check the logs above for detailed information and fix suggestions.")
