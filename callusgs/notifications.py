"""
This module is used to parse notifications from USGS related
to their service and data set status.
"""
from html.parser import HTMLParser
from typing import Set

class USGSNotificationParser(HTMLParser):
    """
    Notification parser

    :param HTMLParser: Python HTMLParser to subclass
    :type HTMLParser: Python HTMLParser
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.message = []

    def handle_data(self, data):
        """
        As per Python's documentation, this method is called
        to handle arbitrary data.

        :param data: data stream
        :type data: str
        """
        self.message.append(data.strip())
    
    def __repr__(self) -> str:
        return " ".join(self.message)
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def to_set(self) -> Set[str]:
        """
        Convert message to set with one entry (the parsed message).

        :return: Set with one entry, the message.
        :rtype: Set[str]
        """
        return {self.__repr__(), }
