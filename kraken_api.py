import hashlib
import hmac
import time
import requests
from urllib.parse import urlencode

class KrakenFuturesApi:
    """
    Kraken Futures API client for Python
    """
    
    def __init__(self, api_key, api_secret, base_url='https://futures.kraken.com'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.nonce_counter = 0
    
    def create_nonce(self):
        """Creates a unique nonce for each request."""
        if self.nonce_counter > 9999:
            self.nonce_counter = 0
        counter_str = str(self.nonce_counter).zfill(5)
        self.nonce_counter += 1
        return str(int(time.time() * 1000)) + counter_str
    
    def sign_request(self, endpoint, nonce, post_data=''):
        """Signs the request data to create the 'Authent' header."""
        path = endpoint[len('/derivatives'):] if endpoint.startswith('/derivatives') else endpoint
        message = post_data + nonce + path
        hash_digest = hashlib.sha256(message.encode()).digest()
        secret_decoded = bytes.fromhex(self.api_secret) if len(self.api_secret) == 128 else self.api_secret.encode()
        hmac_digest = hmac.new(secret_decoded, hash_digest, hashlib.sha512).digest()
        return hmac_digest.hex()
    
    def request(self, method, endpoint, params=None):
        """Makes an API request."""
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
        
        headers['Authent'] = self.sign_request(endpoint, nonce, post_data)
        
        try:
            if method.upper() == 'GET':
                if params:
                    url += '?' + urlencode(params)
                response = requests.get(url, headers=headers)
            else:  # POST
                response = requests.post(url, headers=headers, data=post_data)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as error:
            error_message = error.response.json() if error.response else str(error)
            print(f"Error with {method} {endpoint}: {error_message}")
            raise
    
    # Public Methods
    def get_instruments(self):
        return self.request('GET', '/derivatives/api/v3/instruments')
    
    def get_tickers(self):
        return self.request('GET', '/derivatives/api/v3/tickers')
    
    def get_orderbook(self, params):
        return self.request('GET', '/derivatives/api/v3/orderbook', params)
    
    def get_history(self, params):
        return self.request('GET', '/derivatives/api/v3/history', params)
    
    # Private Methods
    def get_accounts(self):
        return self.request('GET', '/derivatives/api/v3/accounts')
    
    def send_order(self, params):
        return self.request('POST', '/derivatives/api/v3/sendorder', params)
    
    def edit_order(self, params):
        return self.request('POST', '/derivatives/api/v3/editorder', params)
    
    def cancel_order(self, params):
        return self.request('POST', '/derivatives/api/v3/cancelorder', params)
    
    def cancel_all_orders(self, params=None):
        return self.request('POST', '/derivatives/api/v3/cancelallorders', params or {})
    
    def cancel_all_orders_after(self, params):
        return self.request('POST', '/derivatives/api/v3/cancelallordersafter', params)
    
    def batch_order(self, params):
        return self.request('POST', '/derivatives/api/v3/batchorder', params)
    
    def get_open_orders(self):
        return self.request('GET', '/derivatives/api/v3/openorders')
    
    def get_open_positions(self):
        return self.request('GET', '/derivatives/api/v3/openpositions')
    
    def get_recent_orders(self, params=None):
        return self.request('GET', '/derivatives/api/v3/recentorders', params or {})
    
    def get_fills(self, params=None):
        return self.request('GET', '/derivatives/api/v3/fills', params or {})
    
    def get_account_log(self):
        return self.request('GET', '/api/history/v2/account-log')
    
    def get_transfers(self, params=None):
        return self.request('GET', '/derivatives/api/v3/transfers', params or {})
    
    def get_notifications(self):
        return self.request('GET', '/derivatives/api/v3/notifications')
