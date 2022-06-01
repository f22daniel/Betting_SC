import json
import os

import requests.exceptions
import urllib3.exceptions
from openpyxl import load_workbook
import web3.exceptions
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv
import datetime
import re
import requests

abi = ''
tx_hash = ''
my_address = ''
private_key = ''
chain_id = ''
balance = ''
index = ''
bytecode = ''
contract_address = ''

install_solc("0.8.11")

load_dotenv('/Users/f22daniel/PycharmProjects/Griraffe/smart_contract_development/Web3_Betting_SC/.env')

# Loading error messages
error_dict = {}
column = 1
ef = load_workbook('/Users/f22daniel/PycharmProjects/Griraffe/smart_contract_development/Web3_Betting_SC/errors.xlsx')
ef_s = ef.active

# Creating error messages dictionary
try:
    while True:
        if 'ERROR' in ef_s[f'A{column}'].value:
            error_dict.update({ef_s[f'A{column}'].value: ef_s[f'B{column}'].value})
            # print(error_dict)
            column = column + 1
except TypeError:
    pass
print(error_dict)


def Compile_and_Deploy_SC():
    global signed_txn, tx_hash, tx_receipt, _contract, contract_address, bytecode, abi, index

    with open("/Users/f22daniel/PycharmProjects/Griraffe/smart_contract_development/Web3_Betting_SC/Betting_SC.sol",
              'r') as file:
        Betting_SC = file.read()

    compiled_sol = compile_standard(
        {
            'language': 'Solidity',
            'sources': {'Betting_SC.sol': {'content': Betting_SC}},
            'settings': {
                'outputSelection': {
                    '*': {'*': ['abi', 'metadata', 'evm.bytecode', 'evm.sourceMap']}
                }
            },
        },
        solc_version='0.8.11',
    )
    with open('compiled_code.json', 'w') as file:
        json.dump(compiled_sol, file, indent=1)

    with open('compiled_code.json', 'r') as file:
        compiled_sol = json.loads(file.read())
    # Get Bytecode
    bytecode = compiled_sol['contracts']['Betting_SC.sol']['Betting_SC']['evm']['bytecode']['object']
    # Get ABI
    abi = compiled_sol['contracts']['Betting_SC.sol']['Betting_SC']['abi']
    while True:
        try:
            i = int(input('Enter odds on player A: '))
            j = int(input('Enter odds on player B: '))
            k = int(input('Enter betting duration in hours: '))
        except ValueError:
            print("Wrong input, please try again.")
            pass
        else:
            break
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.getTransactionCount(my_address)
    print(f'nonce: {nonce}')
    transaction = contract.constructor(i, j, k).buildTransaction(
        {'chainId': chain_id, "gasPrice": w3.eth.gas_price, 'from': my_address, 'nonce': nonce})
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    _contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    contract_address = tx_receipt.contractAddress
    print(f'Contract deployed on: {contract_address}')


def Connect_to_an_existing_SC_on_Rinkeby():
    global _contract, abi, w3, index, contract_address
    contract_address = input('Enter address of the contract: ')
    api = os.getenv('API')
    url = f'https://api-rinkeby.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={api}'
    response = requests.get(url)
    content = response.json()
    abi = content.get('result')
    _contract = w3.eth.contract(address=contract_address, abi=abi)

def Connect_to_an_existing_SC_on_Ganache():
    global _contract, abi, w3, index, contract_address
    contract_address = input('Enter address of the contract: ')
    with open('compiled_code.json', 'r') as file:
        compiled_sol = json.loads(file.read())
    abi = compiled_sol['contracts']['Betting_SC.sol']['Betting_SC']['abi']
    print(abi)
    _contract = w3.eth.contract(address=contract_address, abi=abi)


# Connect to the Rinkeby network
def Connect_to_Rinkeby():
    global w3, my_address, private_key, balance, chain_id
    try:
        w3 = Web3(Web3.HTTPProvider(os.getenv('INFURA')))
        chain_id = 4
        my_address = os.getenv('ADDRESS')
        private_key = os.getenv('PRIVATE_KEY')
        balance = w3.eth.getBalance(my_address)
        print(f'The balance on {my_address} is: ', balance / 10 ** 18, 'ETH')
    except web3.exceptions.TimeExhausted as e:
        print(str(e))


def Connect_to_Ganache():
    global w3, my_address, private_key, balance, chain_id
    w3 = Web3(Web3.HTTPProvider('HTTP://127.0.0.1:8545'))
    chain_id = 1337
    try:
        my_address = input('Enter your wallet address: ')
        private_key = input('Enter your private key: ')
        private_key = '0x' + private_key
        balance = w3.eth.getBalance(my_address)
        print(f'The balance on {my_address} is: ', balance / 10 ** 18, 'ETH')
    except web3.exceptions.InvalidAddress as e:
        print(str(e))


