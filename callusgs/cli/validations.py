"""
This module contains functions to validate various inputs passed on to
the CLI applications. The seperation is done to reduce complexity of 
individual programs.
"""
from argparse import Namespace
from datetime import datetime

class ValidateDownloadArgs:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args


    def check_authentication(self) -> None:
        if self.args.username is None:
            raise AssertionError("Username not specified")
        if self.args.auth is None:
            raise AssertionError("Authentication key (e.g. password, token) not specified")


    def check_cloudcover(self) -> None:
        if not (0 <= self.args.cloudcover[0] <= self.args.cloudcover[1] <= 100):
            raise AssertionError("cloud cover must be from 0 to 100 and minimal cloud cover must be smaller or equal to upper bound")


    def check_dates(self) -> None:
        if datetime.strptime(self.args.date[0], "%Y-%m-%d") > datetime.strptime(self.args.date[1], "%Y-%m-%d"):
            raise AssertionError("Start date must be earlier or on same day than end date")


    def check_coordinates(self) -> None:
        if self.args.aoi_coordinates is None and self.args.aoi_file is None:
            raise AssertionError("Either coordinate list or file with AOI must be given")
        if not self.args.aoi_coordinates:
            return  # return when coordinate file is given
        if (len(self.args.aoi_coordinates) % 2) != 0:
            raise AssertionError("Number of coordinates given must be even")
        if len(self.args.aoi_coordinates) > 2 and self.args.aoi_coordinates[:2] != self.args.aoi_coordinates[-2:]:
            raise AssertionError("Polygon ring must be closed")
        if len(self.args.aoi_coordinates) == 2 and self.args.aoi_type == "Mbr":
            raise AssertionError("Point coordinate can't be used with Mbr AOI type")


    def check(self) -> None:
        self.check_authentication()
        self.check_cloudcover()
        self.check_dates()
        self.check_coordinates()


class ValidateCleanArgs:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args


    def check_authentication(self) -> None:
        if self.args.username is None:
            raise AssertionError("Username not specified")
        if self.args.auth is None:
            raise AssertionError("Authentication key (e.g. password, token) not specified")


    def check(self) -> None:
        self.check_authentication()


class ValidateGeocodeArgs:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args


    def check_authentication(self) -> None:
        if self.args.username is None:
            raise AssertionError("Username not specified")
        if self.args.auth is None:
            raise AssertionError("Authentication key (e.g. password, token) not specified")


    def check(self) -> None:
        self.check_authentication()

class ValidateGrid2llArgs:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args


    def check_authentication(self) -> None:
        if self.args.username is None:
            raise AssertionError("Username not specified")
        if self.args.auth is None:
            raise AssertionError("Authentication key (e.g. password, token) not specified")


    def check(self) -> None:
        self.check_authentication()
