import os
import requests

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

POLIGONSCAN_API_KEY = os.getenv('API_KEY')

web3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))


def get_transactions(contract_address, start_block, end_block):
    url = (f'https://api.polygonscan.com/api'
           f'?module=account'
           f'&action=txlist'
           f'&address={contract_address}'
           f'&startblock={start_block}'
           f'&endblock={end_block}'
           f'&sort=asc'
           f'&apikey={POLIGONSCAN_API_KEY}')
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        transactions = data.get('result', [])
        return transactions
    else:
        print('Error:', response.text)
        return []


def create_address_database(contract_address):
    try:
        start_block = 0
        end_block = web3.eth.blockNumber

        transactions = get_transactions(
            contract_address,
            start_block,
            end_block
        )

        if transactions:
            addresses = set()
            for tx in transactions:
                from_address = tx['from']
                to_address = tx['to']
                if from_address:
                    addresses.add(from_address)
                if to_address:
                    addresses.add(to_address)

            address_list = list(addresses)
            return address_list
        else:
            print('No transactions found.')
            return []
    except Exception as e:
        print(f'Error: {e}')
        return []
