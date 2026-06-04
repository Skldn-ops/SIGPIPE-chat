class Message:
    def __init__(self, sender="0", receiver="0", text="0"):
        self.sender = sender
        self.receiver = receiver
        self.text = text
    
    def to_dict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'text': self.text
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data.get('sender', '0'), 
                  data.get('receiver', '0'), 
                  data.get('text', '0'))
