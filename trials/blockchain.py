import os
from web3 import Web3

# Connect to Ethereum Sepolia through Alchemy
RPC_URL = os.environ.get("ALCHEMY_RPC_URL", "")
w3 = Web3(Web3.HTTPProvider(RPC_URL)) if RPC_URL else Web3()

# Contract address configured in Render
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "")

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

def store_hash_on_blockchain(record_id, data_hash):
    raise RuntimeError(
        "Blockchain writes are disabled on the hosted backend. "
        "Store hashes through Remix using the authorized wallet."
    )