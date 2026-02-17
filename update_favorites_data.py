
#!/usr/bin/env python3
# Update existing favorites with proper names and exchanges

from app import create_app
from app.extensions import db
from app.models.favorites import Favorites
from app.services.data_service import DataService

app = create_app()
with app.app_context():
    favorites = Favorites.query.all()
    updated_count = 0
    
    for fav in favorites:
        updated = False
        
        # Update name if empty
        if not fav.name or fav.name.strip() == '':
            try:
                stock_info = DataService.get_stock_info(fav.symbol)
                if stock_info and stock_info.get('name'):
                    fav.name = stock_info.get('name')
                    updated = True
                else:
                    fav.name = fav.symbol  # Fallback to symbol
                    updated = True
            except Exception:
                fav.name = fav.symbol
                updated = True
        
        # Update exchange if empty
        if not fav.exchange or fav.exchange.strip() == '':
            if fav.symbol.endswith('.OL'):
                fav.exchange = 'Oslo Børs'
                updated = True
            elif fav.symbol.endswith('.ST'):
                fav.exchange = 'Stockholm'
                updated = True
            elif fav.symbol.endswith('.CO'):
                fav.exchange = 'Copenhagen'
                updated = True
            elif '.' not in fav.symbol:
                fav.exchange = 'NASDAQ/NYSE'
                updated = True
            else:
                fav.exchange = 'Unknown'
                updated = True
        
        if updated:
            updated_count += 1
    
    if updated_count > 0:
        db.session.commit()
        print(f"Updated {updated_count} favorites with proper names and exchanges")
    else:
        print("No favorites needed updating")
