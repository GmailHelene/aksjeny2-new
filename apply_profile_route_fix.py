"""
Fix the profile route in the application.
This script:
1. Updates the main profile route to directly implement the profile page
2. Disables the profile blueprint redirect that was causing issues
"""

import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fix_profile_route():
    """Fix the profile route by updating the implementation in main.py"""
    try:
        # Paths
        main_path = os.path.join('app', 'routes', 'main.py')
        profile_path = os.path.join('app', 'routes', 'profile.py')
        
        # 1. Update main.py profile route
        if os.path.exists(main_path):
            logger.info(f"Updating profile route in {main_path}")
            
            # Read the file
            with open(main_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the profile route
            route_def = "@main.route('/profile')"
            if route_def in content:
                # Check if it's already using the direct implementation
                if "render_template('profile.html'" in content[content.index(route_def):content.index(route_def) + 500]:
                    logger.info("Profile route already using direct implementation, no changes needed.")
                else:
                    # Find the full profile route function to replace
                    start_idx = content.index(route_def)
                    end_marker = "def "  # Next function definition
                    try:
                        next_func_idx = content.index(end_marker, start_idx + len(route_def) + 20)
                        # Go back to find the last blank line before the next function
                        nl_idx = content.rindex('\n\n', start_idx, next_func_idx)
                        route_end_idx = nl_idx
                    except ValueError:
                        # If we can't find the next function, just replace the line
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if route_def in line:
                                route_start_line = i
                                # Look for end of the function (next blank line or next route)
                                for j in range(route_start_line + 1, len(lines)):
                                    if '@main.route' in lines[j] or (j < len(lines) - 1 and not lines[j] and not lines[j+1].startswith(' ')):
                                        route_end_line = j - 1
                                        break
                                else:
                                    route_end_line = len(lines) - 1
                                
                                # Extract the old route code
                                old_route = '\n'.join(lines[route_start_line:route_end_line+1])
                                
                                # Create new content with replacement
                                new_content = content.replace(old_route, PROFILE_ROUTE_IMPLEMENTATION)
                                
                                # Write the updated file
                                with open(main_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                
                                logger.info("Successfully updated profile route in main.py")
                                break
                        else:
                            logger.error("Could not find the end of the profile route function")
                            return False
            else:
                logger.error(f"Could not find profile route in {main_path}")
                return False
        else:
            logger.error(f"Main routes file {main_path} not found")
            return False
        
        # 2. Optional: Check if the profile.html template exists
        template_path = os.path.join('app', 'templates', 'profile.html')
        if not os.path.exists(template_path):
            logger.warning(f"Profile template {template_path} does not exist! You need to create it.")
        else:
            logger.info(f"Profile template {template_path} exists, good!")
        
        logger.info("\nProfile route fix applied successfully!")
        logger.info("Remember to restart your Flask server to apply the changes.")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing profile route: {e}")
        logger.error(traceback.format_exc())
        return False

# New profile route implementation
PROFILE_ROUTE_IMPLEMENTATION = """@main.route('/profile')
@login_required
def profile():
    """Display user profile directly instead of redirecting"""
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
        return redirect(url_for('main.index'))"""

if __name__ == "__main__":
    print("Applying profile route fix...")
    success = fix_profile_route()
    sys.exit(0 if success else 1)
