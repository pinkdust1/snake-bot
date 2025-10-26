# create_xrp_wallet.py
# pip install xrpl requests

import json
import time
import requests
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient

# ========== Настройки ==========
# RPC: для тестов используем testnet; для mainnet подставь "https://s1.ripple.com:51234/"
JSON_RPC_URL = "https://s1.ripple.com:51234"  # testnet
client = JsonRpcClient(JSON_RPC_URL)

# Если True — попытаемся профинансировать адрес через официальный testnet faucet
FUND_TESTNET = True
FAUCET_URL = "https://faucet.altnet.rippletest.net/accounts"

# =============================

def create_wallet():
    """
    Создаёт новый кошелёк XRPL и возвращает объект Wallet.
    Wallet содержит: .seed, .classic_address, .public_key, .private_key
    """
    w = Wallet.create()  # создает новый seed и ключи
    return w

def fund_testnet_address(address: str):
    """
    Запрашивает финансирование тестовой сети (если существует faucet).
    Возвращает JSON ответа faucet или None.
    """
    try:
        resp = requests.post(FAUCET_URL, json={"destination": address}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("Не удалось запросить фаусет:", e)
        return None

def main():
    print("Создаём новый XRPL-кошелёк...")
    wallet = create_wallet()

    # Подготавливаем и выводим данные
    out = {
        "seed (secret)": wallet.seed,                # важная секретная строка (начинается с 's' обычно)
        "classic_address": wallet.classic_address,   # адрес r...
        "public_key": getattr(wallet, "public_key", None),
        "private_key": getattr(wallet, "private_key", None),
    }

    print("\n===== NEW WALLET =====")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("======================\n")

    # Предупреждение
    print("!!! ВАЖНО: Сохраните seed в безопасном месте (не в коде, не в публичных репозиториях).")
    print("Если этот seed кто-то получит — он сможет контролировать средства на этом адресе.\n")

    if FUND_TESTNET:
        print("Пытаемся профинансировать адрес через testnet faucet...")
        resp = fund_testnet_address(wallet.classic_address)
        if resp:
            print("Faucet response:")
            print(json.dumps(resp, indent=2, ensure_ascii=False))
            # если faucet вернул funding info, можно вывести баланс через RPC (немного подождём)
            time.sleep(2)
            try:
                from xrpl.models.requests import AccountInfo
                r = client.request(AccountInfo(account=wallet.classic_address, ledger_index="validated", strict=True))
                print("\nAccountInfo (после funding):")
                print(json.dumps(r.result, indent=2, ensure_ascii=False))
            except Exception as e:
                print("Не удалось получить AccountInfo:", e)
        else:
            print("Фаусет недоступен или произошла ошибка.")
    else:
        print("FUND_TESTNET = False — пропускаем запрос фауса.")

if __name__ == "__main__":
    main()
