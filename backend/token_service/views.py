import json

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from web3 import Web3

from .utils import create_address_database

ABI_FILE_PATH = 'data/erc20.abi.json'
CONTRACT_ADDRESS = '0x1a9b54a3075119f1546c52ca0940551a6ce5d2d0'
N_DEFAULT = 10

web3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))


def load_abi_from_file(file_path):
    with open(file_path, 'r') as file:
        abi = json.load(file)
    return abi


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


@api_view(['POST'])
def get_balance_batch_view(request):
    """
    Получает балансы нескольких адресов.

    Parameters:
        request (HttpRequest): POST-запрос, содержащий список адресов.

    Returns:
        Response: JSON-ответ с балансами.
    """
    addresses = request.data.get('addresses', [])
    if not addresses:
        return Response(
            {'error': 'Список адресов пуст'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        balances = []
        for address in addresses:
            balance_wei = contract.functions.balanceOf(address).call()
            balance_eth = web3.fromWei(balance_wei, 'ether')
            balances.append(float(balance_eth))
        return Response({'balances': balances})
    except Exception as e:
        return Response(
            {'error': 'Ошибка при получении балансов'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def get_top_view(request):
    """
    Получает топ N адресов по балансам токена.

    Parameters:
        request (HttpRequest): Запрос, содержащий параметр 'N' адресов в топе.

    Returns:
        Response: JSON-ответ с топ N адресов и их балансами.
    """
    n = request.GET.get('N', N_DEFAULT)
    try:
        n = int(n)
    except ValueError:
        return Response(
            {'error': 'Неверное значение параметра N'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        addresses = create_address_database(CONTRACT_ADDRESS)
        if not addresses:
            return Response(
                {'error': 'Не удалось получить адреса'},
                status=status.HTTP_400_BAD_REQUEST
            )

        balances = []
        for address in addresses:
            address = web3.toChecksumAddress(address)
            balance_wei = contract.functions.balanceOf(address).call()
            balance_eth = web3.fromWei(balance_wei, 'ether')
            balances.append((address, float(balance_eth)))

        top_balances = sorted(balances, key=lambda x: x[1], reverse=True)[:n]
        return Response({'top_balances': top_balances})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
