"""
Implementation of USGS's machine-to-machine API exception codes: https://m2m.cr.usgs.gov/api/docs/exceptioncodes/
"""

from typing import Dict, Callable, Union


class GeneralEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class AuthenticationEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class RateLimitEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class DownloadEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class ExportEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class InventoryEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class OrderEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class SubscriptionEarthExplorerException(Exception):
    """Errors, that fall into the 'General' module"""


class ErrorCodes:
    KNOWN_ERROR_CODES: Dict[str, Dict[str, Union[str, Callable]]] = {
        "ENDPOINT_UNAVAILABLE": {
            "msg": "This endpoint is not available to the requested version",
            "cls": GeneralEarthExplorerException,
        },
        "UNKNOWN": {
            "msg": "An unknown error occurred - full details in developer log",
            "cls": GeneralEarthExplorerException,
        },
        "INPUT_FORMAT": {
            "msg": "JSON payload could not be parsed as valid JSON",
            "cls": GeneralEarthExplorerException,
        },
        "INPUT_PARAMETER_INVALID": {
            "msg": "Invalid parameters used - full details in error message",
            "cls": GeneralEarthExplorerException,
        },
        "INPUT_INVALID": {
            "msg": "Invalid parameters used - full details in error message",
            "cls": GeneralEarthExplorerException,
        },
        "NOT_FOUND": {
            "msg": "Couldn't find the input - full details in error message",
            "cls": GeneralEarthExplorerException,
        },
        "SERVER_ERROR": {
            "msg": "API not configured to handle the request - full details in error message",
            "cls": GeneralEarthExplorerException,
        },
        "VERSION_UNKNOWN": {
            "msg": "Unknown version used",
            "cls": GeneralEarthExplorerException,
        },
        "AUTH_INVALID": {
            "msg": "User credential verification failed",
            "cls": AuthenticationEarthExplorerException,
        },
        "AUTH_UNAUTHORIZED": {
            "msg": "User account does not have access to the requested endpoint",
            "cls": AuthenticationEarthExplorerException,
        },
        "AUTH_KEY_INVALID": {
            "msg": "Invalid API Key",
            "cls": AuthenticationEarthExplorerException,
        },
        "RATE_LIMIT": {
            "msg": "User attempted to run multiple requests at a time",
            "cls": RateLimitEarthExplorerException,
        },
        "RATE_LIMIT_USER_DL": {
            "msg": "User has reached download-related rate limits",
            "cls": RateLimitEarthExplorerException,
        },
        "DOWNLOAD_ERROR": {
            "msg": "Download does not belong to the user",
            "cls": DownloadEarthExplorerException,
        },
        "EXPORT_ERROR": {
            "msg": "Unable to create metadata export",
            "cls": ExportEarthExplorerException,
        },
        "DATASET_ERROR": {
            "msg": "This dataset does not support - full details in error message",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_UNAUTHORIZED": {
            "msg": "Dataset is not available for the user - full details in error message",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_AUTH": {
            "msg": "Dataset is not available for the user - full details in error message",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_INVALID": {
            "msg": "Invalid dataset used",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_CUSTOM_CLEAR_ERROR": {
            "msg": "Unable to clear dataset customization",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_CUSTOM_GET_ERROR": {
            "msg": "Unable to get dataset customization",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_CUSTOMS_GET_ERROR": {
            "msg": "Unable to get dataset customizations",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_CUSTOM_SET_ERROR": {
            "msg": "Unable to create or update dataset customization",
            "cls": InventoryEarthExplorerException,
        },
        "DATASET_CUSTOMS_SET_ERROR": {
            "msg": "Unable to create or update dataset customization",
            "cls": InventoryEarthExplorerException,
        },
        "SEARCH_CREATE_ERROR": {
            "msg": "Unable to create search records or unable to auto-execute the search request",
            "cls": InventoryEarthExplorerException,
        },
        "SEARCH_ERROR": {
            "msg": "Unable to execute search request",
            "cls": InventoryEarthExplorerException,
        },
        "SEARCH_EXECUTE_ERROR": {
            "msg": "Unable to execute search request",
            "cls": InventoryEarthExplorerException,
        },
        "SEARCH_FAILED": {
            "msg": "Search failed",
            "cls": InventoryEarthExplorerException,
        },
        "SEARCH_RESULT_ERROR": {
            "msg": "Unable to translate results into response format",
            "cls": InventoryEarthExplorerException,
        },
        "SEARCH_UNAVAILABLE": {
            "msg": "Search has not been completed",
            "cls": InventoryEarthExplorerException,
        },
        "SEARCH_UPDATE_ERROR": {
            "msg": "Unable to update the search - full details in the error message",
            "cls": InventoryEarthExplorerException,
        },
        "ORDER_ERROR": {
            "msg": "An order related error occurred - full details in error message",
            "cls": OrderEarthExplorerException,
        },
        "ORDER_AUTH": {
            "msg": "Order does not belong to the user",
            "cls": OrderEarthExplorerException,
        },
        "ORDER_INVALID": {
            "msg": "Invalid order given",
            "cls": OrderEarthExplorerException,
        },
        "RESTORE_ORDER_ERROR": {
            "msg": "Unable to restore order units - full details in error message",
            "cls": OrderEarthExplorerException,
        },
        "SUBSCRIPTION_ERROR": {
            "msg": "Subscription creation failed",
            "cls": SubscriptionEarthExplorerException,
        },
        "INPUT_PARAMETER_REQUIRED": {
            "msg": "A parameter is required and was not supplied",
            "cls": GeneralEarthExplorerException,
        },
    }

    def __call__(self, code: str) -> None:
        return ErrorCodes.KNOWN_ERROR_CODES[code]["cls"](
            ErrorCodes.KNOWN_ERROR_CODES[code]["msg"]
        )
