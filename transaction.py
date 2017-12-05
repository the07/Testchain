import hashlib
from time import time
import json

class Transaction:

    def __init__(self, handle, data, amount, destination=None):
        """
            Creates a new transaction object.

            :param handle: <str> User Id of the sender
            :param data: <dict> Data to be added to the blockchain
            :param amount: <int> Amount to be paid to the miner or transferred to another id
            :param destination: <str> (Optional) User Id of the recipient

        """

        self.handle = handle
        self.data = data
        self.amount = amount
        self.timestamp = time()
        if destination:
            self.destination = destination
        self.tx_id = self.calculate_tx_id()

    def calculate_tx_id(self):
        """
            Calculate a transaction hash and return the string

        """

        data_to_json = {
            "handle": self.handle,
            "data": self.data,
            "amount": self.amount,
            "time": self.timestamp,
            "destination": self.destination or 0,
        }

        data_json = json.dumps(data_to_json, sort_keys=True)
        hash_object = hashlib.sha256(data_json.encode('utf-8'))
        return hash_object.hexdigest()

    def toJSON(self):
        return json.dumps(self, default=lambda o: {key: value for key, value in o.__dict__.items()}, sort_keys=True)

    def __repr__(self):
        return "<Transaction {}>".format(self.tx_id)

    def __str__(self):
        return str(self.__dict__)

if __name__ == '__main__':
    pass
