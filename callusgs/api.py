"""
API Class representing USGS's machine-to-machine API: https://m2m.cr.usgs.gov/api/docs/reference/
"""

from pathlib import Path
from typing import Optional, Any, Dict, List, Literal, Callable
from datetime import datetime
from json import loads, dumps
from urllib.parse import unquote
import sys
import warnings
import requests
from tqdm import tqdm

from callusgs.types import (
    UserContext,
    SortCustomization,
    SceneFilter,
    TemporalFilter,
    SpatialFilter,
    DatasetCustomization,
    Metadata,
    SearchSort,
    FileGroups,
    ProxiedDownload,
)
from callusgs.errors import AuthenticationEarthExplorerException, GeneralEarthExplorerException


class Api:
    ENDPOINT: str = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    def __init__(self, method: Optional[str] = "token", user: Optional[str] = None, auth: Optional[str] = None) -> None:
        self.key: Optional[str] = None
        self.login_timestamp: Optional[datetime] = None
        self.headers: Dict[str, str] = None
        self.login_method = method
        self.user = user
        self.auth = auth

    def __enter__(self) -> "Api":
        match self.login_method:
            case "token":
                self.login_token(self.user, self.auth)
            case "password":
                self.login(self.user, self.auth)
            case "sso":
                self.login_sso(self.user, self.auth)
            case "app_guest":
                self.login_app_guest(self.user, self.auth)
            case _:
                raise AttributeError(f"Unknown login method: {self.login_method}")

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.logout()

    def _call_get(self, url: str, stream: Optional[bool] = True) -> requests.Response:
        """
        Abstract method to call a URL with headers set and optional stream parameter.

        :param url: URL to call with GET requeest
        :type url: str
        :param stream: Immediately download the response content, defaults to True
        :type stream: Optional[bool], optional
        :return: Response object
        :rtype: requests.Response
        """        
        return requests.get(url, headers=self.headers, stream=stream)

    def _call_post(
        self, endpoint: str, conversion: Optional[Literal["text", "binary"]] = "text", /, **kwargs
    ) -> Dict:
        """
        Abstract method to call API endpoints with POST method

        .. note:: You don't need to pass the headers argument as it's taken from the class instance.
            if you want to add additional header fields, update self headers dictionary of the instance.

        .. note:: As per API migration guide: All methods are POST request methods!

        :param endpoint: Endpoint to call
        :type endpoint: str
        :param conversion: How respinse should be interpreted, defaults to "text"
        :type conversion: Optional[Literal["text", "binary"]], optional
        :raises AuthenticationEarthExplorerException: If login is older than two hours, the api token used is not valid anymore
        :raises AttributeError: Paramter passed onto 'conversion' must be either 'text' or 'binary'
        :raises HTTPError:
        :return: Complete API response dictionary
        :rtype: Dict
        """
        SECONDS_PER_HOUR: int = 3600
        if self.login_timestamp is not None and (datetime.now() - self.login_timestamp).total_seconds() >= SECONDS_PER_HOUR * 2:
            raise AuthenticationEarthExplorerException(
                "Two hours have passed since you logged in, api session token expired. Please login again!"
            )

        with requests.post(Api.ENDPOINT + endpoint, headers=self.headers, **kwargs) as r:
            if conversion == "text":
                message_content: Dict = loads(r.text)
            elif conversion == "binary":
                message_content: Dict = loads(r.content)
            else:
                raise AttributeError(
                    f"conversion paramter must be either 'text' or 'binary'. Got {conversion}."
                )

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

        return message_content

    def data_owner(self, data_owner: str) -> Dict:
        """
        This method is used to provide the contact information of the data owner.

        :param data_owner: Used to identify the data owner - this value comes from the dataset-search response
        :type data_owner: str
        :return: Dict containing contact information
        :rtype: Dict
        """
        payload = {"dataOwner": data_owner}
        result = self._call_post("data-owner", data=dumps(payload, default=vars))

        return result["data"]

    def dataset(self, dataset_id: Optional[str] = None, dataset_name: Optional[str] = None) -> Dict:
        """
        This method is used to retrieve the dataset by id or name.

        .. note:: Input datasetId or datasetName and get dataset description (including the respective other part).

        .. warning:: Either `dataset_id` or `dataset_name` must be given!

        :param dataset_id: The dataset identifier, defaults to None
        :type dataset_id: Optional[str], optional
        :param dataset_name: The system-friendly dataset name, defaults to None
        :type dataset_name: Optional[str], optional
        :raises AttributeError:
        :return: Dict containing dataset information
        :rtype: Dict
        """
        if dataset_id is None and dataset_name is None:
            raise AttributeError("Not both dataset_id and dataset_name can be None")

        payload = {"datasetId": dataset_id, "datasetName": dataset_name}
        result = self._call_post("dataset", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_browse(self, dataset_id: str) -> List[Dict]:
        """
        This request is used to return the browse configurations for the specified dataset.

        :param dataset_id: Determines which dataset to return browse configurations for
        :type dataset_id: str
        :return: List of Dicts, each containing information about configuration of subdatasets
        :rtype: List[Dict]
        """
        payload = {"datasetId": dataset_id}
        result = self._call_post("dataset-browse", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_catalogs(self) -> Dict:
        """
         This method is used to retrieve the available dataset catalogs.
         The use of dataset catalogs are not required, but are used to group datasets by
         their use within our web applications.

        :return: Dictionary with all available data catalogs
        :rtype: Dict
        """
        result = self._call_post("dataset-catalogs")

        return result["data"]

    def dataset_categories(
        self,
        catalog: Optional[str] = None,
        include_message: Optional[bool] = None,
        public_only: Optional[bool] = None,
        use_customization: Optional[bool] = None,
        parent_id: Optional[str] = None,
        dataset_filter: Optional[str] = None,
    ) -> Dict:
        """
        This method is used to search datasets under the categories.

        :param catalog: Used to identify datasets that are associated with a given application, defaults to None
        :type catalog: Optional[str], optional
        :param include_message: Optional parameter to include messages regarding specific dataset components, defaults to None
        :type include_message: Optional[bool], optional
        :param public_only: Used as a filter out datasets that are not accessible to unauthenticated general public users, defaults to None
        :type public_only: Optional[bool], optional
        :param use_customization: Used as a filter out datasets that are excluded by user customization, defaults to None
        :type use_customization: Optional[bool], optional
        :param parent_id: If provided, returned categories are limited to categories that are children of the provided ID, defaults to None
        :type parent_id: Optional[str], optional
        :param dataset_filter: If provided, filters the datasets - this automatically adds a wildcard before and after the input value, defaults to None
        :type dataset_filter: Optional[str], optional
        :return: Dict containing all datasets within a catalog
        :rtype: Dict
        """
        payload = {
            "catalog": catalog,
            "includeMessage": include_message,
            "publicOnly": public_only,
            "useCustomization": use_customization,
            "parentId": parent_id,
            "datasetFilter": dataset_filter,
        }
        result = self._call_post("dataset-categories", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_clear_customization(
        self,
        dataset_name: Optional[str] = None,
        metadata_type: Optional[List[str]] = None,
        file_group_ids: Optional[List[str]] = None,
    ) -> None:
        """
        This method is used the remove an entire customization or clear out a specific metadata type.

        :param dataset_name: Used to identify the dataset to clear. If null, all dataset customizations will be cleared., defaults to None
        :type dataset_name: Optional[str], optional
        :param metadata_type: If populated, identifies which metadata to clear(export, full, res_sum, shp), defaults to None
        :type metadata_type: Optional[List[str]], optional
        :param file_group_ids: If populated, identifies which file group to clear, defaults to None
        :type file_group_ids: Optional[List[str]], optional
        :raises GeneralEarthExplorerException:
        """
        payload = {
            "datasetName": dataset_name,
            "metadataType": metadata_type,
            "fileGroupIds": file_group_ids,
        }
        result = self._call_post("dataset-clear-customization", data=dumps(payload, default=vars))

        if result["data"] != 1:
            raise GeneralEarthExplorerException("Value of data section is not 1")

    def dataset_coverage(self, dataset_name: str) -> Dict:
        """
        Returns coverage for a given dataset.

        :param dataset_name: Determines which dataset to return coverage for
        :type dataset_name: str
        :return: Bounding box and GeoJSON coverage
        :rtype: Dict
        """
        payload = {"datasetName": dataset_name}
        result = self._call_post("dataset-coverage", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_filters(self, dataset_name: str) -> Dict:
        """
        This request is used to return the metadata filter fields for the specified dataset. These values can be used as additional criteria when submitting search and hit queries.

        :param dataset_name: Determines which dataset to return filters for
        :type dataset_name: str
        :return: Dict with all related dataset fiters
        :rtype: Dict
        """
        payload = {"datasetName": dataset_name}
        result = self._call_post("dataset-filters", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_get_customization(self, dataset_name: str) -> Dict:
        """
        This method is used to retrieve metadata customization for a specific dataset.

        :param dataset_name: Used to identify the dataset to search
        :type dataset_name: str
        :return: Dict containing customized metadata representations
        :rtype: Dict
        """
        payload = {"datasetName": dataset_name}
        result = self._call_post("dataset-get-customization", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_get_customizations(
        self, dataset_names: Optional[List[str]] = None, metadata_type: Optional[List[str]] = str
    ) -> Dict:
        """
        This method is used to retrieve metadata customizations for multiple datasets at once.

        :param dataset_names: Used to identify the dataset(s) to return. If null it will return all the users customizations, defaults to None
        :type dataset_names: Optional[List[str]], optional
        :param metadata_type: If populated, identifies which metadata to return(export, full, res_sum, shp), defaults to str
        :type metadata_type: Optional[List[str]], optional
        :return: Dict containing customized metadata representations for datasets, identified by their Ids
        :rtype: Dict
        """
        payload = {"datasetNames": dataset_names, "metadataType": metadata_type}
        result = self._call_post("dataset-get-customizations", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_messages(
        self,
        catalog: Optional[str],
        dataset_name: Optional[str] = None,
        dataset_names: Optional[List[str]] = None,
    ) -> Dict:
        """
        Returns any notices regarding the given datasets features.

        :param catalog: Used to identify datasets that are associated with a given application
        :type catalog: Optional[str]
        :param dataset_name: Used as a filter with wildcards inserted at the beginning and the end of the supplied value, defaults to None
        :type dataset_name: Optional[str], optional
        :param dataset_names: Used as a filter with wildcards inserted at the beginning and the end of the supplied value, defaults to None
        :type dataset_names: Optional[List[str]], optional
        :return: Dict containing notices per dataset supplied
        :rtype: Dict
        """
        payload = {"catalog": catalog, "datasetName": dataset_name, "datasetNames": dataset_names}
        result = self._call_post("dataset-messages", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_metadata(self, dataset_name: str) -> Dict:
        """
        This method is used to retrieve all metadata fields for a given dataset.

        :param dataset_name: The system-friendly dataset name
        :type dataset_name: str
        :return: All metadata for given dataset
        :rtype: Dict
        """
        payload = {"datasetName": dataset_name}
        result = self._call_post("dataset-metadata", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_search(
        self,
        catalog: Optional[str] = None,
        category_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        include_messages: Optional[bool] = None,
        public_only: Optional[bool] = None,
        include_unknown_spatial: Optional[bool] = None,
        temporal_filter: Optional[TemporalFilter] = None,
        spatial_filter: Optional[SpatialFilter] = None,
        sort_direction: Optional[Literal["ASC", "DESC"]] = "ASC",
        sort_field: Optional[str] = None,
        use_customization: Optional[bool] = None,
    ) -> Dict:
        """
        This method is used to find datasets available for searching. By passing only API Key, all available datasets are returned. Additional parameters such as temporal range and spatial bounding box can be used to find datasets that provide more specific data. The dataset name parameter can be used to limit the results based on matching the supplied value against the public dataset name with assumed wildcards at the beginning and end.

        .. note:: Can be used to transfrom "natural language description" to datasetId and/or dataset_alias.

        .. warning:: SpatialFilter is an abstract class. SpatialFilterMbr or SpatialFilterGeoJson must be supplied.

        :param catalog: Used to identify datasets that are associated with a given application, defaults to None
        :type catalog: Optional[str], optional
        :param category_id: Used to restrict results to a specific category (does not search sub-sategories), defaults to None
        :type category_id: Optional[str], optional
        :param dataset_name: Used as a filter with wildcards inserted at the beginning and the end of the supplied value, defaults to None
        :type dataset_name: Optional[str], optional
        :param include_messages: Optional parameter to include messages regarding specific dataset components, defaults to None
        :type include_messages: Optional[bool], optional
        :param public_only: Used as a filter out datasets that are not accessible to unauthenticated general public users, defaults to None
        :type public_only: Optional[bool], optional
        :param include_unknown_spatial: Optional parameter to include datasets that do not support geographic searching, defaults to None
        :type include_unknown_spatial: Optional[bool], optional
        :param temporal_filter: Used to filter data based on data acquisition, defaults to None
        :type temporal_filter: Optional[TemporalFilter], optional
        :param spatial_filter: Used to filter data based on data location, defaults to None
        :type spatial_filter: Optional[SpatialFilter], optional
        :param sort_direction: Defined the sorting as Ascending (ASC) or Descending (DESC), defaults to "ASC"
        :type sort_direction: Optional[Literal["ASC", "DESC"]], optional
        :param sort_field: Identifies which field should be used to sort datasets (shortName - default, longName, dastasetName, GloVis), defaults to None
        :type sort_field: Optional[str], optional
        :param use_customization: Optional parameter to indicate whether to use customization, defaults to None
        :type use_customization: Optional[bool], optional
        :return: Get dataset descriptions and attributes
        :rtype: Dict

        :Example:

        Api().dataset_search("EE", "dataset_name="Collection 2 Level-1")
        """
        payload = {
            "catalog": catalog,
            "categoryId": category_id,
            "datasetName": dataset_name,
            "includeMessages": include_messages,
            "publicOnly": public_only,
            "includeUnknownSpatial": include_unknown_spatial,
            "temporalFilter": temporal_filter,
            "spatialFilter": spatial_filter,
            "sortDirection": sort_direction,
            "sortField": sort_field,
            "useCustomization": use_customization,
        }
        result = self._call_post("dataset-search", data=dumps(payload, default=vars))

        return result["data"]

    def dataset_set_customization(
        self,
        dataset_name: str,
        excluded: Optional[bool] = None,
        metadata: Optional[Metadata] = None,
        search_sort: Optional[SearchSort] = None,
        file_groups: Optional[FileGroups] = None,
    ) -> None:
        """
        This method is used to create or update dataset customizations for a given dataset.

        .. warning:: Metadata is an abstract class. Instead use a combination of
            MetadataAnd, MetadataBetween, MetadataOr and MetadataValue.

        :param dataset_name: Used to identify the dataset to search
        :type dataset_name: str
        :param excluded: Used to exclude the dataset, defaults to None
        :type excluded: Optional[bool], optional
        :param metadata: Used to customize the metadata layout, defaults to None
        :type metadata: Optional[Metadata], optional
        :param search_sort: Used to sort the dataset results, defaults to None
        :type search_sort: Optional[SearchSort], optional
        :param file_groups: Used to customize downloads by file groups, defaults to None
        :type file_groups: Optional[FileGroups], optional
        :raises GeneralEarthExplorerException:
        """
        payload = {
            "datasetName": dataset_name,
            "excluded": excluded,
            "metadata": metadata,
            "searchSort": search_sort,
            "fileGroups": file_groups,
        }
        result = self._call_post("dataset-set-customization", data=dumps(payload, default=vars))

        if result["data"] != 1:
            raise GeneralEarthExplorerException("Value of data section is not 1")

    def dataset_set_customizations(self, dataset_customization: DatasetCustomization) -> None:
        """
        This method is used to create or update customizations for multiple datasets at once.

        :param dataset_customization: Used to create or update a dataset customization for multiple datasets
        :type dataset_customization: DatasetCustomization
        :raises GeneralEarthExplorerException:
        """
        payload = {"datasetCustomization": dataset_customization}
        result = self._call_post("dataset-set-customizations", data=dumps(payload, default=vars))

        if result["data"] != 1:
            raise GeneralEarthExplorerException("Value of data section is not 1")

    def download_complete_proxied(self, proxied_downloads: List[ProxiedDownload]) -> Dict:
        """
        Updates status to 'C' with total downloaded file size for completed proxied downloads.

        :param proxied_downloads: Used to specify multiple proxied downloads
        :type proxied_downloads: List[ProxiedDownload]
        :return: Dict containing number of failed downloads and number of statuses updated
        :rtype: Dict
        """
        payload = {"proxiedDownloads": proxied_downloads}
        result = self._call_post("download-complete-proxied", data=dumps(payload, default=vars))

        return result["data"]

    def download_labels(self, download_application: Optional[str] = None) -> List[Dict]:
        # TODO 4
        """
        Gets a list of unique download labels associated with the orders.

        :param download_application: Used to denote the application that will perform the download, defaults to None
        :type download_application: Optional[str], optional
        :return: Information about all valid(?) download orders ['label', 'dateEntered', 'downloadSize', 'downloadCount', 'totalComplete']
        :rtype: List[Dict]
        """
        payload = {"downloadApplication": download_application}
        result = self._call_post("download-labels", data=dumps(payload, default=vars))

        return result["data"]

    def download_order_load(
        self, download_application: Optional[str] = None, label: Optional[str] = None
    ) -> List[Dict]:
        """
        This method is used to prepare a download order for processing by moving the scenes into the queue for processing.

        :param download_application: Used to denote the application that will perform the download, defaults to None
        :type download_application: Optional[str], optional
        :param label: Determines which order to load, defaults to None
        :type label: Optional[str], optional
        :return: Metadata for specified orders given by labels
        :rtype: List[Dict]
        """
        payload = {"downloadApplication": download_application, "label": label}
        result = self._call_post("download-order-load", data=dumps(payload, default=vars))

        return result["data"]

    def download_order_remove(
        self, label: str, download_application: Optional[str] = None, 
    ) -> None:
        """
        This method is used to remove an order from the download queue.

        :param download_application: Used to denote the application that will perform the download
        :type download_application: str
        :param label: Determines which order to remove, defaults to None
        :type label: Optional[str], optional
        :raises GeneralEarthExplorerException:
        """
        payload = {"downloadApplication": download_application, "label": label}
        _ = self._call_post("download-order-remove", data=dumps(payload, default=vars))


    def download_remove(self, download_id: int) -> None:
        """
        Removes an item from the download queue.

        .. note:: "downloadId" can be retrieved by calling download-search.

        :param download_id: Represents the ID of the download from within the queue
        :type download_id: int
        :raises GeneralEarthExplorerException:
        """
        payload = {"downloadId": download_id}
        result = self._call_post("download-remove", data=dumps(payload, default=vars))

        if result["data"] is not True:
            raise GeneralEarthExplorerException("Removal returned False")

    def download_retrieve(
        self, download_application: Optional[str] = None, label: Optional[str] = None
    ) -> Dict:
        """
        Returns all available and previously requests but not completed downloads.

        .. warning:: This API may be online while the distribution systems are unavailable. When this occurs, the downloads being fulfilled by those systems will not appear as available nor are they counted in the 'queueSize' response field.

        :param download_application: Used to denote the application that will perform the download, defaults to None
        :type download_application: Optional[str], optional
        :param label: Determines which downloads to return, defaults to None
        :type label: Optional[str], optional
        :return: Dict with EULAs, List of available downloads (['url', 'label', 'entityId', 'eulaCode', 'filesize' 'datasetId', 'displayId', 'downloadId', 'statusCode', 'statusText', 'productCode', 'productName', 'collectionName']), queue size and requested downloads
        :rtype: Dict
        """
        payload = {"downloadApplication": download_application, "label": label}
        result = self._call_post("download-retrieve", data=dumps(payload, default=vars))

        return result["data"]

    def download_search(
        self,
        active_only: Optional[bool] = None,
        label: Optional[str] = None,
        download_application: Optional[str] = None,
    ) -> List[Dict]:
        """
        This method is used to search for downloads within the queue, regardless of status, that match the given label.

        :param active_only: Determines if completed, failed, cleared and proxied downloads are returned, defaults to None
        :type active_only: Optional[bool], optional
        :param label: Used to filter downloads by label, defaults to None
        :type label: Optional[str], optional
        :param download_application: Used to filter downloads by the intended downloading application, defaults to None
        :type download_application: Optional[str], optional
        :return: All download orders according to filters (['label', 'entityId', 'eulaCode', 'filesize' 'datasetId', 'displayId', 'downloadId', 'statusCode', 'statusText', 'productCode', 'productName', 'collectionName'])
        :rtype: List[Dict]
        """
        payload = {
            "acitveOnly": active_only,
            "label": label,
            "downloadApplication": download_application,
        }
        result = self._call_post("download-search", data=dumps(payload, default=vars))

        return result["data"]

    def download(self, url: str, output_directory: Optional[Path] = Path("."), chunk_size: int = 2048) -> None:
        # https://stackoverflow.com/questions/31804799/how-to-get-pdf-filename-with-python-requests
        result = self._call_get(url)
        result.raise_for_status()

        file_name = unquote(result.headers["content-disposition"].split("filename=").pop().strip('"'))
        download_size = int(result.headers["content-length"])
        print(download_size)

        # https://www.slingacademy.com/article/python-requests-module-how-to-download-files-from-urls/
        with open(output_directory / file_name, "wb") as f, \
             tqdm(desc=file_name, total=download_size, unit="B",
             unit_scale=True, unit_divisor=1024) as bar:
             for chunk in result.iter_content(chunk_size=chunk_size):
                bytes_written = f.write(chunk)
                bar.update(bytes_written)

        result.close()

    def grid2ll(
        self,
        grid_type: Optional[Literal["WRS1", "WRS2"]] = "WRS2",
        response_shape: Optional[Literal["polygon", "point"]] = None,
        path: Optional[str] = None,
        row: Optional[str] = None,
    ) -> Dict:
        """
        Used to translate between known grids and coordinates.

        :param grid_type: Which grid system is being used?, defaults to "WRS2"
        :type grid_type: Optional[Literal["WRS1", "WRS2"]], optional
        :param response_shape: What type of geometry should be returned - a bounding box polygon or a center point?, defaults to None
        :type response_shape: Optional[Literal["polygon", "point"]], optional
        :param path: The x coordinate in the grid system, defaults to None
        :type path: Optional[str], optional
        :param row: The y coordinate in the grid system, defaults to None
        :type row: Optional[str], optional
        :return: Dict describing returned geometry
        :rtype: Dict
        """
        payload = {"gridType": grid_type, "responseShape": response_shape, "path": path, "row": row}
        result = self._call_post("grid2ll", data=dumps(payload, default=vars))

        return result["data"]

    def login(self, username: str, password: str, user_context: Any = None):
        # TODO show notifications after successfull login? Maybe something for an app, not the api integration
        """
        Upon a successful login, an API key will be returned. This key will be active for two
        hours and should be destroyed upon final use of the service by calling the logout method.

        .. note:: This request requires an HTTP POST request instead of a HTTP GET request as a
            security measure to prevent username and password information from being logged
            by firewalls, web servers, etc.

        :param username: ERS Username
        :type username: str
        :param password: ERS Password
        :type password: str
        :param user_context: Metadata describing the user the request is on behalf of, defaults to None
        :type user_context: Any, optional
        :raises HTTPError:
        """
        payload: Dict = {"username": username, "password": password}
        if user_context:
            payload += {"userContext": user_context}

        result = self._call_post("login", data=dumps(payload, default=vars))

        self.key = result["data"]
        self.login_timestamp = datetime.now()
        self.headers = {"X-Auth-Token": self.key}

    def login_app_guest(self, application_token: str, user_token: str):
        """
        This endpoint assumes that the calling application has generated a single-use token to
        complete the authentication and return an API Key specific to that guest user. All
        subsequent requests should use the API Key under the 'X-Auth-Token' HTTP header as the
        Single Sign-On cookie will not authenticate those requests. The API Key will be active
        for two hours, which is restarted after each subsequent request, and should be destroyed
        upon final use of the service by calling the logout method.

        The 'appToken' field will be used to verify the 'Referrer' HTTP Header to ensure the
        request was authentically sent from the assumed application.

        :param application_token: The token for the calling application
        :type application_token: str
        :param user_token: The single-use token generated for this user
        :type user_token: str
        :raises HTTPError:
        """
        payload: Dict = {"application_token": application_token, "user_token": user_token}
        result = self._call_post("login-app-guest", data=dumps(payload, default=vars))

        self.key = result["data"]
        self.login_timestamp = datetime.now()
        self.headers = {"X-Auth-Token": self.key}

    def login_sso(self, user_context: UserContext = None):
        """
        This endpoint assumes that a user has an active ERS Single Sign-On Cookie in their
        browser or attached to this request. Authentication will be performed from the Single
        Sign-On Cookie and return an API Key upon successful authentication. All subsequent
        requests should use the API Key under the 'X-Auth-Token' HTTP header as the Single
        Sign-On cookie will not authenticate those requests. The API Key will be active for
        two hours, which is restarted after each subsequent request, and should be destroyed
        upon final use of the service by calling the logout method.

        :param user_context: Metadata describing the user the request is on behalf of, defaults to None
        :type user_context: UserContext, optional
        :raises NotImplementedError:
        """
        raise NotImplementedError()

    def login_token(self, username: str, token: str):
        """
        This login method uses ERS application tokens to allow for authentication that is not
        directly tied the users ERS password. Instructions for generating the application token
        can be found `here <https://www.usgs.gov/media/files/m2m-application-token-documentation>`_.

        Upon a successful login, an API key will be returned. This key will be active for two
        hours and should be destroyed upon final use of the service by calling the logout method.

        .. note:: This request requires an HTTP POST request instead of a HTTP GET request as a
            security measure to prevent username and password information from being logged by
            firewalls, web servers, etc.

        :param username: ERS Username
        :type username: str
        :param token: Application Token
        :type token: str
        :raises HTTPError:
        """
        payload: Dict = {"username": username, "token": token}

        result = self._call_post("login-token", data=dumps(payload, default=vars))

        self.key = result["data"]
        self.login_timestamp = datetime.now()
        self.headers = {"X-Auth-Token": self.key}

    def logout(self) -> None:
        """
        This method is used to remove the users API key from being used in the future.
        :raises HTTPError:
        """
        with requests.post(Api.ENDPOINT + "logout", headers=self.headers) as r:
            _ = r.raise_for_status()
        self.key = None
        self.headers = None
        self.login_timestamp = None

    def notifications(self, system_id: str) -> List[Dict]:
        """
        Gets a notification list. 

        :param system_id: Used to identify notifications that are associated with a given application
        :type system_id: str
        :return: List of all notifications
        :rtype: List[Dict]
        """        
        payload = {
            "systemId": system_id
        }
        results = self._call_post("notifications", data=dumps(payload, default=vars))

        return results["data"]

    def permissions(self) -> List[str]:
        """
        Returns a list of user permissions for the authenticated user.
        This method does not accept any input.

        :return: List of user permissions
        :rtype: List[str]
        :raises HTTPError:
        """
        result = self._call_post("permissions")

        return result["data"]

    def placename(
        self, feature_type: Optional[Literal["US", "World"]] = None, name: Optional[str] = None
    ) -> Dict:
        """
        Geocoder

        :param feature_type: Type or feature - see type hint, defaults to None
        :type feature_type: Optional[Literal["US", "World"]], optional
        :param name: Name of the feature, defaults to None
        :type name: Optional[str], optional
        :return: Return list of dictionaries for matched places.
            Dictionary keys are: ['id', 'feature_id', 'placename', 'feature_code', 'country_code',
            'latitude', 'longitude', 'feature_name', 'country_name'].
        :rtype: Dict
        :raises HTTPError:
        """
        # TODO convert result dicts to class instances of class Place; depend on method argument if this should
        #  be done
        payload = {"featureType": feature_type, "name": name}
        result = self._call_post("placename", data=dumps(payload, default=vars))

        return result["data"]["results"]

    def scene_list_add(
        self,
        list_id: str,
        dataset_name: str,
        id_field: Optional[Literal["entityId", "displayId"]] = "entityId",
        entity_id: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        ttl: Optional[str] = None,
        check_download_restriction: Optional[bool] = None,
    ) -> None:
        """
        Adds items in the given scene list.

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias
        :type dataset_name: str
        :param id_field: Used to determine which ID is being used, defaults to entityId
        :type id_field: Optional[str], optional
        :param entity_id: Scene Identifier, defaults to None
        :type entity_id: Optional[str], optional
        :param entity_ids: A list of Scene Identifiers, defaults to None
        :type entity_ids: Optional[List[str]], optional
        :param ttl: User defined lifetime using ISO-8601 formatted duration (such as "P1M") for the list, defaults to None
        :type ttl: Optional[str], optional
        :param check_download_restriction: Optional parameter to check download restricted access and availability, defaults to None
        :type check_download_restriction: Optional[bool], optional
        :raises HTTPError:
        :raises RuntimeError: If number of added items does not equal 1 or len(entity_ids), a RunTimeError is raised

        :Example:

        Api.scene_list_add(
            list_id="my_scene_list",
            dataset_name="landsat_ot_c2_l2",
            id_field="displayId",
            entity_id="LC08_L2SP_012025_20201231_20210308_02_T1"
        )
        """
        if entity_id is not None and entity_ids is not None:
            warnings.warn("Both entityId and entityIds given. Ignoring the first one")
        payload = {
            "listId": list_id,
            "datasetName": dataset_name,
            "idField": id_field,
            "entityId": entity_id if entity_ids is None else None,
            "entityIds": entity_ids,
            "timeToLive": ttl,
            "checkDownloadRestriction": check_download_restriction,
        }
        result = self._call_post("scene-list-add", data=dumps(payload, default=vars))

        items_to_add: int = 1 if entity_ids is None else len(entity_ids)
        if result["data"] != items_to_add:
            raise RuntimeError(
                f"Number of scenes added {result['data']} does not equal provided number of scenes {items_to_add}"
            )

    def scene_list_get(
        self,
        list_id: str,
        dataset_name: Optional[str] = None,
        starting_number: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict]:
        """
        Returns items in the given scene list.

        .. note:: starting_number is 1-indexed

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias, defaults to None
        :type dataset_name: Optional[str], optional
        :param starting_number: Used to identify the start number to search from, defaults to None
        :type starting_number: Optional[int], optional
        :param max_results: How many results should be returned?, defaults to None
        :type max_results: Optional[int], optional
        :return: List of items in requested scene list. Each entry is a dictionary in the form of {'entityId', 'datasetName'}.
        :rtype: List[Dict]
        :raises HTTPError:

        :Example:

        Api.scene_list_get(list_id="my_scene_list")
        """
        payload = {
            "listId": list_id,
            "datasetName": dataset_name,
            "startingNumber": starting_number,
            "maxResults": max_results,
        }
        result = self._call_post("scene-list-get", data=dumps(payload, default=vars))

        return result["data"]

    def scene_list_remove(
        self,
        list_id: str,
        dataset_name: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
    ):
        """
        Removes items from the given list. If no datasetName is provided, the call removes
        the whole list. If a datasetName is provided but no entityId, this call removes that
        dataset with all its IDs. If a datasetName and entityId(s) are provided,
        the call removes the ID(s) from the dataset.

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias, defaults to None
        :type dataset_name: Optional[str], optional
        :param entity_id: Scene Identifier, defaults to None
        :type entity_id: Optional[str], optional
        :param entity_ids: A list of Scene Identifiers, defaults to None
        :type entity_ids: Optional[List[str]], optional
        :raises HTTPError:

        :Example:

        Api.scene_list_remove(
            list_id="my_scene_list",
            dataset_name="landsat_ot_c2_l2",
            entity_id="LC80120252020366LGN00"
        )
        """
        if entity_id is not None and entity_ids is not None:
            warnings.warn("Both entityId and entityIds given. Passing both to API.")
        payload = {
            "listId": list_id,
            "datasetName": dataset_name,
            "entityId": entity_id,
            "entityIds": entity_ids,
        }
        _ = self._call_post("scene-list-remove", data=dumps(payload, default=vars))

    def scene_list_summary(self, list_id: str, dataset_name: Optional[str] = None) -> Dict:
        """
        Returns summary information for a given list.

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias, defaults to None
        :type dataset_name: Optional[str], optional
        :return: Dictionary containing a summary and datasets ({'summary', 'datasets'}).
        :rtype: Dict
        :raises HTTPError:
        """
        payload = {
            "listId": list_id,
            "datasetName": dataset_name,
        }
        result = self._call_post("scene-list-summary", data=dumps(payload, default=vars))

        return result["data"]

    def scene_list_types(self, list_filter: Optional[str]) -> List[Dict]:
        """
        Returns scene list types (exclude, search, order, bulk, etc).

        :param list_filter: If provided, only returns listIds that have the provided filter value within the ID
        :type list_filter: Optional[str]
        :return: List of scene list, each containing a dictionary describing a scene list.
        :rtype: List[Dict]
        """
        # TODO list_filter would likely have to be the result of the MetadataFilter types, no?
        payload = {"listFilter": list_filter}
        result = self._call_post("scene-list-types", data=dumps(payload, default=vars))

        return result["data"]

    def scene_metadata(
        self,
        dataset_name: str,
        entity_id: str,
        id_type: Optional[str] = "entityId",
        metadata_type: Optional[str] = None,
        include_null_metadata: Optional[bool] = None,
        use_customization: Optional[bool] = None,
    ) -> Dict:
        """
        This request is used to return metadata for a given scene.

        .. note:: The parameter `entity_id` is named confusingly.
            Depending on `id_type`, passing one of entityId, displayId or orderingId is allowed

        :param dataset_name: Used to identify the dataset to search
        :type dataset_name: str
        :param entity_id: Used to identify the scene to return results for
        :type entity_id: str
        :param id_type: If populated, identifies which ID field (entityId, displayId or orderingId) to use when searching for the provided entityId, defaults to "entityId"
        :type id_type: Optional[str], optional
        :param metadata_type: If populated, identifies which metadata to return (summary, full, fgdc, iso), defaults to None
        :type metadata_type: Optional[str], optional
        :param include_null_metadata: Optional parameter to include null metadata values, defaults to None
        :type include_null_metadata: Optional[bool], optional
        :param use_customization: Optional parameter to display metadata view as per user customization, defaults to None
        :type use_customization: Optional[bool], optional
        :return: Dict containing scene metadata
        :rtype: Dict

        :raises HTTPError:
        """
        payload = {
            "datasetName": dataset_name,
            "entityId": entity_id,
            "idType": id_type,
            "metadataType": metadata_type,
            "includeNullMetadataValues": include_null_metadata,
            "useCustomization": use_customization,
        }
        result = self._call_post("scene-metadata", data=dumps(payload, default=vars))

        return result["data"]

    def scene_metadata_list(
        self,
        list_id: str,
        dataset_name: Optional[str] = None,
        metadata_type: Optional[str] = None,
        include_null_metadata: Optional[bool] = None,
        use_customization: Optional[bool] = None,
    ) -> Dict:
        """
        Scene Metadata where the input is a pre-set list.

        :param list_id: Used to identify the list of scenes to use
        :type list_id: str
        :param dataset_name: Used to identify the dataset to search, defaults to None
        :type dataset_name: Optional[str], optional
        :param metadata_type: If populated, identifies which metadata to return (summary or full), defaults to None
        :type metadata_type: Optional[str], optional
        :param include_null_metadata: Optional parameter to include null metadata values, defaults to None
        :type include_null_metadata: Optional[bool], optional
        :param use_customization: Optional parameter to display metadata view as per user customization, defaults to None
        :type use_customization: Optional[bool], optional
        :return: Dict containing metadata for requested list
        :rtype: Dict
        """
        payload = {
            "datasetName": dataset_name,
            "listId": list_id,
            "metadataType": metadata_type,
            "includeNullMetadataValues": include_null_metadata,
            "useCustomization": use_customization,
        }
        result = self._call_post("scene-metadata-list", data=dumps(payload, default=vars))

        return result["data"]

    def scene_metadata_xml(
        self, dataset_name: str, entity_id: str, metadata_type: Optional[str] = None
    ) -> Dict:
        """
        Returns metadata formatted in XML, ahering to FGDC, ISO and EE scene metadata
        formatting standards.

        .. note:: It's unclear if entity_id refers exclucively to the entityId or
            if other kinds of Ids can be passed as well.

        :param dataset_name: Used to identify the dataset to search
        :type dataset_name: str
        :param entity_id: Used to identify the scene to return results for
        :type entity_id: str
        :param metadata_type: Used to identify the scene to return results for, defaults to None
        :type metadata_type: Optional[str], optional
        :return: Returns dictionary with metadata for requested scene. The XML content is available with the key 'exportContent'
        :rtype: Dict

        :raises HTTPError:
        """
        payload = {
            "datasetName": dataset_name,
            "entityId": entity_id,
            "metadataType": metadata_type,
        }
        result = self._call_post("scene-metadata-list", data=dumps(payload, default=vars))

        return result["data"]

    def scene_search(
        self,
        dataset_name: str,
        max_results: int = 100,
        starting_number: Optional[int] = None,
        metadata_type: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_direction: Optional[Literal["ASC", "DESC"]] = None,
        sort_customization: Optional[SortCustomization] = None,
        use_customization: Optional[bool] = None,
        scene_filter: Optional[SceneFilter] = None,
        compare_list_name: Optional[str] = None,
        bulk_list_name: Optional[str] = None,
        order_list_name: Optional[str] = None,
        exclude_list_name: Optional[str] = None,
        include_null_metadata: Optional[bool] = None,
    ) -> Dict:
        """
        Searching is done with limited search criteria. All coordinates are assumed decimal-degree
        format. If lowerLeft or upperRight are supplied, then both must exist in the request
        to complete the bounding box. Starting and ending dates, if supplied, are used as a
        range to search data based on acquisition dates. The current implementation will
        only search at the date level, discarding any time information. If data in a given
        dataset is composite data, or data acquired over multiple days, a search will be done
        to match any intersection of the acquisition range. There currently is a 50,000 scene
        limit for the number of results that are returned, however, some client applications may
        encounter timeouts for large result sets for some datasets. To use the sceneFilter field,
        pass one of the four search filter objects (SearchFilterAnd, SearchFilterBetween,
        SearchFilterOr, SearchFilterValue) in JSON format with sceneFilter being the root
        element of the object.

        Searches without a 'sceneFilter' parameter can take much longer to execute.
        To minimize this impact we use a cached scene count for 'totalHits' instead of
        computing the actual row count. An additional field, 'totalHitsAccuracy', is
        also included in the response to indicate if the 'totalHits' value was computed
        based off the query or using an approximated value. This does not impact the users ability
        to access these results via pagination. This cached value is updated daily for all datasets
        with active data ingests. Ingest frequency for each dataset can be found using the
        'ingestFrequency' field in the dataset, dataset-categories and dataset-search endpoint
        responses.

        .. note:: It returns 100 results by default. Users can set input 'maxResults' to get
            different results number returned. It is recommened to set the maxResults less than
            10,000 to get better performance. The allowed maximum is 50_000.

        .. note:: The response of this request includes a 'totalHits' response parameter
            that indicates the total number of scenes that match the search query to allow for
            pagination.

        .. note:: The argument dataset_name can be given by datasetAlias.

        .. note:: starting_number is 1-indexed

        .. warning: SortCustomizatoin and SceneFilter are likely not implemented correctly, yet!

        :param dataset_name: Used to identify the dataset to search. Can be datasetAlias.
        :type dataset_name: str
        :param max_results: How many results should be returned ?, defaults to 100
        :type max_results: int, optional
        :param starting_number: Used to identify the start number to search from, defaults to None
        :type starting_number: Optional[int], optional
        :param metadata_type: If populated, identifies which metadata to return (summary or full), defaults to None
        :type metadata_type: Optional[str], optional
        :param sort_field: Determines which field to sort the results on, defaults to None
        :type sort_field: Optional[str], optional
        :param sort_direction: Determines how the results should be sorted, defaults to None
        :type sort_direction: Optional[Literal["ASC", "DESC"]], optional
        :param sort_customization: Used to pass in custom sorts, defaults to None
        :type sort_customization: Optional[SortCustomization], optional
        :param use_customization: Optional parameter to indicate whether to use customization, defaults to None
        :type use_customization: Optional[bool], optional
        :param scene_filter: Used to filter data within the dataset, defaults to None
        :type scene_filter: Optional[SceneFilter], optional
        :param compare_list_name: If provided, defined a scene-list listId to use to track scenes selected for comparison, defaults to None
        :type compare_list_name: Optional[str], optional
        :param bulk_list_name: If provided, defined a scene-list listId to use to track scenes selected for bulk ordering, defaults to None
        :type bulk_list_name: Optional[str], optional
        :param order_list_name: If provided, defined a scene-list listId to use to track scenes selected for on-demand ordering, defaults to None
        :type order_list_name: Optional[str], optional
        :param exclude_list_name: If provided, defined a scene-list listId to use to exclude scenes from the results, defaults to None
        :type exclude_list_name: Optional[str], optional
        :param include_null_metadata: Optional parameter to include null metadata values, defaults to None
        :type include_null_metadata: Optional[bool], optional
        :raises HTTPError:
        :return: Dictionary containing search results as List[Dict] together with some additional search meatadata (['recordsReturned', 'totalHits', 'totalHitsAccuracy', 'isCustomized', 'numExcluded', 'startingNumber', 'nextRecord'])
        :rtype: Dict

        :Example:

        # General search
        Api.scene_search(
        "gls_all",
        max_results=500,
        scene_filter=SceneFilter(AcquisitionFilter(...), CloudCoverFilter(...), ...),
        bulk_list_name="my_bulk_list",
        metadata_type="summary",
        order_list_name="my_order_list",
        starting_number=1,
        compare_list_name="my_comparison_list",
        exlucde_list_name="my_exclude_list"
        )

        # Search with spatial filter and ingest filter

        # Search with acquisition filter

        # Search with metadata filter (metadata filter ids can be retrieved by calling dataset-filters)

        # Sort search results using useCustomization flag and sortCustomization
        """
        # TODO add missing examples
        payload = {
            "datasetName": dataset_name,
            "maxResults": max_results,
            "startingNumber": starting_number,
            "metadataType": metadata_type,
            "sortField": sort_field,
            "sortDirection": sort_direction,
            "sortCustomization": sort_customization,
            "useCustomization": use_customization,
            "sceneFilter": scene_filter,
            "compareListName": compare_list_name,
            "bulkListName": bulk_list_name,
            "orderListName": order_list_name,
            "excludeListName": exclude_list_name,
            "includeNullMetadataValue": include_null_metadata,
        }
        result = self._call_post("scene-search", data=dumps(payload, default=vars))

        return result["data"]

    def scene_search_delete(
        self,
        dataset_name: str,
        max_results: int = 100,
        starting_number: Optional[int] = None,
        sort_field: Optional[str] = None,
        sort_direction: Optional[Literal["ASC", "DEC"]] = None,
        temporal_filter: Optional[TemporalFilter] = None,
    ) -> Dict:
        """
        This method is used to detect deleted scenes from datasets that support it. Supported
        datasets are determined by the 'supportDeletionSearch' parameter in the 'datasets'
        response. There currently is a 50,000 scene limit for the number of results that are
        returned, however, some client applications may encounter timeouts for large result
        sets for some datasets.

        .. note:: It returns 100 results by default. Users can set input 'maxResults' to get
            different results number returned. It is recommened to set the maxResults less than
            10,000 to get better performance. The allowed maximum is 50_000.

        .. note:: The response of this request includes a 'totalHits' response parameter
            that indicates the total number of scenes that match the search query to allow for
            pagination.

        .. note:: The argument dataset_name can be given by datasetAlias.

        .. note:: starting_number is 1-indexed

        :param dataset_name: Used to identify the dataset to search
        :type dataset_name: str
        :param max_results: How many results should be returned ?, defaults to 100
        :type max_results: int, optional
        :param starting_number: Used to identify the start number to search from, defaults to None
        :type starting_number: Optional[int], optional
        :param sort_field: Determines which field to sort the results on, defaults to None
        :type sort_field: Optional[str], optional
        :param sort_direction: Determines how the results should be sorted, defaults to None
        :type sort_direction: Optional[Literal["ASC", "DEC"]], optional
        :param temporal_filter: Used to filter data based on data acquisition, defaults to None
        :type temporal_filter: Optional[TemporalFilter], optional
        :return: Dictionary containing search results as List[Dict] together with some additional search meatadata
        :rtype: Dict

        :raises HTTPError:
        """
        payload = {
            "datasetName": dataset_name,
            "maxResults": max_results,
            "startingNumber": starting_number,
            "sortField": sort_field,
            "sortDirection": sort_direction,
            "temporalFilter": temporal_filter,
        }
        result = self._call_post("scene-search-delete", data=dumps(payload, default=vars), headers=self.headers)

        return result["data"]

    def scene_search_secondary(
        self,
        entity_id: str,
        dataset_name: str,
        max_results: int = 100,
        starting_number: Optional[int] = None,
        metadata_type: Optional[str] = None,
        sort_filed: Optional[str] = None,
        sort_direction: Optional[Literal["ASC", "DESC"]] = None,
        compare_list_name: Optional[str] = None,
        bulk_list_name: Optional[str] = None,
        order_list_name: Optional[str] = None,
        exlucde_list_name: Optional[str] = None,
    ) -> Dict:
        """
        This method is used to find the related scenes for a given scene.

        .. note:: It returns 100 results by default. Users can set input 'maxResults' to get
            different results number returned. It is recommened to set the maxResults less than
            10,000 to get better performance. The allowed maximum is 50_000.

        .. note:: The response of this request includes a 'totalHits' response parameter
            that indicates the total number of scenes that match the search query to allow for
            pagination.

        .. note:: The argument dataset_name can be given by datasetAlias.

        .. note:: starting_number is 1-indexed

        :param entity_id: Used to identify the scene to find related scenes for
        :type entity_id: str
        :param dataset_name: Used to identify the dataset to search
        :type dataset_name: str
        :param max_results: How many results should be returned ?, defaults to 100
        :type max_results: int, optional
        :param starting_number: Used to identify the start number to search from, defaults to None
        :type starting_number: Optional[int], optional
        :param metadata_type: If populated, identifies which metadata to return (summary or full), defaults to None
        :type metadata_type: Optional[str], optional
        :param sort_filed: Determines which field to sort the results on, defaults to None
        :type sort_filed: Optional[str], optional
        :param sort_direction: Determines how the results should be sorted, defaults to None
        :type sort_direction: Optional[Literal["ASC", "DESC"]], optional
        :param compare_list_name: If provided, defined a scene-list listId to use to track scenes selected for comparison, defaults to None
        :type compare_list_name: Optional[str], optional
        :param bulk_list_name: If provided, defined a scene-list listId to use to track scenes selected for bulk ordering, defaults to None
        :type bulk_list_name: Optional[str], optional
        :param order_list_name: If provided, defined a scene-list listId to use to track scenes selected for on-demand ordering, defaults to None
        :type order_list_name: Optional[str], optional
        :param exlucde_list_name: If provided, defined a scene-list listId to use to exclude scenes from the results, defaults to None
        :type exlucde_list_name: Optional[str], optional
        :return: Dictionary containing search results for related scenes as List[Dict] together with some additional search meatadata
        :rtype: Dict

        :raise HTTPError:
        """
        # TODO continue with examples
        payload = {
            "entityId": entity_id,
            "datasetName": dataset_name,
            "maxResults": max_results,
            "startingNumber": starting_number,
            "metadataType": metadata_type,
            "sortField": sort_filed,
            "sortDirection": sort_direction,
            "compareListName": compare_list_name,
            "bulkListName": bulk_list_name,
            "orderListName": order_list_name,
            "excludeListName": exlucde_list_name,
        }
        result = self._call_post("scene-search-secondary", data=dumps(payload, default=vars))

        return result["data"]

    def user_preferences_get(
        self, system_id: Optional[str] = None, setting: Optional[List[str]] = None
    ) -> Dict:
        """
        This method is used to retrieve user's preference settings.

        :param system_id: Used to identify which system to return preferences for. If null it will return all the users preferences, defaults to None
        :type system_id: Optional[str], optional
        :param setting: If populated, identifies which setting(s) to return, defaults to None
        :type setting: Optional[List[str]], optional
        :return: Dict containing, possibly subset, preferences of calling user
        :rtype: Dict

        :raises HTTPError:
        """
        payload = {"systemId": system_id, "setting": setting}
        result = self._call_post("user-preferences-get", data=dumps(payload, default=vars))

        return result["data"]

    def user_preferences_set(
        self, system_id: Optional[str] = None, user_preferences: Optional[List[str]] = None
    ) -> None:
        """
        This method is used to create or update user's preferences.

        :param system_id: Used to identify which system the preferences are for, defaults to None
        :type system_id: Optional[str], optional
        :param user_preferences: Used to set user preferences for various systems, defaults to None
        :type user_preferences: Optional[List[str]], optional

        :raises HTTPError:

        :Example:

        preferences = {
             "userPreferences": {
                "map": {
                    "lat": "43.53",
                    "lng": "-96.73",
                    "showZoom": false,
                    "showMouse": true,
                    "zoomLevel": "7",
                    "defaultBasemap": "OpenStreetMap"
                },
                "browse": {
                    "browseSize": "10",
                    "selectedOpacity": "100",
                    "nonSelectedOpacity": "100"
                },
                "general": {
                    "defaultDataset": "gls_all",
                    "codiscoveryEnabled": false
                }
        }

        Api.user_preferences_set("EE", preferences)
        """
        # TODO N° 2
        payload = {"systemId": system_id, "userPreferences": user_preferences}
        _ = self._call_post("user-preferences-set", data=dumps(payload, default=vars))

        return
