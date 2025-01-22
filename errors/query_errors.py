class AddressExpiredError(Exception):
    """Exception raised when a forwarding address has expired."""
    
    def __init__(self, message="The forwarding address has expired"):
        self.message = message
        super().__init__(self.message)

class AddressNotActiveError(Exception):
    """Exception raised when a forwarding address is not active."""
    
    def __init__(self, message="The forwarding address is not active"):
        self.message = message
        super().__init__(self.message)

class AddressNotFoundError(Exception):
    """Exception raised when a forwarding address is not found."""
    
    def __init__(self, message="The forwarding address was not found"):
        self.message = message
        super().__init__(self.message)