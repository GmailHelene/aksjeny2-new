"""
Initialize user stats for existing users
"""
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.user_stats import UserStats

def init_user_stats():
    """Create user stats entries for all existing users"""
    app = create_app()
    
    with app.app_context():
        # Get all users
        users = User.query.all()
        stats_created = 0
        
        for user in users:
            # Check if user already has stats
            existing_stats = UserStats.query.filter_by(user_id=user.id).first()
            
            if not existing_stats:
                # Create new stats entry
                stats = UserStats(user_id=user.id)
                
                # Set verified email based on user's email_verified status
                if hasattr(user, 'email_verified'):
                    stats.verified_email = user.email_verified
                
                # Set completed profile if user has first and last name
                if (hasattr(user, 'first_name') and hasattr(user, 'last_name') and 
                    user.first_name and user.last_name):
                    stats.completed_profile = True
                
                # Set portfolio stats if user has portfolios
                if hasattr(user, 'portfolios'):
                    portfolio_count = user.portfolios.count()
                    stats.portfolios_created = portfolio_count
                    if portfolio_count > 0:
                        stats.added_first_stock = True
                
                # Set watchlist stats if user has watchlists
                if hasattr(user, 'watchlists'):
                    stats.watchlists_created = user.watchlists.count()
                
                # Set alert stats if user has price alerts
                if hasattr(user, 'alerts'):
                    alert_count = user.alerts.count()
                    stats.alerts_created = alert_count
                    if alert_count > 0:
                        stats.created_first_alert = True
                        stats.used_alerts = True
                
                db.session.add(stats)
                stats_created += 1
                
                # Commit every 100 users to avoid memory issues
                if stats_created % 100 == 0:
                    db.session.commit()
        
        # Final commit for remaining users
        db.session.commit()
        
        print(f"✅ Created {stats_created} user stats entries")
        print(f"   Total users: {len(users)}")

if __name__ == '__main__':
    init_user_stats()
