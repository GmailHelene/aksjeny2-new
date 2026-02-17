"""
Advanced Order Management System for CMC Markets-style MT4 functionality
Implements One-Cancels-Other (OCO), Stealth Orders, and Advanced Order Types
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid
import logging

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    OCO = "OCO"  # One-Cancels-Other
    STEALTH = "STEALTH"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class Order:
    """Advanced order with MT4-style features"""
    
    def __init__(self, symbol: str, side: OrderSide, order_type: OrderType, 
                 quantity: float, price: float = None, stop_price: float = None,
                 take_profit: float = None, stop_loss: float = None, 
                 trailing_amount: float = None, time_in_force: str = "GTC",
                 stealth_size: float = None, parent_order_id: str = None):
        
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trailing_amount = trailing_amount
        self.time_in_force = time_in_force
        self.stealth_size = stealth_size  # For stealth orders
        self.parent_order_id = parent_order_id  # For OCO orders
        
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0
        self.average_fill_price = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.fills = []
        
        # Trailing stop tracking
        self.highest_price = None  # For sell trailing stops
        self.lowest_price = None   # For buy trailing stops
        
        # Stealth order tracking
        self.stealth_revealed_quantity = 0.0
        
    def add_fill(self, quantity: float, price: float):
        """Add a fill to the order"""
        fill = {
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now()
        }
        self.fills.append(fill)
        
        # Update filled quantity and average price
        total_value = self.average_fill_price * self.filled_quantity + quantity * price
        self.filled_quantity += quantity
        self.average_fill_price = total_value / self.filled_quantity
        
        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
            
        self.updated_at = datetime.now()
        
    def cancel(self):
        """Cancel the order"""
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.CANCELLED
            self.updated_at = datetime.now()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'trailing_amount': self.trailing_amount,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'average_fill_price': self.average_fill_price,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'fills': self.fills,
            'stealth_size': self.stealth_size,
            'parent_order_id': self.parent_order_id
        }


class OCOOrder:
    """One-Cancels-Other Order Pair"""
    
    def __init__(self, primary_order: Order, secondary_order: Order):
        self.id = str(uuid.uuid4())
        self.primary_order = primary_order
        self.secondary_order = secondary_order
        self.status = "ACTIVE"
        self.created_at = datetime.now()
        
        # Link orders to this OCO
        primary_order.parent_order_id = self.id
        secondary_order.parent_order_id = self.id
        
    def check_execution(self, current_price: float):
        """Check if either order should be executed"""
        if self.status != "ACTIVE":
            return
            
        # Check if primary order is triggered
        if self._should_execute_order(self.primary_order, current_price):
            self.primary_order.add_fill(self.primary_order.quantity, current_price)
            self.secondary_order.cancel()
            self.status = "PRIMARY_EXECUTED"
            
        # Check if secondary order is triggered
        elif self._should_execute_order(self.secondary_order, current_price):
            self.secondary_order.add_fill(self.secondary_order.quantity, current_price)
            self.primary_order.cancel()
            self.status = "SECONDARY_EXECUTED"
            
    def _should_execute_order(self, order: Order, current_price: float) -> bool:
        """Check if order should be executed at current price"""
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                return current_price <= order.price
            else:  # SELL
                return current_price >= order.price
                
        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY:
                return current_price >= order.stop_price
            else:  # SELL
                return current_price <= order.stop_price
                
        return False


class AdvancedOrderManager:
    """Advanced order management system with MT4-style features"""
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.oco_orders: Dict[str, OCOOrder] = {}
        self.fills_history = []
        self.market_data = {}
        
    def create_market_order(self, symbol: str, side: OrderSide, quantity: float,
                          take_profit: float = None, stop_loss: float = None) -> Order:
        """Create a market order"""
        order = Order(symbol, side, OrderType.MARKET, quantity, 
                     take_profit=take_profit, stop_loss=stop_loss)
        self.orders[order.id] = order
        return order
        
    def create_limit_order(self, symbol: str, side: OrderSide, quantity: float, 
                          price: float, take_profit: float = None, 
                          stop_loss: float = None) -> Order:
        """Create a limit order"""
        order = Order(symbol, side, OrderType.LIMIT, quantity, price=price,
                     take_profit=take_profit, stop_loss=stop_loss)
        self.orders[order.id] = order
        return order
        
    def create_stop_order(self, symbol: str, side: OrderSide, quantity: float,
                         stop_price: float, take_profit: float = None,
                         stop_loss: float = None) -> Order:
        """Create a stop order"""
        order = Order(symbol, side, OrderType.STOP, quantity, stop_price=stop_price,
                     take_profit=take_profit, stop_loss=stop_loss)
        self.orders[order.id] = order
        return order
        
    def create_trailing_stop_order(self, symbol: str, side: OrderSide, quantity: float,
                                  trailing_amount: float, current_price: float) -> Order:
        """Create a trailing stop order"""
        order = Order(symbol, side, OrderType.TRAILING_STOP, quantity, 
                     trailing_amount=trailing_amount)
        
        # Initialize tracking prices
        if side == OrderSide.SELL:
            order.highest_price = current_price
            order.stop_price = current_price - trailing_amount
        else:  # BUY
            order.lowest_price = current_price
            order.stop_price = current_price + trailing_amount
            
        self.orders[order.id] = order
        return order
        
    def create_stealth_order(self, symbol: str, side: OrderSide, total_quantity: float,
                           stealth_size: float, price: float = None) -> Order:
        """Create a stealth order that reveals quantity gradually"""
        order_type = OrderType.MARKET if price is None else OrderType.STEALTH
        
        order = Order(symbol, side, order_type, total_quantity, price=price,
                     stealth_size=stealth_size)
        self.orders[order.id] = order
        return order
        
    def create_oco_order(self, symbol: str, side: OrderSide, quantity: float,
                        limit_price: float, stop_price: float) -> OCOOrder:
        """Create One-Cancels-Other order"""
        
        # Create limit order (take profit)
        limit_order = Order(symbol, side, OrderType.LIMIT, quantity, price=limit_price)
        
        # Create stop order (stop loss) 
        opposite_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
        stop_order = Order(symbol, opposite_side, OrderType.STOP, quantity, stop_price=stop_price)
        
        oco = OCOOrder(limit_order, stop_order)
        
        self.orders[limit_order.id] = limit_order
        self.orders[stop_order.id] = stop_order
        self.oco_orders[oco.id] = oco
        
        return oco
        
    def update_market_data(self, symbol: str, price: float, bid: float = None, ask: float = None):
        """Update market data and process orders"""
        self.market_data[symbol] = {
            'price': price,
            'bid': bid or price,
            'ask': ask or price,
            'timestamp': datetime.now()
        }
        
        # Process all orders for this symbol
        self._process_orders(symbol, price)
        
    def _process_orders(self, symbol: str, current_price: float):
        """Process all orders for a symbol at current price"""
        
        # Process OCO orders first
        for oco in self.oco_orders.values():
            if (oco.primary_order.symbol == symbol and 
                oco.status == "ACTIVE"):
                oco.check_execution(current_price)
                
        # Process individual orders
        for order in self.orders.values():
            if (order.symbol == symbol and 
                order.status == OrderStatus.PENDING):
                
                if order.order_type == OrderType.MARKET:
                    self._execute_market_order(order, current_price)
                    
                elif order.order_type == OrderType.LIMIT:
                    self._check_limit_order(order, current_price)
                    
                elif order.order_type == OrderType.STOP:
                    self._check_stop_order(order, current_price)
                    
                elif order.order_type == OrderType.TRAILING_STOP:
                    self._update_trailing_stop(order, current_price)
                    
                elif order.order_type == OrderType.STEALTH:
                    self._process_stealth_order(order, current_price)
                    
    def _execute_market_order(self, order: Order, current_price: float):
        """Execute market order immediately"""
        if order.stealth_size:
            # For stealth market orders, only execute stealth size
            quantity_to_fill = min(order.stealth_size, 
                                 order.quantity - order.filled_quantity)
        else:
            quantity_to_fill = order.quantity
            
        order.add_fill(quantity_to_fill, current_price)
        
    def _check_limit_order(self, order: Order, current_price: float):
        """Check if limit order should be executed"""
        should_execute = False
        
        if order.side == OrderSide.BUY:
            should_execute = current_price <= order.price
        else:  # SELL
            should_execute = current_price >= order.price
            
        if should_execute:
            quantity_to_fill = order.quantity - order.filled_quantity
            order.add_fill(quantity_to_fill, order.price)
            
    def _check_stop_order(self, order: Order, current_price: float):
        """Check if stop order should be triggered"""
        should_trigger = False
        
        if order.side == OrderSide.BUY:
            should_trigger = current_price >= order.stop_price
        else:  # SELL
            should_trigger = current_price <= order.stop_price
            
        if should_trigger:
            # Convert to market order
            order.order_type = OrderType.MARKET
            quantity_to_fill = order.quantity - order.filled_quantity
            order.add_fill(quantity_to_fill, current_price)
            
    def _update_trailing_stop(self, order: Order, current_price: float):
        """Update trailing stop order"""
        if order.side == OrderSide.SELL:
            # Update highest price and trailing stop
            if order.highest_price is None or current_price > order.highest_price:
                order.highest_price = current_price
                order.stop_price = current_price - order.trailing_amount
                
            # Check if stop should trigger
            if current_price <= order.stop_price:
                quantity_to_fill = order.quantity - order.filled_quantity
                order.add_fill(quantity_to_fill, current_price)
                
        else:  # BUY trailing stop
            # Update lowest price and trailing stop
            if order.lowest_price is None or current_price < order.lowest_price:
                order.lowest_price = current_price
                order.stop_price = current_price + order.trailing_amount
                
            # Check if stop should trigger
            if current_price >= order.stop_price:
                quantity_to_fill = order.quantity - order.filled_quantity
                order.add_fill(quantity_to_fill, current_price)
                
    def _process_stealth_order(self, order: Order, current_price: float):
        """Process stealth order - gradually reveal quantity"""
        remaining_quantity = order.quantity - order.filled_quantity
        
        if remaining_quantity <= 0:
            return
            
        # Calculate next stealth reveal
        reveal_quantity = min(order.stealth_size, remaining_quantity)
        
        # Check if price condition is met
        should_execute = False
        if order.side == OrderSide.BUY:
            should_execute = current_price <= order.price
        else:  # SELL
            should_execute = current_price >= order.price
            
        if should_execute:
            order.add_fill(reveal_quantity, order.price)
            order.stealth_revealed_quantity += reveal_quantity
            
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            order.cancel()
            
            # If this is part of an OCO, cancel the other order too
            if order.parent_order_id and order.parent_order_id in self.oco_orders:
                oco = self.oco_orders[order.parent_order_id]
                if oco.primary_order.id == order_id:
                    oco.secondary_order.cancel()
                else:
                    oco.primary_order.cancel()
                oco.status = "CANCELLED"
                
            return True
        return False
        
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
        
    def get_orders(self, symbol: str = None, status: OrderStatus = None) -> List[Order]:
        """Get orders with optional filters"""
        orders = list(self.orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
            
        if status:
            orders = [o for o in orders if o.status == status]
            
        return orders

    # Compatibility helper methods expected by professional_analytics
    def get_pending_orders(self) -> List[Order]:
        return [o for o in self.orders.values() if o.status == OrderStatus.PENDING]

    def get_active_positions(self) -> List[Any]:  # Position objects not implemented; return empty list
        return []
        
    def get_oco_orders(self) -> List[OCOOrder]:
        """Get all OCO orders"""
        return list(self.oco_orders.values())
        
    def calculate_position_size(self, account_balance: float, risk_percentage: float,
                              entry_price: float, stop_loss_price: float) -> Tuple[float, Dict[str, float]]:
        """Calculate position size based on risk management"""
        risk_amount = account_balance * (risk_percentage / 100)
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share == 0:
            return 0, {}
            
        position_size = risk_amount / risk_per_share
        
        calculation_details = {
            'account_balance': account_balance,
            'risk_percentage': risk_percentage,
            'risk_amount': risk_amount,
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'risk_per_share': risk_per_share,
            'position_size': position_size,
            'max_loss': position_size * risk_per_share
        }
        
        return position_size, calculation_details


# Global order manager instance
order_manager = AdvancedOrderManager()
# Alias for backward compatibility with modules expecting advanced_order_manager symbol
advanced_order_manager = order_manager
