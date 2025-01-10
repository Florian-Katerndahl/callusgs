from argparse import Namespace
import logging
from typing import List
from callusgs import Api
from callusgs.utils import (
    report_usgs_messages,
    determine_log_level,
    get_auth_from_environment
)
api_logger = logging.getLogger("callusgs")

def grid2ll(args: Namespace):
    grid2ll_logger = logging.getLogger("callusgs.grid2ll")
    logging.basicConfig(
        level=determine_log_level(args.verbose, args.very_verbose),
        format="%(asctime)s [%(name)s %(levelname)s]: %(message)s",
    )
    for handler in logging.root.handlers:
        handler.addFilter(logging.Filter("callusgs"))
        handler.setLevel(determine_log_level(args.verbose, args.very_verbose))
    
    if args.username is None and args.auth is None:
        args.username, args.auth = get_auth_from_environment()

    # can still be None if environment variables are not set
    assert (
        args.username is not None and args.auth is not None
    ), "Username and Authentication key (e.g. password, token) not specified"

    accumulated_output: List = []

    assert len(args.coordinates) > 0, "Must give at least one WRS coordinate pair"

    with Api(method=args.auth_method, user=args.username, auth=args.auth) as ee_session:
        report_usgs_messages(ee_session.notifications("M2M").data)
        grid2ll_logger.info("Successfully connected to API endpoint")
        for path_row in args.coordinates:
            grid_response = ee_session.grid2ll(
                args.grid, args.response_shape, *path_row.split(",")
            )
            accumulated_output.append(grid_response.data)

    print(accumulated_output)
