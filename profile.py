class Profile:

    def __init__(self, address):
        # Add option for a signature ( For security )
        self.address = address
        self.name = None
        self.balance = 100
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
