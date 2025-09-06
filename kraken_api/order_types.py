from enum import Enum
from typing import Dict, Any

class OrderType(Enum):
    LIMIT = 'lmt'
    MARKET = 'mkt'
    STOP_LIMIT = 'stp'
    TAKE_PROFIT = 'take_profit'
    STOP_LOSS = 'stop_loss'
    POST_ONLY = 'post'

class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'

def create_limit_order(symbol: str, side: str, size: float, price: float, 
                      reduce_only: bool = False, post_only: bool = False) -> Dict[str, Any]:
    """
    Create a limit order parameters dictionary
    
    Args:
        symbol: Trading symbol
        side: 'buy' or 'sell'
        size: Order size
        price: Limit price
        reduce_only: Whether order is reduce-only
        post_only: Whether order is post-only
    """
    order = {
        'orderType': 'lmt',
        'symbol': symbol,
        'side': side,
        'size': size,
        'limitPrice': price
    }
    
    if reduce_only:
        order['reduceOnly'] = True
    
    if post_only:
        order['postOnly'] = True
    
    return order

def create_market_order(symbol: str, side: str, size: float) -> Dict[str, Any]:
    """
    Create a market order parameters dictionary
    """
    return {
        'orderType': 'mkt',
        'symbol': symbol,
        'side': side,
        'size': size
    }

def create_stop_order(symbol: str, side: str, size: float, stop_price: float, 
                     limit_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Create a stop order parameters dictionary
    """
    order = {
        'orderType': 'stp' if limit_price else 'mkt',
        'symbol': symbol,
        'side': side,
        'size': size,
        'stopPrice': stop_price
    }
    
    if limit_price:
        order['limitPrice'] = limit_price
    
    return order
