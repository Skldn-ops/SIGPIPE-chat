from enum import Enum, auto, IntEnum


class MessageStatus(IntEnum):
    SENT = 1
    DELIVERED = 2
    READ = 3