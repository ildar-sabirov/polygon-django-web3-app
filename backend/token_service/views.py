import asyncio
import json
import time

from adrf.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from web3 import AsyncWeb3, AsyncHTTPProvider

from .utils import create_address_database, get_last_transaction_date

ABI_FILE_PATH = 'data/erc20.abi.json'
CONTRACT_ADDRESS = '0x1a9b54a3075119f1546c52ca0940551a6ce5d2d0'
N_DEFAULT = 10

web3 = AsyncWeb3(AsyncHTTPProvider('https://polygon-rpc.com'))


def load_abi_from_file(file_path):
    with open(file_path, 'r') as file:
        abi = json.load(file)
    return abi


try:
    erc20_abi = load_abi_from_file(ABI_FILE_PATH)
    contract_address = web3.to_checksum_address(CONTRACT_ADDRESS)
    contract = web3.eth.contract(address=contract_address, abi=erc20_abi)
except FileNotFoundError:
    print(f'Файл ABI не найден: {ABI_FILE_PATH}')
    raise


@api_view(['GET'])
async def get_balance_view(request):
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
        balance_wei = await contract.functions.balanceOf(address).call()
        balance_eth = web3.from_wei(balance_wei, 'ether')
        response_data = {'balance': str(balance_eth)}
        return Response(response_data)
    except Exception:
        return Response(
            {'error': 'Ошибка при получении баланса'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
async def get_balance_batch_view(request):
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
            balance_wei = await contract.functions.balanceOf(address).call()
            balance_eth = web3.from_wei(balance_wei, 'ether')
            balances.append(float(balance_eth))
        return Response({'balances': balances})
    except Exception:
        return Response(
            {'error': 'Ошибка при получении балансов'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
async def get_top_view(request):
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
        addresses = await create_address_database(CONTRACT_ADDRESS, web3)
        if not addresses:
            return Response(
                {'error': 'Не удалось получить адреса'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        semaphore = asyncio.Semaphore(2)

        async def get_balance(address):
            async with semaphore:
                address = web3.to_checksum_address(address)
                balance_wei = await contract.functions.balanceOf(
                    address
                ).call()
                balance_eth = web3.from_wei(balance_wei, 'ether')
                return address, float(balance_eth)

        tasks = [get_balance(address) for address in addresses]
        balances = await asyncio.gather(*tasks)
        end_time = time.time()

        execution_time = end_time - start_time

        print(f"Время выполнения: {execution_time} секунд")

        top_balances = sorted(balances, key=lambda x: x[1], reverse=True)[:n]
        return Response({'top_balances': top_balances})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
async def get_top_with_transactions_view(request):
    """
    Получает топ N адресов по балансам токена с информацией о
                                                датах последних транзакций.

    Parameters:
        request (HttpRequest): Запрос, содержащий параметр 'N' адресов в топе.

    Returns:
        Response: JSON-ответ с топ N адресов, их балансами и
                                                датами последних транзакций.
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
        addresses = await create_address_database(CONTRACT_ADDRESS, web3)
        if not addresses:
            return Response(
                {'error': 'Не удалось получить адреса'},
                status=status.HTTP_400_BAD_REQUEST
            )

        top_with_transactions = []
        for address in addresses:
            address = web3.to_checksum_address(address)
            balance_wei = contract.functions.balanceOf(address).call()
            balance_eth = web3.from_wei(balance_wei, 'ether')
            last_transaction_date = await get_last_transaction_date(address)
            top_with_transactions.append(
                (address, float(balance_eth), last_transaction_date)
            )

        top_with_transactions = sorted(
            top_with_transactions,
            key=lambda x: x[1],
            reverse=True
        )[:n]
        return Response({'top_with_transactions': top_with_transactions})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_token_info_view(request):
    """
    Получает информацию о токене по его адресу.

    Parameters:
        request (HttpRequest): Запрос, содержащий параметр 'address' с адресом.

    Returns:
        Response: JSON-ответ с информацией о токене.
    """
    token_address = request.GET.get('address', '')
    if not token_address:
        return Response(
            {'error': 'Адрес токена не указан'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        symbol = contract.functions.symbol().call()
        name = contract.functions.name().call()
        total_supply = contract.functions.totalSupply().call()

        token_info = {
            'symbol': symbol,
            'name': name,
            'totalSupply': total_supply
        }

        return Response(token_info)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
