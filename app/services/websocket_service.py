"""
WebSocket service for real-time push notifications
"""
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
import json
from datetime import datetime
import threading
import time
import logging

logger = logging.getLogger(__name__)

# Global SocketIO instance
socketio = None

class WebSocketService:
    """WebSocket service for real-time communications"""
    
    def __init__(self, app=None):
        self.app = app
        self.active_connections = {}
        self.market_rooms = {
            'oslo': set(),
            'global': set(),
            'crypto': set(),
            'currency': set()
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize WebSocket service with Flask app (non-blocking)"""
        try:
            # Only initialize if WebSocket support is explicitly enabled
            if not app.config.get('ENABLE_WEBSOCKETS', False):
                app.logger.info('WebSocket service disabled - skipping initialization')
                return
                
            from flask_socketio import SocketIO
            global socketio
            socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
            self.socketio = socketio
            
            # Register event handlers
            self.register_handlers()
            
            # Start background tasks in a separate thread to avoid blocking startup
            import threading
            def start_background_tasks_delayed():
                try:
                    self.start_background_tasks()
                    app.logger.info('WebSocket background tasks started')
                except Exception as e:
                    app.logger.error(f'Failed to start WebSocket background tasks: {e}')
            
            thread = threading.Thread(target=start_background_tasks_delayed)
            thread.daemon = True
            thread.start()
            
            app.logger.info('WebSocket service initialized successfully')
            
        except ImportError:
            app.logger.warning('Flask-SocketIO not available - WebSocket features disabled')
        except Exception as e:
            app.logger.error(f'Failed to initialize WebSocket service: {e}')
            # Don't raise - allow app to continue without WebSockets
    
    def register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            user_id = current_user.id if current_user.is_authenticated else 'anonymous'
            logger.info(f"Client connected: {user_id}")
            
            # Send welcome message
            emit('status', {
                'message': 'Connected to Aksjeradar real-time service',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            user_id = current_user.id if current_user.is_authenticated else 'anonymous'
            logger.info(f"Client disconnected: {user_id}")
            
            # Clean up user from all rooms
            for market, users in self.market_rooms.items():
                users.discard(user_id)
        
        @self.socketio.on('join_market')
        def handle_join_market(data):
            """Handle client joining market room"""
            market = data.get('market', 'oslo')
            user_id = current_user.id if current_user.is_authenticated else 'anonymous'
            
            if market in self.market_rooms:
                join_room(f'market_{market}')
                self.market_rooms[market].add(user_id)
                
                emit('joined_market', {
                    'market': market,
                    'message': f'Joined {market} market updates',
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"User {user_id} joined market room: {market}")
        
        @self.socketio.on('leave_market')
        def handle_leave_market(data):
            """Handle client leaving market room"""
            market = data.get('market', 'oslo')
            user_id = current_user.id if current_user.is_authenticated else 'anonymous'
            
            if market in self.market_rooms:
                leave_room(f'market_{market}')
                self.market_rooms[market].discard(user_id)
                
                emit('left_market', {
                    'market': market,
                    'message': f'Left {market} market updates',
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"User {user_id} left market room: {market}")
        
        @self.socketio.on('subscribe_ticker')
        def handle_subscribe_ticker(data):
            """Handle ticker subscription"""
            ticker = data.get('ticker')
            category = data.get('category', 'oslo')
            
            if ticker:
                room_name = f'ticker_{category}_{ticker}'
                join_room(room_name)
                
                emit('subscribed_ticker', {
                    'ticker': ticker,
                    'category': category,
                    'message': f'Subscribed to {ticker} updates',
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"Client subscribed to ticker: {ticker} ({category})")
    
    def broadcast_market_update(self, market, data):
        """Broadcast market update to all clients in market room"""
        if not self.socketio:
            return
            
        room_name = f'market_{market}'
        self.socketio.emit('market_update', {
            'market': market,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }, room=room_name)
        
        logger.debug(f"Broadcasted market update for {market}")
    
    def broadcast_ticker_update(self, ticker, category, data):
        """Broadcast ticker update to subscribed clients"""
        if not self.socketio:
            return
            
        room_name = f'ticker_{category}_{ticker}'
        self.socketio.emit('ticker_update', {
            'ticker': ticker,
            'category': category,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }, room=room_name)
        
        logger.debug(f"Broadcasted ticker update for {ticker}")
    
    def broadcast_news_update(self, news_data):
        """Broadcast news update to all connected clients"""
        if not self.socketio:
            return
            
        self.socketio.emit('news_update', {
            'data': news_data,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.debug("Broadcasted news update")
    
    def broadcast_alert(self, alert_data, user_id=None):
        """Broadcast alert to specific user or all users"""
        if not self.socketio:
            return
            
        if user_id:
            # Send to specific user (requires session tracking)
            self.socketio.emit('price_alert', {
                'data': alert_data,
                'timestamp': datetime.now().isoformat()
            }, room=f'user_{user_id}')
        else:
            # Broadcast to all
            self.socketio.emit('general_alert', {
                'data': alert_data,
                'timestamp': datetime.now().isoformat()
            })
        
        logger.info(f"Broadcasted alert to {'user ' + str(user_id) if user_id else 'all users'}")
    
    def start_background_tasks(self):
        """Start background tasks for real-time updates"""
        def market_data_updater():
            """Background task to send periodic market updates"""
            while True:
                try:
                    from ..services.realtime_data_service import real_time_service
                    
                    # Get market summary data
                    market_data = real_time_service.get_market_summary()
                    
                    if market_data:
                        # Broadcast to each market room
                        for market, data in market_data.items():
                            if market != 'last_updated' and data.get('status') == 'active':
                                self.broadcast_market_update(market, data)
                    
                    time.sleep(30)  # Update every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in market data updater: {e}")
                    time.sleep(60)  # Wait longer on error
        
        def news_updater():
            """Background task to send news updates"""
            while True:
                try:
                    # Simulate news updates (replace with actual news service)
                    news_data = {
                        'headline': 'Markedsoppdatering',
                        'summary': 'Automatisk oppdatering av markedsdata',
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Aksjeradar'
                    }
                    
                    self.broadcast_news_update(news_data)
                    time.sleep(300)  # Update every 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error in news updater: {e}")
                    time.sleep(300)
        
        # Start background threads
        market_thread = threading.Thread(target=market_data_updater, daemon=True)
        news_thread = threading.Thread(target=news_updater, daemon=True)
        
        market_thread.start()
        news_thread.start()
        
        logger.info("Started WebSocket background tasks")

# Global instance
websocket_service = WebSocketService()

def init_websocket(app):
    """Initialize WebSocket service with app"""
    websocket_service.init_app(app)
    return websocket_service