def Add_Capital():

    while True:
        try:

            while True:
                try:
                    amount_sent = int(input('Enter an amount: '))
                    money = str(input('Select W for Wei, G for Gwei, E for ETH: '))
                    money = str.upper(money)
                    if money == 'W':
                        pass
                    elif money == 'G':
                        amount_sent = amount_sent * (10 ** 9)
                    elif money == 'E':
                        amount_sent = amount_sent * (10 ** 18)
                    else:
                        print('Wrong input.')
                        continue
                except ValueError:
                    print("Wrong input, please try again.")
                    pass
                else:
                    break
            nonce = w3.eth.getTransactionCount(my_address)
            store_transaction = _contract.functions.addCapital().buildTransaction(
                {'chainId': chain_id, "gasPrice": w3.eth.gas_price, 'from': my_address, 'nonce': nonce, 'value': amount_sent})
            signed_store_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
            send_store_tx = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
            w3.eth.wait_for_transaction_receipt(send_store_tx)
            print(f'Balance of the contract is {_contract.functions.ViewContractBalance().call()} Wei')
            print(f'Balance of the contract is {(_contract.functions.ViewContractBalance().call()) / 18} ETH')
        except web3.exceptions.ContractLogicError as e:
            msg = str(e)
            print(msg)
            e_msg = None
            for i in range(column - 1, 0, -1):
                try:
                    e_msg = re.search(f'ERROR{i}', msg)
                    e_msg = (e_msg.group())
                    # print(f'e_msg: {e_msg}')
                    break
                except AttributeError:
                    # print(f'exception {i}')
                    pass
            error = (error_dict.get(e_msg))
            print(error)
            break
        except TimeoutError:
            print('Timeout!!')
            break
        except urllib3.exceptions.ReadTimeoutError as e:
            print(str(e))
            break
        except requests.exceptions.ReadTimeout as e:
            print(str(e))
            break
        except ValueError as e:
            print(str(e))
            break
        except web3.exceptions.TimeExhausted as e:
            print(str(e))
        else:
            break


def Refund():
    while True:
        try:
            nonce = w3.eth.getTransactionCount(my_address)
            store_transaction = _contract.functions.Refund().buildTransaction(
                {'chainId': chain_id, "gasPrice": w3.eth.gas_price, 'from': my_address, 'nonce': nonce})
            signed_store_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
            send_store_tx = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
            w3.eth.wait_for_transaction_receipt(send_store_tx)
        except web3.exceptions.ContractLogicError as e:
            msg = str(e)
            print(msg)
            e_msg = None
            for i in range(column - 1, 0, -1):
                try:
                    e_msg = re.search(f'ERROR{i}', msg)
                    e_msg = (e_msg.group())
                    # print(f'e_msg: {e_msg}')
                    break
                except AttributeError:
                    # print(f'exception {i}')
                    pass
            error = (error_dict.get(e_msg))
            print(error)
            break
        except TimeoutError:
            print('Timeout!!')
            break
        except urllib3.exceptions.ReadTimeoutError as e:
            print(str(e))
            break
        except requests.exceptions.ReadTimeout as e:
            print(str(e))
            break
        except web3.exceptions.TimeExhausted as e:
            print(str(e))
        except ValueError as e:
            print(str(e))
            break
        else:
            break


def Betting_Money():
    while True:
        try:
            while True:
                try:
                    Age = int(input('Enter your age: '))
                    amount_sent = int(input('Enter an amount: '))
                    money = str(input('Select W for Wei, G for Gwei, E for ETH: '))
                    money = str.upper(money)
                    if money == 'W':
                        pass
                    elif money == 'G':
                        amount_sent = amount_sent * (10 ** 9)
                    elif money == 'E':
                        amount_sent = amount_sent * (10 ** 18)
                    else:
                        print('Wrong input.')
                        continue
                except ValueError:
                    print("Wrong input, please try again.")
                    pass
                else:
                    break
            Player = input('Enter a player you would like to bet on (A or B): ')
            Player = str.upper(Player)
            nonce = w3.eth.getTransactionCount(my_address)
            store_transaction = _contract.functions.Bet_Money(Age, Player).buildTransaction(
                {'chainId': chain_id, "gasPrice": w3.eth.gas_price, 'from': my_address, 'nonce': nonce,
                 'value': amount_sent})
            signed_store_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
            send_store_tx = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
            w3.eth.wait_for_transaction_receipt(send_store_tx)
            Get_Amount_Betted()
        except web3.exceptions.ContractLogicError as e:
            msg = str(e)
            print(msg)
            e_msg = None
            for i in range(column - 1, 0, -1):
                try:
                    e_msg = re.search(f'ERROR{i}', msg)
                    e_msg = (e_msg.group())
                    # print(f'e_msg: {e_msg}')
                    break
                except AttributeError:
                    # print(f'exception {i}')
                    pass
            error = (error_dict.get(e_msg))
            print(error)
            break
        except TimeoutError:
            print('Timeout!!')
            break
        except urllib3.exceptions.ReadTimeoutError as e:
            print(str(e))
            break
        except requests.exceptions.ReadTimeout as e:
            print(str(e))
            break
        except ValueError as e:
            print(str(e))
            break
        except web3.exceptions.TimeExhausted as e:
            print(str(e))
        else:
            break


