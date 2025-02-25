from argparse import Namespace
import logging
from callusgs import Api
from callusgs.utils import (
    report_usgs_messages,
    determine_log_level,
    get_auth_from_environment
)
from callusgs.cli.validations import ValidateGeocodeArgs

api_logger = logging.getLogger("callusgs")

def geocode(args: Namespace):
    geocode_logger = logging.getLogger("callusgs.geocode")
    logging.basicConfig(
        level=determine_log_level(args.verbose, args.very_verbose),
        format="%(asctime)s [%(name)s %(levelname)s]: %(message)s",
    )
    for handler in logging.root.handlers:
        handler.addFilter(logging.Filter("callusgs"))
        handler.setLevel(determine_log_level(args.verbose, args.very_verbose))

    if args.username is None and args.auth is None:
        args.username, args.auth = get_auth_from_environment()

    ValidateGeocodeArgs(args).check()

    with Api(method=args.auth_method, user=args.username, auth=args.auth) as ee_session:
        report_usgs_messages(ee_session.notifications("M2M").data)
        geocode_logger.info("Successfully connected to API endpoint")
        geocode_response = ee_session.placename(args.feature, args.name)
        print(geocode_response.data["results"] or "No results found!")
