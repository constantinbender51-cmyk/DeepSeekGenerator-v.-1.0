import base64
import hashlib
import hmac
import time
import requests
from typing import Dict, Optional, Any, List
from urllib.parse import urlencode

class KrakenFuturesApi:
    """
    Kraken Futures API client for Python
    
    Args:
        api_key (str): Your Kraken Futures API key
        api_secret (str): Your Kraken Futures API secret
        base_url (str): The base URL for the API (default: 'https://futures.kraken.com')
    """
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = 'https://futures.kraken.com'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.nonce_counter = 0
    
    def create_nonce(self) -> str:
        """Creates a unique nonce for each request"""
        if self.nonce_counter > 9999:
            self.nonce_counter = 0
        # Pad with leading zeros to 5 digits
        counter_str = str(self.nonce_counter).zfill(5)
        self.nonce_counter += 1
        return str(int(time.time() * 1000)) + counter_str
    
    def sign_request(self, endpoint: str, nonce: str, post_data: str = '') -> str:
        """
        Signs the request data to create the 'Authent' header
        
        Args:
            endpoint (str): The API endpoint path
            nonce (str): The unique nonce for this request
            post_data (str): URL-encoded string of parameters for POST requests
            
        Returns:
            str: Base64-encoded signature
        """
        # Remove '/derivatives' prefix if present
        path = endpoint[len('/derivatives'):] if endpoint.startswith('/derivatives') else endpoint
        
        # Create the message to sign
        message = post_data + nonce + path
        
        # SHA-256 hash of the message
        hash_digest = hashlib.sha256(message.encode('utf-8')).digest()
        
        # Decode the base64 secret
        secret_decoded = base64.b64decode(self.api_secret)
        
        # Create HMAC-SHA512 signature
        hmac_digest = hmac.new(secret_decoded, hash_digest, hashlib.sha512).digest()
        
        # Base64 encode the signature
        return base64.b64encode(hmac_digest).decode('utf-8')
    
    def request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Makes an API request
        
        Args:
            method (str): HTTP method ('GET' or 'POST')
            endpoint (str): API endpoint path
            params (dict): Request parameters
            
        Returns:
            dict: API response data
            
        Raises:
            Exception: If the API request fails
        """
        if params is None:
            params = {}
        
        url = self.base_url + endpoint
        nonce = self.create_nonce()
        post_data = ''
        
        headers = {
            'APIKey': self.api_key,
            'Nonce': nonce,
            'User-Agent': 'Kraken-Futures-Python-Client/1.0'
        }
        
        if method.upper() == 'POST':
            post_data = urlencode(params)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        # Sign the request
        headers['Authent'] = self.sign_request(endpoint, nonce, post_data)
        
        # Prepare request
        request_kwargs = {
            'method': method.upper(),
            'url': url,
            'headers': headers,
            'timeout': 30
        }
        
        if method.upper() == 'POST':
            request_kwargs['data'] = post_data
        elif params:
            # For GET requests, add params to URL
            request_kwargs['url'] += '?' + urlencode(params)
        
        try:
            response = requests.request(**request_kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = e.response.json() if e.response else str(e)
            print(f"Error with {method} {endpoint}: {error_message}")
            raise Exception(f"API request failed: {error_message}")
    
    # ######################
    # ### Public Methods ###
    # ######################
    
    def get_instruments(self) -> Dict:
        """Returns all instruments with their specifications"""
        return self.request('GET', '/derivatives/api/v3/instruments')
    
    def get_tickers(self) -> Dict:
        """Returns market data for all instruments"""
        return self.request('GET', '/derivatives/api/v3/tickers')
    
    def get_orderbook(self, symbol: str) -> Dict:
        """
        Returns the entire order book for a given symbol
        
        Args:
            symbol (str): Trading symbol (e.g., 'pi_xbtusd')
        """
        return self.request('GET', '/derivatives/api/v3/orderbook', {'symbol': symbol})
    
    def get_history(self, symbol: str, last_time: Optional[str] = None) -> Dict:
        """
        Returns historical data for a given symbol
        
        Args:
            symbol (str): Trading symbol
            last_time (str): Optional timestamp for pagination
        """
        params = {'symbol': symbol}
        if last_time:
            params['lastTime'] = last_time
        return self.request('GET', '/derivatives/api/v3/history', params)
    
    # #######################
    # ### Private Methods ###
    # #######################
    
    def get_accounts(self) -> Dict:
        """Returns key account information"""
        return self.request('GET', '/derivatives/api/v3/accounts')
    
    def send_order(self, order_params: Dict) -> Dict:
        """
        Places a new order
        
        Args:
            order_params (dict): Order parameters including:
                - orderType (str): 'lmt', 'mkt', 'post', etc.
                - symbol (str): Trading symbol
                - side (str): 'buy' or 'sell'
                - size (float): Order size
                - limitPrice (float): Limit price (for limit orders)
                - stopPrice (float): Stop price (for stop orders)
        """
        return self.request('POST', '/derivatives/api/v3/sendorder', order_params)
    
    def edit_order(self, edit_params: Dict) -> Dict:
        """
        Edits an existing order
        
        Args:
            edit_params (dict): Edit parameters including:
                - order_id (str): Order ID to edit
                - limitPrice (float): New limit price
                - size (float): New order size
        """
        return self.request('POST', '/derivatives/api/v3/editorder', edit_params)
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancels an existing order
        
        Args:
            order_id (str): Order ID to cancel
        """
        return self.request('POST', '/derivatives/api/v3/cancelorder', {'order_id': order_id})
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> Dict:
        """
        Cancels all orders, optionally for a specific symbol
        
        Args:
            symbol (str): Optional symbol to cancel orders for
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self.request('POST', '/derivatives/api/v3/cancelallorders', params)
    
    def cancel_all_orders_after(self, timeout: int) -> Dict:
        """
        Cancels all orders after a specified timeout
        
        Args:
            timeout (int): Timeout in seconds
        """
        return self.request('POST', '/derivatives/api/v3/cancelallordersafter', {'timeout': timeout})
    
    def batch_order(self, commands: List[Dict]) -> Dict:
        """
        Sends a batch of order commands (send, cancel, edit)
        
        Args:
            commands (list): List of order commands
        """
        return self.request('POST', '/derivatives/api/v3/batchorder', {'batchOrder': commands})
    
    def get_open_orders(self) -> Dict:
        """Returns all open orders"""
        return self.request('GET', '/derivatives/api/v3/openorders')
    
    def get_open_positions(self) -> Dict:
        """Returns all open positions"""
        return self.request('GET', '/derivatives/api/v3/openpositions')
    
    def get_recent_orders(self, symbol: Optional[str] = None) -> Dict:
        """
        Returns recent orders, optionally for a specific symbol
        
        Args:
            symbol (str): Optional symbol filter
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self.request('GET', '/derivatives/api/v3/recentorders', params)
    
    def get_fills(self, symbol: Optional[str] = None, last_fill_time: Optional[str] = None) -> Dict:
        """
        Returns filled orders (executions)
        
        Args:
            symbol (str): Optional symbol filter
            last_fill_time (str): Optional timestamp for pagination
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        if last_fill_time:
            params['lastFillTime'] = last_fill_time
        return self.request('GET', '/derivatives/api/v3/fills', params)
    
    def get_account_log(self) -> Dict:
        """Returns account activity log"""
        return self.request('GET', '/api/history/v2/account-log')
    
    def get_transfers(self, last_transfer_time: Optional[str] = None) -> Dict:
        """
        Returns wallet transfer history
        
        Args:
            last_transfer_time (str): Optional timestamp for pagination
        """
        params = {}
        if last_transfer_time:
            params['lastTransferTime'] = last_transfer_time
        return self.request('GET', '/derivatives/api/v3/transfers', params)
    
    def get_notifications(self) -> Dict:
        """Returns system notifications"""
        return self.request('GET', '/derivatives/api/v3/notifications')