def Add_more():
    while True:
        try:
            while True:
                try:
                    amount_sent = int(input('Enter an amount: '))
                    money = str(input('Select W for Wei, G for Gwei, E for ETH: '))
                    money = str.upper(money)
                    if money == 'W':
                        pass
                    elif money == 'G':
                        amount_sent = amount_sent * (10 ** 9)
                    elif money == 'E':
                        amount_sent = amount_sent * (10 ** 18)
                    else:
                        print('Wrong input.')
                        continue
                except ValueError:
                    print("Wrong input, please try again.")
                    pass
                else:
                    break
            nonce = w3.eth.getTransactionCount(my_address)
            store_transaction = _contract.functions.add_more().buildTransaction(
                {'chainId': chain_id, "gasPrice": w3.eth.gas_price, 'from': my_address, 'nonce': nonce,
                 'value': amount_sent})
            signed_store_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
            send_store_tx = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
            w3.eth.wait_for_transaction_receipt(send_store_tx)
            Get_Amount_Betted()
        except web3.exceptions.ContractLogicError as e:
            msg = str(e)
            print(msg)
            e_msg = None
            for i in range(column - 1, 0, -1):
                try:
                    e_msg = re.search(f'ERROR{i}', msg)
                    e_msg = (e_msg.group())
                    # print(f'e_msg: {e_msg}')
                    break
                except AttributeError:
                    # print(f'exception {i}')
                    pass
            error = (error_dict.get(e_msg))
            print(error)
            break
        except TimeoutError:
            print('Timeout!!')
            break
        except urllib3.exceptions.ReadTimeoutError as e:
            print(str(e))
            break
        except requests.exceptions.ReadTimeout as e:
            print(str(e))
            break
        except ValueError as e:
            print(str(e))
            break
        except web3.exceptions.TimeExhausted as e:
            print(str(e))
        else:
            break


def Declare_winner_pay_bets():
    while True:
        try:
            winner = input('The winner is: ')
            winner = str.upper(winner)
            nonce = w3.eth.getTransactionCount(my_address)
            store_transaction = _contract.functions.Declare_Winner(winner).buildTransaction(
                {'chainId': chain_id, "gasPrice": w3.eth.gas_price, 'from': my_address, 'nonce': nonce})
            signed_store_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
            send_store_tx = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
            w3.eth.wait_for_transaction_receipt(send_store_tx)
            print(f'{_contract.functions.ViewContractBalance().call()} Wei')
            print(f'{(_contract.functions.ViewContractBalance().call()) / 10 ** 9} Gwei')
            print(f'{(_contract.functions.ViewContractBalance().call()) / 10 ** 18} ETH')
        except web3.exceptions.ContractLogicError as e:
            msg = str(e)
            print(msg)
            e_msg = None
            for i in range(column - 1, 0, -1):
                try:
                    e_msg = re.search(f'ERROR{i}', msg)
                    e_msg = (e_msg.group())
                    # print(f'e_msg: {e_msg}')
                    break
                except AttributeError:
                    # print(f'exception {i}')
                    pass
            error = (error_dict.get(e_msg))
            print(error)
            break
        except TimeoutError:
            print('Timeout!!')
            break
        except urllib3.exceptions.ReadTimeoutError as e:
            print(str(e))
            break
        except requests.exceptions.ReadTimeout as e:
            print(str(e))
            break
        except ValueError as e:
            print(str(e))
            break
        except web3.exceptions.TimeExhausted as e:
            print(str(e))
        else:
            break


