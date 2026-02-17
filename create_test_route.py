#!/usr/bin/env python3
"""
Create a test route to debug favorites
"""

# Test API endpoint to debug favorites
test_favorites_route = '''
@main.route('/test-favorites')
def test_favorites():
    """Test route to debug favorites display"""
    try:
        from ..models.favorites import Favorites
        from ..models.user import User
        from ..extensions import db
        
        # Get all users
        all_users = User.query.all()
        users_info = [f"ID: {u.id}, Username: {u.username}" for u in all_users]
        
        # Get all favorites
        all_favorites = Favorites.query.all()
        favorites_info = [f"UserID: {f.user_id}, Symbol: {f.symbol}, Name: {f.name}" for f in all_favorites]
        
        # Test the profile logic for first user if exists
        test_result = "No users found"
        if all_users:
            test_user = all_users[0]
            user_favorites = Favorites.query.filter_by(user_id=test_user.id).all()
            
            user_favorites_list = []
            for fav in user_favorites:
                favorite_info = {
                    'symbol': fav.symbol,
                    'name': fav.name,
                    'exchange': fav.exchange,
                    'created_at': fav.created_at
                }
                user_favorites_list.append(favorite_info)
            
            has_favorites = user_favorites_list and len(user_favorites_list) > 0
            test_result = f"User {test_user.id} ({test_user.username}): {len(user_favorites_list)} favorites, Template condition: {has_favorites}"
        
        html = f"""
        <h2>Database Debug Info</h2>
        <h3>Users ({len(all_users)}):</h3>
        <ul>{"".join([f"<li>{u}</li>" for u in users_info])}</ul>
        
        <h3>Favorites ({len(all_favorites)}):</h3>
        <ul>{"".join([f"<li>{f}</li>" for f in favorites_info])}</ul>
        
        <h3>Profile Logic Test:</h3>
        <p>{test_result}</p>
        
        <p><a href="/profile">Go to Profile</a> | <a href="/admin/test-login/testuser">Test Login as testuser</a></p>
        """
        
        return html
        
    except Exception as e:
        return f"Error: {e}"
'''

print("Test route code created. Add this to main.py routes to debug favorites:")
print(test_favorites_route)
