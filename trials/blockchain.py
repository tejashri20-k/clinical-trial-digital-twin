import os
from web3 import Web3

# Connect to Ethereum Sepolia through Alchemy
RPC_URL = os.environ.get("ALCHEMY_RPC_URL", "")
w3 = Web3(Web3.HTTPProvider(RPC_URL)) if RPC_URL else Web3()

# Contract address configured in Render
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "")

# Private key of a TESTNET-ONLY wallet that holds a little Sepolia ETH.
# It signs the storeHash transactions. Set it in Render's environment
# variables - never commit it to GitHub.
WALLET_PRIVATE_KEY = os.environ.get("WALLET_PRIVATE_KEY", "").strip()

# Smart contract ABI
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "recordId", "type": "string"},
            {"internalType": "string", "name": "dataHash", "type": "string"}
        ],
        "name": "storeHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "recordId", "type": "string"}
        ],
        "name": "getHash",
        "outputs": [
            {"internalType": "string", "name": "", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Create the contract object only when configuration is available
contract = (
    w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=CONTRACT_ABI
    )
    if CONTRACT_ADDRESS and Web3.is_address(CONTRACT_ADDRESS)
    else None
)


def get_onchain_hash(record_id):
    """Read the hash stored on the blockchain for a record ('' if none)."""
    if contract is None:
        raise RuntimeError(
            "Blockchain is not configured on the server "
            "(ALCHEMY_RPC_URL / CONTRACT_ADDRESS missing)."
        )

    return contract.functions.getHash(record_id).call()


def store_hash_on_blockchain(record_id, data_hash):
    """Write a record's hash to the Sepolia contract.

    Signs the transaction with WALLET_PRIVATE_KEY and returns the
    transaction hash immediately (it does not wait for the block to be
    mined, so the web request stays fast).
    """
    if contract is None:
        raise RuntimeError(
            "Blockchain is not configured on the server "
            "(ALCHEMY_RPC_URL / CONTRACT_ADDRESS missing)."
        )

    if not WALLET_PRIVATE_KEY:
        raise RuntimeError(
            "WALLET_PRIVATE_KEY is not set on the server, so the hash "
            "could not be written to the blockchain."
        )

    key = WALLET_PRIVATE_KEY
    if not key.startswith("0x"):
        key = "0x" + key

    account = w3.eth.account.from_key(key)
    function = contract.functions.storeHash(record_id, data_hash)

    gas = int(function.estimate_gas({"from": account.address}) * 1.3)

    transaction = function.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "chainId": w3.eth.chain_id,
        "gas": gas,
        "gasPrice": int(w3.eth.gas_price * 1.2),
    })

    signed = w3.eth.account.sign_transaction(transaction, key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction).hex()

    return tx_hash if tx_hash.startswith("0x") else "0x" + tx_hash