class Message {
  final String sender;
  final String receiver;
  final String text;

  Message({
    required this.sender,
    required this.receiver,
    required this.text,
  });

  Map<String, dynamic> toJson() => {
    'sender': sender,
    'receiver': receiver,
    'text': text,
  };

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      sender: json['sender'] ?? '0',
      receiver: json['receiver'] ?? '0',
      text: json['text'] ?? '0',
    );
  }
}
