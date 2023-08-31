import json
import requests
from .gql_queries_v3 import  FETCH_V3_TOKEN_QUERY, FETCH_V3_PAIRS_FOR_TOKEN_QUERY, FETCH_V3_SWAP_TRANSACTIONS_QUERY, FETCH_V3_SWAP_TRANSACTIONS_FOR_TIMESTAMP_QUERY, FETCH_V3_SPECIFIC_PAIR #,  Assuming ql_queries contains v3 queries as well
from models.pair_v3 import PairV3
from models.token_v3 import TokenV3
from models.transaction_v3 import TransactionV3

class UniswapV3Client:

    def __init__(self, endpoint='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'):
        self.endpoint = endpoint

    def send_query(self, query, variables={}):
        payload = {'query': query, 'variables': variables}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.endpoint, json=payload, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Query failed with status code {response.status_code}")

        return json.loads(response.content.decode())

    def fetch_token(self, token_id):
        response = self.send_query(FETCH_V3_TOKEN_QUERY, {'id': token_id})
        token_data = response.get('data', {}).get('token', {})
        
        if token_data:
            return TokenV3.from_json(token_data)
        return None

    def fetch_pairs_for_token(self, token_id):
        response = self.send_query(FETCH_V3_PAIRS_FOR_TOKEN_QUERY, {'id': token_id})
        pairs_data = response.get('data', {}).get('pairs', [])
        
        pairs = []
        for pair_data in pairs_data:
            pairs.append(PairV3.from_json(pair_data))
        
        return pairs
    
    def fetch_swap_transactions(self, pair_id, first=10, order_by="timestamp", order_direction="desc"):
        variables = {
            'pairId': pair_id,
            'first': first,
            'orderBy': order_by,
            'orderDirection': order_direction
        }
        response = self.send_query(FETCH_V3_SWAP_TRANSACTIONS_QUERY, variables)
        swaps_data = response.get('data', {}).get('swaps', [])
        
        transactions = []
        for swap_data in swaps_data:
            transactions.append(TransactionV3.from_json(swap_data))
        
        return transactions

    def fetch_swaps_for_pair_at_timestamp(self, pair_id, target_timestamp, time_range=600000):
        start_time = target_timestamp - time_range
        end_time = target_timestamp + time_range

        variables = {
            'pair_id': pair_id,
            'start_time': start_time,
            'end_time': end_time
        }

        response = self.send_query(FETCH_V3_SWAP_TRANSACTIONS_FOR_TIMESTAMP_QUERY, variables)
        return response.get('data', {}).get('swaps', [])
    
    def fetch_specific_pair(self, token0_id, token1_id):
        token0_id = token0_id.lower()
        token1_id = token1_id.lower()
        variables = {'token0_id': token0_id, 'token1_id': token1_id}
        
        response = self.send_query(FETCH_V3_SPECIFIC_PAIR, variables)
        pairs_data = response.get('data', {})

        pair0_data = pairs_data.get('pool0', [])
        pair1_data = pairs_data.get('pool1', [])
        
        if pair0_data and pair1_data:
            volume0 = max(float(x.get('volumeUSD', 0)) for x in pair0_data)
            volume1 = max(float(x.get('volumeUSD', 0)) for x in pair1_data)

            # Choose the pair with the higher volumeUSD
            return PairV3.from_json(pair0_data[0]) if volume0 > volume1 else PairV3.from_json(pair1_data[0])
        elif pair0_data:
            # Choose the pair with the maximum volumeUSD in pool0
            max_volume_pair_data = max(pair0_data, key=lambda x: float(x.get('volumeUSD', 0)))
            return PairV3.from_json(max_volume_pair_data)
        elif pair1_data:
            # Choose the pair with the maximum volumeUSD in pool1
            max_volume_pair_data = max(pair1_data, key=lambda x: float(x.get('volumeUSD', 0)))
            return PairV3.from_json(max_volume_pair_data)
        else:
            return None  # No pools available
