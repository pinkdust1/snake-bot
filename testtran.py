from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.models.requests import AccountInfo
from xrpl.utils import xrp_to_drops

# RPC узел (testnet)
JSON_RPC_URL = "https://s1.ripple.com:51234"
client = JsonRpcClient(JSON_RPC_URL)

# 🔒 твой seed (только seed, не адрес)
SECRET = "sEd7ArkaAzAPkFWstvKc8MNnN8gvpRj"  # замените на ваш

# ⚠️ Адрес получателя (обязательно начинается с r)
DESTINATION = "rN2CHxsWbUnBwaxw7w2Sg1ZHtKuYKiyiDF"

# создаем кошелек из seed
wallet = Wallet.from_seed(SECRET)

# создаем транзакцию
payment = Payment(
    account=wallet.classic_address,
    amount=xrp_to_drops(0.00001),  # 1 XRP (можно изменить)
    destination=DESTINATION,
)

# отправляем и ждем подтверждения
print("Отправляем транзакцию...")
response = submit_and_wait(payment, client, wallet)

print("\nРезультат:")
print(response.result)
