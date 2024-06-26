import time
import random
from concurrent.futures import ThreadPoolExecutor
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from solana.keypair import Keypair
from solana.rpc.types import TxOpts
import base58
import config

# Функция для создания клиента с заданным RPC URL
def create_client(rpc_url):
    return Client(rpc_url)

# Функция для отправки транзакции самому себе
def send_transaction_to_self(client, from_keypair, to_pubkey, lamports):
    try:
        # Создание инструкции для перевода лампортов
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=from_keypair.public_key,
                to_pubkey=to_pubkey,
                lamports=lamports
            )
        )

        # Создание транзакции и добавление инструкции
        transaction = Transaction().add(transfer_instruction)

        # Подписание и отправка транзакции
        response = client.send_transaction(
            transaction,
            from_keypair,
            opts=TxOpts(skip_preflight=True)
        )
        print(f"Transaction sent from {from_keypair.public_key} with amount {lamports} lamports")
        return response
    except Exception as e:
        print(f"Error sending transaction from {from_keypair.public_key}: {e}")

# Функция для загрузки ключей из файла
def load_keypairs_from_file(file_path):
    keypairs = []
    with open(file_path, 'r') as file:
        for line in file:
            private_key = base58.b58decode(line.strip())
            keypairs.append(Keypair.from_secret_key(private_key))
    return keypairs

# Функция для выполнения транзакций с одного кошелька
def perform_transactions(client, sender_keypair):
    for _ in range(config.NUM_REPETITIONS):
        receiver_pubkey = sender_keypair.public_key  # Отправка самому себе
        lamports_to_send = random.randint(config.MIN_LAMPORTS, config.MAX_LAMPORTS)  # Рандомизация суммы
        response = send_transaction_to_self(client, sender_keypair, receiver_pubkey, lamports_to_send)
        delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)  # Рандомизация задержки
        time.sleep(delay)

# Пример использования
if __name__ == "__main__":
    # Создайте клиента
    client = create_client(config.RPC_URL)

    # Загрузите ключи отправителя из файла
    keypairs = load_keypairs_from_file('wallets.txt')

    # Перемешайте список кошельков, если это указано в конфигурации
    if config.SHUFFLE_WALLETS:
        random.shuffle(keypairs)

    # Используйте ThreadPoolExecutor для параллельного выполнения транзакций с нескольких кошельков
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(perform_transactions, client, keypair) for keypair in keypairs]
        for future in futures:
            future.result()
