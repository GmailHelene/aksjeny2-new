#!/usr/bin/env python3

from app import create_app
from app.models import Favorites, User
from app.extensions import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_favorites_table():
    app = create_app()
    
    with app.app_context():
        logger.info("Creating favorites table...")
        
        # Create only the favorites table
        try:
            db.create_all()
            logger.info("✅ Favorites table created successfully!")
            
            # Add some test favorites for our test user
            user = User.query.filter_by(username='testuser').first()
            if user:
                # Check if favorites already exist
                existing_favorites = Favorites.query.filter_by(user_id=user.id).count()
                if existing_favorites == 0:
                    favorites_data = [
                        ('AAPL', 'Apple Inc.', 'NASDAQ'),
                        ('TSLA', 'Tesla Inc.', 'NASDAQ'),
                        ('GOOGL', 'Alphabet Inc.', 'NASDAQ')
                    ]
                    
                    for symbol, name, exchange in favorites_data:
                        favorite = Favorites(
                            user_id=user.id,
                            symbol=symbol,
                            name=name,
                            exchange=exchange
                        )
                        db.session.add(favorite)
                    
                    db.session.commit()
                    logger.info(f"✅ Added {len(favorites_data)} test favorites for user {user.username}")
                else:
                    logger.info(f"User {user.username} already has {existing_favorites} favorites")
            else:
                logger.warning("Test user not found!")
                
        except Exception as e:
            logger.error(f"❌ Error creating favorites table: {e}")
            db.session.rollback()

if __name__ == "__main__":
    create_favorites_table()
