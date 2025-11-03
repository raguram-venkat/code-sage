from abc import ABC, abstractmethod

class Subcommand(ABC):
    
    """
    Parser will only get instantiated after registering
    So -> register is the only function that you call in cli.py
    """
    
    name: str
    help: str
    
    def __init__(self):
        self.parser = None
    
    @abstractmethod
    def add_arguments(self):
        pass
        
    
    @abstractmethod
    def run(self, args):
        pass
    
    def register(self, subparsers_helper):
        self.parser = subparsers_helper.add_parser(self.name, help=self.help)
        # print(f"Registered subcommand: {self.name}")
        self.add_arguments()
        self.parser.set_defaults(func=self.run)
        