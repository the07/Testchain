import pyelliptic
import json
import hashlib
import socket

from blockchain import Blockchain
from transaction import Transaction
from block import Block
from profile import Profile

import requests
from klein import Klein
from uuid import uuid4

import configparser
import os.path

FULL_NODE_PORT = 19003
NODES_URL = "http://{}:{}/nodes"
NEW_NODES_URL = "http://{}:{}/nodes/register"
NEW_BLOCK_URL = "http://{}:{}/block/new"
NEW_USER_URL = "http://{}:{}/user/add"
CHAIN_URL = "http://{}:{}/chain"

class Node:

    # Instantiate the node
    app = Klein()

    # Create a configuration instance or read an existing config file
    config = configparser.ConfigParser()
    if os.path.exists('node.ini'):

        # Read the required variables - Node Identifier, Blockchain, privatekey, other file paths
        pass
    else:
        # TODO : Generate a privatekey key for the node_identifier
        config['DEFAULT'] = {'ServerAliveInterval': 45,
            'Compression': 'yes',
            'CompressionLevel': '3'
            }
        config['NODE-ID'] = {}

    def __init__(self, node_identifier=None, blockchain=None):
        """
            :param node_identifier: <str> (Optional) A Globally unique Identifier for each node, also acts as wallet address
            :param blockchain: <blockchain> (Optional) If a global uuid exists, so will a blockchain file/object.
        """

        if node_identifier is None and blockchain is None:
            # Generate a globally unique address for this node
            self.node_identifier = str(uuid4()).replace('-','')
            self.config['NODE-ID']['node_identifier'] = self.node_identifier

            self.peer_nodes = set(['192.168.43.224']) #TODO: figure out how to deal with first node
            self.config['NODE-ID']['peer_nodes'] = ', '.join(self.peer_nodes)

            existing_chain = self.synchronize()

            if existing_chain is not None:
                # TODO: add functions to initiate transaction and block from JSON

                remote_blocks = []
                remote_users = []
                for block in existing_chain["Blocks"]:
                    current_transactions = []
                    for block_transaction in existing_chain["Blocks"][block]["transactions"]:
                        block_transaction_json = json.loads(block_transaction)
                        current_amount = block_transaction_json["amount"]
                        current_destination = block_transaction_json["destination"]
                        current_handle = block_transaction_json["handle"]
                        current_data = block_transaction_json["data"]
                        current_timestamp = block_transaction_json["timestamp"]
                        transaction = Transaction(current_handle, current_data, current_amount, current_destination, current_timestamp)
                        current_transactions.append(transaction)
                    current_index = int(block)
                    current_proof = existing_chain["Blocks"][block]["proof"]
                    current_block_previous_hash = existing_chain["Blocks"][block]["previous_hash"]
                    current_block_timestamp = existing_chain["Blocks"][block]["timestamp"]
                    current_block = Block(current_index, current_transactions, current_proof, current_block_previous_hash, current_block_timestamp)
                    remote_blocks.append(current_block)
                for user in existing_chain["Users"]:
                    current_user_address = user
                    current_user_data = existing_chain["Users"][user]["data"]
                    current_user_name = existing_chain["Users"][user]["name"]
                    current_user_balance = existing_chain["Users"][user]["balance"]
                    current_user = Profile(current_user_address, current_user_name, current_user_balance,current_user_data)
                    remote_users.append(current_user)
                self.Peopleschain = Blockchain(remote_blocks, remote_users)

                print ("Blockchain created")

            else:
                self.Peopleschain = Blockchain()

            # TODO: ADD Blockchain file path to config file

            with open('node.ini', 'w') as configfile:
                self.config.write(configfile)
        else:
            self.node_identifier = node_identifier
            self.peer_nodes = set(config['PEER-NODES'])
            self.Peopleschain = blockchain

        self.app.run('0.0.0.0', FULL_NODE_PORT)

    def my_node(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        my_node = s.getsockname()[0]
        s.close()
        return my_node

    def request_nodes(self, node, port):
        url = NODES_URL.format(node, port)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                all_nodes = response.json()
                return all_nodes
        except requests.exceptions.RequestException as re:
            pass
        return None

    def remove_nodes(self, nodes):
        for node in nodes:
            self.peer_nodes.discard(node)


    def request_nodes_from_all(self):
        full_nodes = self.peer_nodes.copy()
        bad_nodes = set()

        for node in full_nodes:
            if node == self.my_node():
                continue
            all_nodes = self.request_nodes(node, FULL_NODE_PORT)
            if all_nodes is not None:
                full_nodes = full_nodes.union(all_nodes["full_nodes"])
            else:
                bad_nodes.add(node)
        self.peer_nodes = full_nodes
        self.remove_nodes(bad_nodes)
        bad_nodes = set()
        return

    def broadcast_node(self):

        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "host": self.my_node()
        }

        for node in self.peer_nodes:
            if node == self.my_node():
                continue
            url = NEW_NODES_URL.format(node, FULL_NODE_PORT)
            try:
                requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)

        self.remove_nodes(bad_nodes)
        bad_nodes.clear()

        return

    def broadcast_block(self, block):

        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "index": block.index,
            "transactions": [transaction.toJSON() for transaction in block.transactions],
            "proof": block.proof,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
        }

        for node in self.peer_nodes:
            if node == self.my_node():
                continue
            url = NEW_BLOCK_URL.format(node, FULL_NODE_PORT)
            try:
                requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)

        self.remove_nodes(bad_nodes)
        bad_nodes.clear()

        return

    def broadcast_user(self, user):

        bad_nodes = set()

        data = {
            "address": user.address,
        }

        for node in self.peer_nodes:
            if node == self.my_node():
                continue
            url = NEW_USER_URL.format(node, FULL_NODE_PORT)
            try:
                requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)

        self.remove_nodes(bad_nodes)
        bad_nodes.clear()

    def synchronize(self):
        """ Download blockchain from other nodes, make the longest chain my chain. """

        self.request_nodes_from_all()
        self.broadcast_node()
        bad_nodes = set()
        longest = 0
        for node in self.peer_nodes:
            if node == self.my_node():
                continue
            url = CHAIN_URL.format(node, FULL_NODE_PORT)
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    remote_chain = response.json()
                    if len(remote_chain["Blocks"]) > longest:
                        my_chain = remote_chain
                        longest = len(remote_chain["Blocks"])
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)

        self.remove_nodes(bad_nodes)
        bad_nodes.clear()

        if longest > 0:
            return my_chain
        else:
            return None

    def proof_of_work(self, last_proof):
        """
            A simple proof of work algorithm:
                - Find a number p' such that p % p' == 0 and p % 9 == 0
                - p: Previous proof, p': New proof

        """

        proof = 1
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof.

        :param last_proof: Previous proof
        :param proof: Current proof
        :return: True if found else False

        """
        print ("Trying proof: {}".format(proof))
        return (last_proof % proof == 0 and proof % 9 == 0)

    def add_profile(self, address):

        if address in [user.address for user in self.Peopleschain.users]:
            return None

        user_profile = Profile(address)
        self.Peopleschain.users.append(user_profile)
        response = {
            "message": "New User Profile Created.",
            "address": address,
            "balance": user_profile.balance,
        }
        return response, user_profile

    def broadcast_user_change(self, user):
        pass

    @app.route('/create', methods=['GET'])
    def create_profile(self, request):

        response, user_profile = self.add_profile(self.node_identifier)
        if response is None:
            response = {
                "message": "User already exists!",
            }
            return json.dumps(response)
        self.broadcast_user(user_profile)
        return json.dumps(response)

    @app.route('/user/add', methods=['POST'])
    def add_user(self, request):

        request_body = json.loads(request.content.read())
        response, user_profile = self.add_profile(request_body["address"])
        if response is None:
            response = {
                "message": "User already exists",
            }
        return json.dumps(response)


    @app.route('/view/<address>', methods=['GET'])
    def view_profile(self, request, address):

        for user in self.Peopleschain.users:
            if address == user.address:

                response = {
                    "address": user.address,
                    "name": user.name,
                    "balance": user.balance,
                    "data": user.data,
                }

                return json.dumps(response)

        response = {
            "message": "User does not exist"
        }

        return json.dumps(response)

    @app.route('/edit/<address>', methods=['POST'])
    def edit_profile(self, request, address):

        # Transaction Fee for any kind of editing
        transaction_fee = 20
        request_body = json.loads(request.content.read())
        for user in self.Peopleschain.users:
            if address == user.address:
                if user.balance >= transaction_fee:
                    transaction_data = {}
                    user.balance -= transaction_fee # TODO add a transfer function
                    response = {
                        "message": "Profile Updated",
                    }
                    if 'name' in request_body.keys():
                        user.edit_name(request_body['name'])
                        transaction_data['name'] = request_body['name']
                        response["Name Changed to: "] = request_body['name']
                    if 'data' in request_body.keys():
                        user.add_data(request_body['data'])
                        response["Added data"] = request_body['data']
                        transaction_data['user-data'] = request_body['data']
                    user_transaction = Transaction(user.address, transaction_data, 20, "Network")
                    self.Peopleschain.push_unconfirmed_transaction(user_transaction)

                    return json.dumps(response)
                else:
                    response = {
                        "message": "Not enough balance",
                    }

                    return json.dumps(response)

        response = {
            "message": "User Not Found",
        }

        return json.dumps(response)

    @app.route('/mine', methods=['GET'])
    def mine(self, request):
        # We run the proof of work algorithm to get the next proof
        last_block = self.Peopleschain.last_block
        last_proof = last_block.proof
        proof = self.proof_of_work(last_proof)
        print ("Proof of work: {}".format(proof))
        # We must send a reward for finding the proof
        reward_transaction  = Transaction("Network", {"message": "Block reward"}, 200, self.node_identifier)

        self.Peopleschain.push_unconfirmed_transaction(reward_transaction)

        # Add money to the node
        for user in self.Peopleschain.users:
            if user.address == self.node_identifier:
                user.balance += 200

        new_index = last_block.index + 1
        previous_hash = last_block.hash

        new_block = Block(new_index, self.Peopleschain.unconfimed_transaction, proof, previous_hash)
        self.Peopleschain.add_block(new_block)

        #Once the block has been created, reset unconfimed_transaction
        self.Peopleschain.unconfimed_transaction = []
        # Broadcast new block to other nodes
        # TODO: Receive confirmation from other nodes, about the validity of the block, if more than 50% success, only then add block to chain
        self.broadcast_block(new_block)
        return json.dumps(str(new_block))


    @app.route('/chain', methods=['GET'])
    def view_chain(self, request):

        unconfimed_transaction_json = {}
        for each_transaction in self.Peopleschain.unconfimed_transaction:
            unconfimed_transaction_json[each_transaction.tx_id] = {
                "handle": each_transaction.handle,
                "data": each_transaction.data,
                "amount": each_transaction.amount,
                "timestamp": each_transaction.timestamp,
                "destination": each_transaction.destination
            }
        blocks_json = {}
        for each_block in self.Peopleschain.blocks:
            blocks_json[each_block.index] = {
                "transactions": [transaction.toJSON() for transaction in each_block.transactions],
                "timestamp": each_block.timestamp,
                "proof": each_block.proof,
                "previous_hash": each_block.previous_hash
            }

        users_json = {}
        for each_user in self.Peopleschain.users:
            users_json[each_user.address] = {
                "name": each_user.name,
                "balance": each_user.balance,
                "data": each_user.data,
            }

        data = {
            "unconfirmed_transaction": unconfimed_transaction_json,
            "Blocks":  blocks_json,
            "Users": users_json,
        }

        return json.dumps(data)

    @app.route('/nodes')
    def view_nodes(self, request):
        response = {
            "full_nodes" : list(self.peer_nodes)
        }

        return json.dumps(response)

    @app.route('/nodes/register', methods=['POST'])
    def register_nodes(self, request):
        request_body = json.loads(request.content.read())
        host = request_body['host']
        print (host)
        self.peer_nodes.add(host)
        response = {
            "message": "Node registered",
            "Status": 200
        }

        return json.dumps(response)

    @app.route('/block/new', methods=['POST'])
    def register_block(self, request):
        request_body = json.loads(request.content.read())
        new_block = Block(request_body['index'], request_body['transactions'], request_body['proof'], request_body['previous_hash'], request_body['timestamp'])
        #TODO: Check validity of block, only then add to chain
        self.Peopleschain.add_block(new_block)
        response = {
            "Success": "New Block Added"
        }

        return json.dumps(response)

if __name__ == '__main__':

    node = Node()
