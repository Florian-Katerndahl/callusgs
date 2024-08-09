from enum import Enum


class ExitCodes(Enum):
    E_OK = 0
    E_ORDERINCOMPLETE = 1
    E_LARGEORDER = 2
    E_RATELIMIT = 3
    E_UNKNONW = 99
