import hashlib
import json
from time import time

class Block:
    """ A Block holds a list of transaction. """

    def __init__(self, index, transactions, proof, previous_hash, timestamp=None):
        """
            :param index: <int> The index of the block
            :param transactions: <list> List of transactions to be added to this block
            :param proof: <int> The proof given by the proof of work algorithm
            :param previous_hash: <str> Hash of the previous block

        """

        self.index = index
        self.transactions = transactions
        if timestamp is None:
            self.timestamp = time()
        else:
            self.timestamp = timestamp
        self.proof = proof
        self.previous_hash = previous_hash
        self.hash = self.calculate_block_hash()

    def calculate_block_hash(self):

        data_to_json = {
            "index": self.index,
            "transactions": [transaction.toJSON() for transaction in self.transactions],
            "timestamp": self.timestamp,
            "proof": self.proof,
            "previous_hash": self.previous_hash,
        }

        data_json = json.dumps(data_to_json, sort_keys=True)
        hash_object = hashlib.sha256(data_json.encode('utf-8'))
        return hash_object.hexdigest()

    def to_json(self):
        return json.dumps(self, default=lambda o: {key: value for key, value in o.__dict__.items()}, sort_keys=True)

    def __repr__(self):
        return "<PeopleChain Block {}>".format(self.hash)

    def __str__(self):
        return str(self.__dict__)
