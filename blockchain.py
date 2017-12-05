import hashlib
import logging
import threading
from time import time

from block import Block
from transaction import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Blockchain():

    def __init__(self, blocks=None, users=None):

        self.unconfimed_transaction = []
        self.blocks = []
        self.users = []

        if blocks is None:
            # TODO: When a node starts, check parameters for peer list and then synchronize the chain
            genesis_block = self.get_genesis_block()
            self.add_block(genesis_block)
        else:
            for block in blocks:
                self.add_block(block)
            if users is not None:
                for user in users:
                    self.users.append(user)

    def get_genesis_block(self):

        #TODO: Reward miner with some amount
        genesis_transaction_one = Transaction(
            "Network",
            {"message": "Genesis Transaction 1"},
            0,
            "Network"
        )

        genesis_transaction_two = Transaction(
            "Network",
            {"message": "Genesis Transaction 2"},
            0,
            "Network"
        )

        genesis_transactions = [genesis_transaction_one, genesis_transaction_two]
        print ("Creating genesis block")
        genesis_block  = Block(0, genesis_transactions, 0, 0)
        return genesis_block

    def add_block(self, block):
        # TODO change this from memory to persistent

        if self.validate_block(block):
            self.blocks.append(block)
            return True
        return False

    @property
    def last_block(self):
        return self.blocks[-1]

    def validate_block(self, block):
        # TODO write code to validate a block
        return True

    def validate_chain(self):
        pass

    def pop_next_unconfirmed_transaction(self):
        try:
            return self.unconfimed_transaction.pop(0)
        except IndexError:
            return None

    def push_unconfirmed_transaction(self, transaction):
        self.unconfimed_transaction.append(transaction)
        return True

    def __str__(self):
        return str(self.__dict__)
