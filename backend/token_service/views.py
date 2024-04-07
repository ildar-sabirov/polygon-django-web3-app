import json

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from web3 import Web3

ABI_FILE_PATH = 'data/erc20.abi.json'
CONTRACT_ADDRESS = '0x1a9b54a3075119f1546c52ca0940551a6ce5d2d0'

# Подключение к RPC-узлу Polygon
web3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))


# Загрузка ABI из файла
def load_abi_from_file(file_path):
    with open(file_path, 'r') as file:
        abi = json.load(file)
    return abi


# Инициализация контракта
try:
    erc20_abi = load_abi_from_file(ABI_FILE_PATH)
    contract_address = web3.toChecksumAddress(CONTRACT_ADDRESS)
    contract = web3.eth.contract(address=contract_address, abi=erc20_abi)
except FileNotFoundError:
    print(f'Файл ABI не найден: {ABI_FILE_PATH}')
    raise


@api_view(['GET'])
def get_balance_view(request):
    """
    Получает баланс выбранного адреса.

    Parameters:
        request (HttpRequest): Запрос, содержащий параметр 'address' с адресом.

    Returns:
        Response: JSON-ответ с балансом в виде строки.
    """
    address = request.GET.get('address', '')
    if not address:
        return Response(
            {'error': 'Адрес не указан'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        balance_wei = contract.functions.balanceOf(address).call()
        balance_eth = web3.fromWei(balance_wei, 'ether')
        response_data = {'balance': str(balance_eth)}
        return Response(response_data)
    except Exception as e:
        return Response(
            {'error': 'Ошибка при получении баланса'},
            status=status.HTTP_400_BAD_REQUEST
        )
