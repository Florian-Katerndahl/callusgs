from argparse import Namespace
import logging

from callusgs import Api
from callusgs.utils import (
    determine_log_level,
    get_auth_from_environment
)
from callusgs.cli.validations import ValidateCleanArgs

api_logger = logging.getLogger("callusgs")

def clean(args: Namespace):
    clean_logger = logging.getLogger("callusgs.clean")
    logging.basicConfig(
        level=determine_log_level(args.verbose, args.very_verbose),
        format="%(asctime)s [%(name)s %(levelname)s]: %(message)s",
    )
    for handler in logging.root.handlers:
        handler.addFilter(logging.Filter("callusgs"))
        handler.setLevel(determine_log_level(args.verbose, args.very_verbose))

    if args.username is None and args.auth is None:
        args.username, args.auth = get_auth_from_environment()

    ValidateCleanArgs(args).check()

    with Api(method=args.auth_method, user=args.username, auth=args.auth) as ee_session:
        searched_labels = ee_session.download_labels()
        clean_logger.info("Request %d in session %d: Retrieved download labels", searched_labels.request_id, searched_labels.session_id)
        unique_labels = set()
        for entry in searched_labels.data:
            unique_labels.add(entry["label"])

        for label in unique_labels:
            ee_session.download_order_remove(label)
            clean_logger.info("Deleted download order %s", label)