def Get_Amount_Betted():
    global my_address
    for i in range(0, (_contract.functions.getLength().call())):
        dtbs = ((_contract.functions.database(i).call())[2])
        if dtbs == my_address:
            print(f'Your betted amount is: {(_contract.functions.database(i).call())[0]} Wei')
            print(f'Your betted amount is: {((_contract.functions.database(i).call())[0]) / 10 ** 9} Gwei')
            print(f'Your betted amount is: {((_contract.functions.database(i).call())[0]) / 10 ** 18} ETH')
            break
        else:
            pass


def Odds_on_Players():
    print(f'Odds on player A are: {_contract.functions.oddsPlayerA().call()}')
    print(f'Odds on player B are: {_contract.functions.oddsPlayerB().call()}')


def Time_until_the_end():
    deadline = _contract.functions.Deadline().call()
    current_time = _contract.functions.CurrentTime().call()
    remaining_time = deadline - current_time
    if remaining_time > 0 and (_contract.functions.WinnerDeclared().call()) is False:
        print(f'Remaining time until bets are closed: {datetime.timedelta(seconds=remaining_time)}')
    elif remaining_time == 0 and (_contract.functions.WinnerDeclared().call()) is False:
        print('Time is up. Betting no longer possible!!')
    elif _contract.functions.WinnerDeclared().call():
        print('Winner has already been declared!!')


def Get_List_of_Betters():
    print('The database is made up of: ')
    for i in range(0, (_contract.functions.getLength().call())):
        print((_contract.functions.database(i).call()))


def Get_Contract_balance():
    print('The balance of the contracts account is:')
    try:
        print(f'{_contract.functions.ViewContractBalance().call()} Wei')
        print(f'{(_contract.functions.ViewContractBalance().call()) / 10 ** 9} Gwei')
        print(f'{(_contract.functions.ViewContractBalance().call()) / 10 ** 18} ETH')
    except web3.exceptions.ContractLogicError as e:
        msg = str(e)
        print(msg)
        e_msg = None
        for i in range(column - 1, 0, -1):
            try:
                e_msg = re.search(f'ERROR{i}', msg)
                e_msg = (e_msg.group())
                # print(f'e_msg: {e_msg}')
                break
            except AttributeError:
                # print(f'exception {i}')
                pass
        error = (error_dict.get(e_msg))
        print(error)


def winner_declared():
    print(f'Declaration of a winner: {_contract.functions.WinnerDeclared().call()}')
    return bool


def Network_selection():
    print('R for Rinkeby')
    print('G for Ganache')
    network = input('Select a connection: ')
    network = str.upper(network)
    if network == 'R':
        Connect_to_Rinkeby()
    elif network == 'G':
        Connect_to_Ganache()


def Contract_selection():
    print('D to "deploy contract"')
    print('R to "connect to the contract on Rinkeby"')
    print('C to "connect to the contract on Ganache"')
    cs = input('Select a contract: ')
    cs = str.upper(cs)
    if cs == 'D':
        Compile_and_Deploy_SC()
    elif cs == 'R':
        Connect_to_an_existing_SC_on_Rinkeby()
    elif cs == 'C':
        Connect_to_an_existing_SC_on_Ganache()


while True:
    Network_selection()
    Contract_selection()
    print('')
    print(my_address)
    print(f'{private_key}\n')
    Odds_on_Players()
    while True:
        print('')
        print('A to "Add Capital"(available only to the admin)')
        print('B to "Bet money"')
        print('C to "Add more money"')
        print('D to "Refund"')
        print('E to "Declare winner and pay bets" (available only to the admin)')
        print('F to "Get list of betters" (available only to the admin)')
        print('G to "Get time until the betting deadline"')
        print('H to "Get contract balance" (available only to the admin)')
        print('I to "Get odds on Players"')
        print('J to "Get amount betted"')
        print('K to "Select network and different address"')
        print('L to "See if winner has been declared"')
        print('Q to quit')
        function = input('Enter a function you would like to execute: ')
        function = str.upper(function)
        print('')
        if function == 'A':
            Add_Capital()
        elif function == 'B':
            Betting_Money()
        elif function == 'C':
            Add_more()
        elif function == 'D':
            Refund()
        elif function == 'E':
            Declare_winner_pay_bets()
        elif function == 'F':
            Get_List_of_Betters()
        elif function == 'G':
            Time_until_the_end()
        elif function == 'H':
            Get_Contract_balance()
        elif function == 'I':
            Odds_on_Players()
        elif function == 'J':
            Get_Amount_Betted()
        elif function == 'K':
            Network_selection()
        elif function == 'L':
            winner_declared()
        elif function == 'Q':
            break
        else:
            print('Input out of range, please try again.')
        # os.system('cls')
    x = input('Press Enter to move on./Press Q to quit: ')
    x = str.upper(x)
    if x == 'Q':
        break
