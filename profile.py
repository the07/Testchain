class Profile:

    def __init__(self, address, name=None, balance=None, data=None):
        # Add option for a signature ( For security )
        self.address = address
        if name is not None:
            self.name = name
        else:
            self.name = None
        if balance is not None:
            self.balance = balance
        else:
            self.balance = 100
        if data is not None:
            self.data = data
        else:
            self.data = {}

    def edit_name(self, new_name):
        self.name = new_name
        return self.name

    def add_data(self, new_data): # new_data is type dictionary

        for key in new_data:
            self.data[key] = new_data[key]

    def transfer(self, amount):

        if amount > self.balance:
            return "Not enough balance"
        else:
            self.balance -= amount
