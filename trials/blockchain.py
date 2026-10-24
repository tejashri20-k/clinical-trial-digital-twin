from web3 import Web3

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

# Deployed smart contract address
CONTRACT_ADDRESS = "0x9DB41174221eA8a933FB97016136F2f69e0Bd798"

# Smart contract ABI
CONTRACT_ABI = [
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "recordId",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "dataHash",
                "type": "string"
            }
        ],
        "name": "storeHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "recordId",
                "type": "string"
            }
        ],
        "name": "getHash",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Create contract object
contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=CONTRACT_ABI
)

def store_hash_on_blockchain(record_id, data_hash):
    account = w3.eth.accounts[0]

    transaction = contract.functions.storeHash(
        record_id,
        data_hash
    ).transact({
        "from": account
    })

    receipt = w3.eth.wait_for_transaction_receipt(transaction)

    return receipt