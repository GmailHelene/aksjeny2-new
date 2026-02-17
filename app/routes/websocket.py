from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
import json
import time
from threading import Thread
import queue

websocket_bp = Blueprint('websocket', __name__)

# Store for active WebSocket connections
active_connections = {}
message_queues = {}

@websocket_bp.route('/ws/realtime')
def realtime_websocket():
    """WebSocket endpoint for real-time data"""
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        user_id = current_user.id if current_user.is_authenticated else 'anonymous'
        connection_id = f"{user_id}_{time.time()}"
        
        # Store connection
        active_connections[connection_id] = ws
        message_queues[connection_id] = queue.Queue()
        
        current_app.logger.info(f"WebSocket connected: {connection_id}")
        
        try:
            # Send initial connection message
            ws.send(json.dumps({
                'type': 'connection',
                'status': 'connected',
                'message': 'WebSocket connection established'
            }))
            
            # Handle incoming messages
            while True:
                message = ws.receive()
                if message is None:
                    break
                    
                try:
                    data = json.loads(message)
                    handle_websocket_message(ws, data, connection_id)
                except json.JSONDecodeError:
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                    
        except Exception as e:
            current_app.logger.error(f"WebSocket error: {str(e)}")
        finally:
            # Clean up connection
            if connection_id in active_connections:
                del active_connections[connection_id]
            if connection_id in message_queues:
                del message_queues[connection_id]
            current_app.logger.info(f"WebSocket disconnected: {connection_id}")
            
    return '', 204

def handle_websocket_message(ws, data, connection_id):
    """Handle incoming WebSocket messages"""
    msg_type = data.get('type')
    
    if msg_type == 'subscribe':
        tickers = data.get('tickers', [])
        # Here you would implement subscription logic
        ws.send(json.dumps({
            'type': 'subscribed',
            'tickers': tickers,
            'message': f'Subscribed to {len(tickers)} tickers'
        }))
        
    elif msg_type == 'unsubscribe':
        tickers = data.get('tickers', [])
        ws.send(json.dumps({
            'type': 'unsubscribed',
            'tickers': tickers
        }))
        
    elif msg_type == 'ping':
        ws.send(json.dumps({
            'type': 'pong',
            'timestamp': time.time()
        }))
        
    else:
        ws.send(json.dumps({
            'type': 'error',
            'message': f'Unknown message type: {msg_type}'
        }))

def broadcast_price_update(ticker, price_data):
    """Broadcast price updates to all connected clients"""
    message = json.dumps({
        'type': 'price_update',
        'ticker': ticker,
        'data': price_data,
        'timestamp': time.time()
    })
    
    for connection_id, ws in list(active_connections.items()):
        try:
            ws.send(message)
        except Exception as e:
            current_app.logger.error(f"Error broadcasting to {connection_id}: {str(e)}")
            # Remove dead connections
            if connection_id in active_connections:
                del active_connections[connection_id]

def attempt_reconnect(ws, connection_id):
    """Attempt to reconnect WebSocket"""
    max_attempts = 5
    for attempt in range(max_attempts):
        time.sleep(2 ** attempt)  # Exponential backoff
        try:
            ws.send(json.dumps({
                'type': 'reconnect',
                'message': 'Attempting to reconnect...'
            }))
            # Attempt to reconnect logic here
            break  # Exit loop if successful
        except Exception as e:
            current_app.logger.error(f"Reconnect attempt {attempt + 1} failed: {str(e)}")
    else:
        current_app.logger.error(f"Max reconnect attempts reached for {connection_id}")
