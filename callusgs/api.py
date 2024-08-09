"""
API Class representing USGS's machine-to-machine API: https://m2m.cr.usgs.gov/api/docs/reference/
"""

from pathlib import Path
from typing import Optional, Any, Dict, List, Literal, Union
from datetime import datetime
from json import loads, dumps
import logging
import os
from urllib.parse import unquote
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
    DownloadInput,
    FilepathDownload,
    FilegroupDownload,
    ApiResponse,
    ProductInput,
)
from callusgs.errors import (
    AuthenticationEarthExplorerException,
    GeneralEarthExplorerException,
    RateLimitEarthExplorerException,
)

api_logger = logging.getLogger("callusgs.api")


class Api:
    ENDPOINT: str = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    def __init__(
        self,
        relogin: bool = True,
        method: Optional[str] = "token",
        user: Optional[str] = None,
        auth: Optional[str] = None,
    ) -> None:
        self.key: Optional[str] = None
        self.login_timestamp: Optional[datetime] = None
        self.headers: Dict[str, str] = {"Content-type": "application/json"}
        self.relogin = relogin
        self.login_method = method
        self.user = user
        self.auth = auth
        self.logger = logging.getLogger("callusgs.api.Api")
        self.logger.setLevel(logging.DEBUG)
        self.last_request = None

    def __enter__(self) -> "Api":
        self.logger.debug("Entering context manager")
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
        self.logger.debug("Exiting context manager")
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
        self.last_request = datetime.now()
        r = requests.get(url, headers=self.headers, stream=stream, timeout=1200)

        if r.status_code == 429:
            raise RateLimitEarthExplorerException
        else:
            r.raise_for_status()

        return r

    def _call_post(
        self,
        endpoint: str,
        conversion: Optional[Literal["text", "binary"]] = "text",
        /,
        **kwargs,
    ) -> ApiResponse:
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
        :rtype: ApiResponse
        """
        SECONDS_PER_HOUR: int = 3600
        if (
            self.login_timestamp is not None
            and (datetime.now() - self.last_request).total_seconds()
            >= SECONDS_PER_HOUR * 2
        ):
            if not self.relogin:
                raise AuthenticationEarthExplorerException(
                    "Two hours have passed since the last request, api session token expired. Please login again!"
                )

            self.logger.warning(
                "Maximum API conncetion time after inactivity reached. Trying to reconnect..."
            )
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
            self.logger.warning("Successfully reconnected")

        with requests.post(
            Api.ENDPOINT + endpoint, headers=self.headers, timeout=1200, **kwargs
        ) as r:
            self.logger.debug(f"Post request to {Api.ENDPOINT + endpoint}")
            self.last_request = datetime.now()
            if conversion == "text":
                message_content: ApiResponse = ApiResponse(**loads(r.text))
            elif conversion == "binary":
                message_content: ApiResponse = ApiResponse(**loads(r.content))
            else:
                raise AttributeError(
                    f"conversion paramter must be either 'text' or 'binary'. Got {conversion}."
                )

            if message_content.error_code is not None:
                message_content.raise_status()
            else:
                _ = r.raise_for_status()

        return message_content

    def data_owner(self, data_owner: str) -> ApiResponse:
        """
        This method is used to provide the contact information of the data owner.

        :param data_owner: Used to identify the data owner - this value comes from the dataset-search response
        :type data_owner: str
        :return: Dict containing contact information
        :rtype: ApiResponse
        """
        payload: Dict = {"dataOwner": data_owner}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("data-owner", data=post_payload)

    def dataset(
        self, dataset_id: Optional[str] = None, dataset_name: Optional[str] = None
    ) -> ApiResponse:
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
        :rtype: ApiResponse
        """
        if dataset_id is None and dataset_name is None:
            raise AttributeError("Not both dataset_id and dataset_name can be None")

        payload: Dict = {"datasetId": dataset_id, "datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset", data=post_payload)

    def dataset_browse(self, dataset_id: str) -> ApiResponse:
        """
        This request is used to return the browse configurations for the specified dataset.

        :param dataset_id: Determines which dataset to return browse configurations for
        :type dataset_id: str
        :return: List of Dicts, each containing information about configuration of subdatasets
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetId": dataset_id}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-browse", data=post_payload)

    def dataset_bulk_products(self, dataset_name: Optional[str] = None) -> ApiResponse:
        """
        Lists all available bulk products for a dataset - this does not guarantee scene availability.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param dataset_name: Used to identify the which dataset to return results for, defaults to None
        :type dataset_name: Optional[str], optional
        :return: List of dictionaries containing bulk download information
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-bulk-products", data=post_payload)

    def dataset_catalogs(self) -> ApiResponse:
        """
         This method is used to retrieve the available dataset catalogs.
         The use of dataset catalogs are not required, but are used to group datasets by
         their use within our web applications.

        :return: Dictionary with all available data catalogs
        :rtype: ApiResponse
        """
        return self._call_post("dataset-catalogs")

    def dataset_categories(
        self,
        catalog: Optional[str] = None,
        include_message: Optional[bool] = None,
        public_only: Optional[bool] = None,
        use_customization: Optional[bool] = None,
        parent_id: Optional[str] = None,
        dataset_filter: Optional[str] = None,
    ) -> ApiResponse:
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
        :rtype: ApiResponse
        """
        payload: Dict = {
            "catalog": catalog,
            "includeMessage": include_message,
            "publicOnly": public_only,
            "useCustomization": use_customization,
            "parentId": parent_id,
            "datasetFilter": dataset_filter,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-categories", data=post_payload)

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
        payload: Dict = {
            "datasetName": dataset_name,
            "metadataType": metadata_type,
            "fileGroupIds": file_group_ids,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("dataset-clear-customization", data=post_payload)

        if result.data != 1:
            raise GeneralEarthExplorerException("Value of data section is not 1")

    def dataset_coverage(self, dataset_name: str) -> ApiResponse:
        """
        Returns coverage for a given dataset.

        :param dataset_name: Determines which dataset to return coverage for
        :type dataset_name: str
        :return: Bounding box and GeoJSON coverage
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-coverage", data=post_payload)

    def dataset_download_options(
        self, dataset_name: str, scene_filter: Optional[SceneFilter] = None
    ) -> ApiResponse:
        """
        This request lists all available products for a given dataset.

        .. warning:: Product listed here does not guarantee scene availability!

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param dataset_name: Used to identify the which dataset to return results for
        :type dataset_name: str
        :param scene_filter: Used to filter data within the dataset, defaults to None
        :type scene_filter: Optional[SceneFilter], optional
        :return: List of available products
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetName": dataset_name, "sceneFilter": scene_filter}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-download-options", data=post_payload)

    def dataset_file_groups(self, dataset_name: str) -> ApiResponse:
        """
        This method is used to list all configured file groups for a dataset.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param dataset_name: Dataset alias
        :type dataset_name: str
        :return: Primary and secondary file group information
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-file-groups", data=post_payload)

    def dataset_filters(self, dataset_name: str) -> ApiResponse:
        """
        This request is used to return the metadata filter fields for the specified dataset. These values can be used as additional criteria when submitting search and hit queries.

        :param dataset_name: Determines which dataset to return filters for
        :type dataset_name: str
        :return: Dict with all related dataset fiters
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-filters", data=post_payload)

    def dataset_get_customization(self, dataset_name: str) -> ApiResponse:
        """
        This method is used to retrieve metadata customization for a specific dataset.

        :param dataset_name: Used to identify the dataset to search
        :type dataset_name: str
        :return: Dict containing customized metadata representations
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-get-customization", data=post_payload)

    def dataset_get_customizations(
        self,
        dataset_names: Optional[List[str]] = None,
        metadata_type: Optional[List[str]] = str,
    ) -> ApiResponse:
        """
        This method is used to retrieve metadata customizations for multiple datasets at once.

        :param dataset_names: Used to identify the dataset(s) to return. If null it will return all the users customizations, defaults to None
        :type dataset_names: Optional[List[str]], optional
        :param metadata_type: If populated, identifies which metadata to return(export, full, res_sum, shp), defaults to str
        :type metadata_type: Optional[List[str]], optional
        :return: Dict containing customized metadata representations for datasets, identified by their Ids
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetNames": dataset_names, "metadataType": metadata_type}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-get-customizations", data=post_payload)

    def dataset_messages(
        self,
        catalog: str,
        dataset_name: Optional[str] = None,
        dataset_names: Optional[List[str]] = None,
    ) -> ApiResponse:
        """
        Returns any notices regarding the given datasets features.

        :param catalog: Used to identify datasets that are associated with a given application
        :type catalog: str
        :param dataset_name: Used as a filter with wildcards inserted at the beginning and the end of the supplied value, defaults to None
        :type dataset_name: Optional[str], optional
        :param dataset_names: Used as a filter with wildcards inserted at the beginning and the end of the supplied value, defaults to None
        :type dataset_names: Optional[List[str]], optional
        :return: Dict containing notices per dataset supplied
        :rtype: ApiResponse
        """
        payload: Dict = {
            "catalog": catalog,
            "datasetName": dataset_name,
            "datasetNames": dataset_names,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-messages", data=post_payload)

    def dataset_metadata(self, dataset_name: str) -> ApiResponse:
        """
        This method is used to retrieve all metadata fields for a given dataset.

        :param dataset_name: The system-friendly dataset name
        :type dataset_name: str
        :return: All metadata for given dataset
        :rtype: ApiResponse
        """
        payload: Dict = {"datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-metadata", data=post_payload)

    def dataset_order_products(self, dataset_name: str) -> ApiResponse:
        """
        Lists all available order products for a dataset.

        .. warning:: Product listed here does not guarantee scene availability!

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param dataset_name: Used to identify the which dataset to return results for
        :type dataset_name: str
        :return: List of all products available for given dataset name
        :rtype: ApiResponse

        :Example:

        Api.dataset_order_products("landsat_ot_c2_l2")

        # [
        #    {
        #        "productCode": "LO220",
        #        "productName": "L8-9 Collection 2 Level 1 and Level 2 Std Products from Level 0 input"
        #    },
        #    {
        #        "productCode": "LO221",
        #        "productName": "L8-9 Collection 2 Level 2 Std product from Level 1 input"
        #    },
        #    ...,
        # ]
        """
        payload: Dict = {"datasetName": dataset_name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-order-products", data=post_payload)

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
    ) -> ApiResponse:
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
        :rtype: ApiResponse

        :Example:

        Api().dataset_search("EE", "dataset_name="Collection 2 Level-1")
        """
        payload: Dict = {
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
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("dataset-search", data=post_payload)

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
        payload: Dict = {
            "datasetName": dataset_name,
            "excluded": excluded,
            "metadata": metadata,
            "searchSort": search_sort,
            "fileGroups": file_groups,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("dataset-set-customization", data=post_payload)

        if result.data != 1:
            raise GeneralEarthExplorerException("Value of data section is not 1")

    def dataset_set_customizations(
        self, dataset_customization: DatasetCustomization
    ) -> None:
        """
        This method is used to create or update customizations for multiple datasets at once.

        :param dataset_customization: Used to create or update a dataset customization for multiple datasets
        :type dataset_customization: DatasetCustomization
        :raises GeneralEarthExplorerException:
        """
        payload: Dict = {"datasetCustomization": dataset_customization}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("dataset-set-customizations", data=post_payload)

        if result.data != 1:
            raise GeneralEarthExplorerException("Value of data section is not 1")

    def download_complete_proxied(
        self, proxied_downloads: List[ProxiedDownload]
    ) -> ApiResponse:
        """
        Updates status to 'C' with total downloaded file size for completed proxied downloads.

        :param proxied_downloads: Used to specify multiple proxied downloads
        :type proxied_downloads: List[ProxiedDownload]
        :return: Dict containing number of failed downloads and number of statuses updated
        :rtype: ApiResponse
        """
        payload: Dict = {"proxiedDownloads": proxied_downloads}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-complete-proxied", data=post_payload)

    def download_eula(
        self, eula_code: Optional[str] = None, eula_codes: Optional[List[str]] = None
    ) -> ApiResponse:
        """
        Gets the contents of a EULA from the eulaCodes.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param eula_code: Used to specify a single eula, defaults to None
        :type eula_code: Optional[str], optional
        :param eula_codes: Used to specify multiple eulas, defaults to None
        :type eula_codes: Optional[List[str]], optional
        :return: List of EULAs
        :rtype: ApiResponse
        """
        payload: Dict = {"eulaCode": eula_code, "eulaCodes": eula_codes}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-eula", data=post_payload)

    def download_labels(
        self, download_application: Optional[str] = None
    ) -> ApiResponse:
        # TODO 4
        """
        Gets a list of unique download labels associated with the orders.

        :param download_application: Used to denote the application that will perform the download, defaults to None
        :type download_application: Optional[str], optional
        :return: Information about all valid(?) download orders ['label', 'dateEntered', 'downloadSize', 'downloadCount', 'totalComplete']
        :rtype: ApiResponse
        """
        payload: Dict = {"downloadApplication": download_application}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-labels", data=post_payload)

    def download_options(
        self,
        dataset_name: str,
        entity_ids: Optional[Union[str, List[str]]] = None,
        list_id: Optional[str] = None,
        include_secondary_file_groups: Optional[bool] = None,
    ) -> ApiResponse:
        """
        The download options request is used to discover downloadable products for each dataset. If a download is marked as not available, an order must be placed to generate that product.

        .. note:: "listId" is the id of the customized list which is built by scene-list-add.
            The parameter entityIds can be either a string array or a string. If passing them in a string, separate them by comma (no space between the IDs).
            If passing them in the test page, use string without quotes/spaces/brackets, just pass entityIds with commas, for example,
            LT50290302005219EDC00,LE70820552011359EDC00

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param dataset_name: Dataset alias
        :type dataset_name: str
        :param entity_ids: List of scenes, defaults to None
        :type entity_ids: Optional[Union[str, List[str]]], optional
        :param list_id: Used to identify the list of scenes to use, defaults to None
        :type list_id: Optional[str], optional
        :param include_secondary_file_groups: Optional parameter to return file group IDs with secondary products, defaults to None
        :type include_secondary_file_groups: Optional[bool], optional
        :return: List of all available download options for a given datset
        :rtype: ApiResponse
        """
        payload: Dict = {
            "datasetName": dataset_name,
            "entityIds": entity_ids,
            "listId": list_id,
            "includeSecondaryFileGroups": include_secondary_file_groups,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-options", data=post_payload)

    def download_order_load(
        self, download_application: Optional[str] = None, label: Optional[str] = None
    ) -> ApiResponse:
        # TODO how do I get the label of an order? There's is download-order in one of the examples, but is this correct?
        """
        This method is used to prepare a download order for processing by moving the scenes into the queue for processing.

        .. note:: label must be label of order.

        :param download_application: Used to denote the application that will perform the download, defaults to None
        :type download_application: Optional[str], optional
        :param label: Determines which order to load, defaults to None
        :type label: Optional[str], optional
        :return: Metadata for specified orders given by labels
        :rtype: ApiResponse
        """
        payload: Dict = {"downloadApplication": download_application, "label": label}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-order-load", data=post_payload)

    def download_order_remove(
        self,
        label: str,
        download_application: Optional[str] = None,
    ) -> None:
        """
        This method is used to remove an order from the download queue.

        :param download_application: Used to denote the application that will perform the download
        :type download_application: str
        :param label: Determines which order to remove, defaults to None
        :type label: Optional[str], optional
        :raises GeneralEarthExplorerException:
        """
        payload: Dict = {"downloadApplication": download_application, "label": label}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        _ = self._call_post("download-order-remove", data=post_payload)

    def download_remove(self, download_id: int) -> None:
        """
        Removes an item from the download queue.

        .. note:: "downloadId" can be retrieved by calling download-search.

        :param download_id: Represents the ID of the download from within the queue
        :type download_id: int
        :raises GeneralEarthExplorerException:
        """
        payload: Dict = {"downloadId": download_id}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("download-remove", data=post_payload)

        if result.data is not True:
            raise GeneralEarthExplorerException("Removal returned False")

    def download_request(
        self,
        configuration_code: Optional[
            Literal["no_data", "test", "order", "order+email", "null"]
        ] = None,
        download_application: Optional[str] = "M2M",
        downloads: Optional[List[DownloadInput]] = None,
        data_paths: Optional[List[FilepathDownload]] = None,
        label: Optional[str] = None,
        system_id: Optional[str] = "M2M",
        data_groups: Optional[List[FilegroupDownload]] = None,
    ) -> ApiResponse:
        """
        This method is used to insert the requested downloads into the download queue and returns the available download URLs.

        Each ID supplied in the downloads parameter you provide will be returned in one of three elements:

            - availableDownloads: URLs provided in this list are immediately available; note that these URLs take you to other distribution systems that may require authentication
            - preparingDownloads: IDs have been accepted but the URLs are NOT YET available for use
            - failed: IDs were rejected; see the errorMessage field for an explanation

        Other information is also provided in the response:

            - newRecords: Includes a downloadId for each element of the downloads parameter that was accepted and a label that applies to the whole request
            - duplicateProducts: Requests that duplicate previous requests by the same user; these are not re-added to the queue and are not included in newRecords
            - numInvalidScenes: The number of products that could not be found by ID or failed to be requested for any reason
            - remainingLimits: The number of remaining downloads to hit the rate limits by user and IP address
                - limitType: The type of the limits are counted by, the value is either 'user' or 'ip'
                - username: The user name associated with the request
                - ipAddress: The IP address associated with the request
                - recentDownloadCount: The number of downloads requested in the past 15 minutes
                - pendingDownloadCount: The number of downloads in pending state before they are available for download
                - unattemptedDownloadCount: The number of downloads in available status but the user has not downloaded yet


        .. warning:: This API may be online while the distribution systems are unavailable. When this occurs, you will recieve the following error when requesting products that belong to any of these systems: 'This download has been temporarily disabled. Please try again at a later time. We apologize for the inconvenience.'. Once the distribution system is back online, this error will stop occuring and download requests will succeed.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param configuration_code: Used to customize the the download routine, primarily for testing, defaults to None
        :type configuration_code: Optional[Literal["no_data", "test", "order", "order+email", "null"]], optional
        :param download_application: Used to denote the application that will perform the download. Internal use only!, defaults to "M2M"
        :type download_application: Optional[str], optional
        :param downloads: Used to identify higher level products that this data may be used to create, defaults to None
        :type downloads: Optional[List[DownloadInput]], optional
        :param data_paths: Used to identify products by data path, specifically for internal automation and DDS functionality, defaults to None
        :type data_paths: Optional[List[FilepathDownload]], optional
        :param label: If this value is passed it will overide all individual download label values, defaults to None
        :type label: Optional[str], optional
        :param system_id: Identifies the system submitting the download/order. Internal use only!, defaults to None
        :type system_id: Optional[str], optional
        :param data_groups: Identifies the products by file groups, defaults to None
        :type data_groups: Optional[List[FilegroupDownload]], optional
        :raises ValueError: When download_application or system_id do not equal "M2M.
        :return: Dict of available downloads, downloads in prepration and failed requests
        :rtype: ApiResponse
        """
        if download_application != "M2M" or system_id != "M2M":
            raise ValueError("download_application and system_id must have value 'M2M'")

        payload: Dict = {
            "configurationCode": configuration_code,
            "downloadApplication": download_application,
            "downloads": downloads,
            "dataPaths": data_paths,
            "label": label,
            "systemId": system_id,
            "dataGroups": data_groups,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-request", data=post_payload)

    def download_retrieve(
        self, download_application: Optional[str] = None, label: Optional[str] = None
    ) -> ApiResponse:
        """
        Returns all available and previously requests but not completed downloads.

        .. warning:: This API may be online while the distribution systems are unavailable. When this occurs, the downloads being fulfilled by those systems will not appear as available nor are they counted in the 'queueSize' response field.

        :param download_application: Used to denote the application that will perform the download, defaults to None
        :type download_application: Optional[str], optional
        :param label: Determines which downloads to return, defaults to None
        :type label: Optional[str], optional
        :return: Dict with EULAs, List of available downloads (['url', 'label', 'entityId', 'eulaCode', 'filesize' 'datasetId', 'displayId', 'downloadId', 'statusCode', 'statusText', 'productCode', 'productName', 'collectionName']), queue size and requested downloads
        :rtype: ApiResponse
        """
        payload: Dict = {"downloadApplication": download_application, "label": label}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-retrieve", data=post_payload)

    def download_search(
        self,
        active_only: Optional[bool] = None,
        label: Optional[str] = None,
        download_application: Optional[str] = None,
    ) -> ApiResponse:
        """
        This method is used to search for downloads within the queue, regardless of status, that match the given label.

        :param active_only: Determines if completed, failed, cleared and proxied downloads are returned, defaults to None
        :type active_only: Optional[bool], optional
        :param label: Used to filter downloads by label, defaults to None
        :type label: Optional[str], optional
        :param download_application: Used to filter downloads by the intended downloading application, defaults to None
        :type download_application: Optional[str], optional
        :return: All download orders according to filters (['label', 'entityId', 'eulaCode', 'filesize' 'datasetId', 'displayId', 'downloadId', 'statusCode', 'statusText', 'productCode', 'productName', 'collectionName'])
        :rtype: ApiResponse
        """
        payload: Dict = {
            "acitveOnly": active_only,
            "label": label,
            "downloadApplication": download_application,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-search", data=post_payload)

    def download_summary(
        self, download_application: str, label: str, send_email: Optional[bool]
    ) -> ApiResponse:
        """
        Gets a summary of all downloads, by dataset, for any matching labels.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param download_application: Used to denote the application that will perform the download
        :type download_application: str
        :param label: Determines which downloads to return
        :type label: str
        :param send_email: If set to true, a summary email will also be sent
        :type send_email: Optional[bool]
        :return: Information about downloaded files
        :rtype: ApiResponse
        """
        payload: Dict = {
            "downloadApplication": download_application,
            "label": label,
            "sendEmail": send_email,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("download-search", data=post_payload)

    def download(
        self,
        url: str,
        output_directory: Optional[Path] = Path("."),
        chunk_size: int = 1024,
        no_progess: Optional[bool] = False,
    ) -> None:
        result = self._call_get(url)

        file_name = unquote(
            result.headers["content-disposition"].split("filename=").pop().strip('"')
        )
        download_size = int(result.headers["content-length"])

        if not output_directory.exists():
            output_directory.mkdir()

        with (
            open(output_directory / file_name, "wb") as f,
            tqdm(
                desc=file_name,
                total=download_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                leave=False,
                disable=no_progess,
            ) as bar,
        ):
            for chunk in result.iter_content(chunk_size=chunk_size):
                bytes_written = f.write(chunk)
                bar.update(bytes_written)

        result.close()

        if download_size != os.path.getsize(output_directory / file_name):
            raise RuntimeError(
                "Downloaded file has not the same size on disk as was promised by USGS"
            )

    def grid2ll(
        self,
        grid_type: Optional[Literal["WRS1", "WRS2"]] = "WRS2",
        response_shape: Optional[Literal["polygon", "point"]] = None,
        path: Optional[str] = None,
        row: Optional[str] = None,
    ) -> ApiResponse:
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
        :rtype: ApiResponse
        """
        payload: Dict = {
            "gridType": grid_type,
            "responseShape": response_shape,
            "path": path,
            "row": row,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("grid2ll", data=post_payload)

    def login(self, username: str, password: str, user_context: Any = None):
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
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("login", data=post_payload)

        self.user = username
        self.auth = password
        self.key = result.data
        self.login_timestamp = datetime.now()
        self.headers.update({"X-Auth-Token": self.key})

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
        payload: Dict = {
            "application_token": application_token,
            "user_token": user_token,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("login-app-guest", data=post_payload)

        self.user = application_token
        self.auth = user_token
        self.key = result.data
        self.login_timestamp = datetime.now()
        self.headers.update({"X-Auth-Token": self.key})

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
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("login-token", data=post_payload)

        self.user = username
        self.auth = token
        self.key = result.data
        self.login_timestamp = datetime.now()
        self.headers.update({"X-Auth-Token": self.key})

    def logout(self) -> None:
        """
        This method is used to remove the users API key from being used in the future.
        :raises HTTPError:
        """
        with requests.post(Api.ENDPOINT + "logout", headers=self.headers) as r:
            self.logger.debug("Logging out")
            _ = r.raise_for_status()
        self.key = None
        self.headers = None
        self.login_timestamp = None

    def notifications(self, system_id: str) -> ApiResponse:
        """
        Gets a notification list.

        :param system_id: Used to identify notifications that are associated with a given application
        :type system_id: str
        :return: List of all notifications
        :rtype: ApiResponse
        """
        payload: Dict = {"systemId": system_id}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("notifications", data=post_payload)

    def order_products(
        self,
        dataset_name: str,
        entity_ids: Optional[List[str]] = None,
        list_id: Optional[str] = None,
    ) -> ApiResponse:
        """
        Gets a list of currently selected products - paginated.

        .. note:: "listId" is the id of the customized list which is built by scene-list-add.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param dataset_name: Dataset alias
        :type dataset_name: str
        :param entity_ids: List of scenes, defaults to None
        :type entity_ids: Optional[List[str]], optional
        :param list_id: Used to identify the list of scenes to use, defaults to None
        :type list_id: Optional[str], optional
        :return: Information about selected products (i.e. id, price, entityId, availability, datasetId, productCode and productName)
        :rtype: ApiResponse
        """
        payload: Dict = {
            "datasetName": dataset_name,
            "entityIds": entity_ids,
            "list_id": list_id,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("order-products", data=post_payload)

    def order_submit(
        self,
        products: List[ProductInput],
        auto_bulk_order: Optional[bool] = None,
        processing_parameters: Optional[str] = None,
        priority: Optional[int] = None,
        order_comment: Optional[str] = None,
        system_id: Optional[str] = None,
    ) -> ApiResponse:
        """
        Submits the current product list as a TRAM order - internally calling tram-order-create.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param products: Used to identify higher level products that this data may be used to create
        :type products: List[Product]
        :param auto_bulk_order: If any products can be bulk ordered as a result of completed processing this option allows users to have orders automatically submitted, defaults to None
        :type auto_bulk_order: Optional[bool], optional
        :param processing_parameters: Optional processing parameters to send to the processing system, defaults to None
        :type processing_parameters: Optional[str], optional
        :param priority: Processing Priority, defaults to None
        :type priority: Optional[int], optional
        :param order_comment: Optional textual identifier for the order, defaults to None
        :type order_comment: Optional[str], optional
        :param system_id: Identifies the system submitting the order, defaults to None
        :type system_id: Optional[str], optional
        :return: Information about successfull (orderNumber) and failed orders
        :rtype: ApiResponse
        """
        payload: Dict = {
            "products": products,
            "autoBulkOrder": auto_bulk_order,
            "processingParameters": processing_parameters,
            "priority": priority,
            "orderComment": order_comment,
            "systemId": system_id,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("order-submit", data=post_payload)

    def permissions(self) -> ApiResponse:
        """
        Returns a list of user permissions for the authenticated user.
        This method does not accept any input.

        :return: List of user permissions
        :rtype: List[str]
        """
        return self._call_post("permissions")

    def placename(
        self,
        feature_type: Optional[Literal["US", "World"]] = None,
        name: Optional[str] = None,
    ) -> ApiResponse:
        """
        Geocoder

        :param feature_type: Type of feature - see type hint, defaults to None
        :type feature_type: Optional[Literal["US", "World"]], optional
        :param name: Name of the feature, defaults to None
        :type name: Optional[str], optional
        :return: Return list of dictionaries for matched places.
            Dictionary keys are: ['id', 'feature_id', 'placename', 'feature_code', 'country_code',
            'latitude', 'longitude', 'feature_name', 'country_name'].
        :rtype: ApiResponse
        :raises HTTPError:
        """
        # TODO convert result dicts to class instances of class Place; depend on method argument if this should
        #  be done
        payload: Dict = {"featureType": feature_type, "name": name}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("placename", data=post_payload)

    def rate_limit_summary(self, ip_address: Optional[List[str]] = None) -> ApiResponse:
        """
        Returns download rate limits and how many downloads are in each status as well as how close the user is to reaching the rate limits

        Three elements are provided in the response:

            - initialLimits: Includes the initial downloads rate limits
                - recentDownloadCount: The maximum number of downloads requested in the past 15 minutes
                - pendingDownloadCount: The maximum number of downloads in pending state before they are available for download
                - unattemptedDownloadCount: The maximum number of downloads in available status but the user has not downloaded yet
            - remainingLimits: Includes downloads that are currently remaining and count towards the rate limits. Users should be watching out for any of those numbers approaching 0 which means it is close to hitting the rate limits
                - limitType: The type of the limits are counted by, the value is either 'user' or 'ip'
                - username: The user name associated with the request
                - ipAddress: The IP address associated with the request
                - recentDownloadCount: The number of downloads requested in the past 15 minutes
                - pendingDownloadCount: The number of downloads in pending state before they are available for download
                - unattemptedDownloadCount: The number of downloads in available status but the user has not downloaded yet
            - recentDownloadCounts: Includes the downloads count in each status for the past 15 minutes
                - countType: The type of the download counts are calculated by, the value is either 'user' or 'ip'
                - username: The user name associated with the request
                - ipAddress: The IP address associated with the request
                - downloadCount: The number of downloads per status in the past 15 minutes

        .. warning:: Users should be watching out for any of the `remainingLimits` numbers approaching 0 which means it is close to hitting the rate limits.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        .. warning:: This API may be online while the distribution systems are unavailable. When this occurs, you will recieve the following error when requesting products that belong to any of these systems: 'This download has been temporarily disabled. Please try again at a later time. We apologize for the inconvenience.'. Once the distribution system is back online, this error will stop occuring and download requests will succeed.

        :param ip_address: Used to specify multiple IP address, defaults to None
        :type ip_address: Optional[List[str]], optional
        :return: Rate Limit stats
        :rtype: ApiResponse
        """
        payload: Dict = {"ipAddress": ip_address}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("rate-limit-summary", data=post_payload)

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
        payload: Dict = {
            "listId": list_id,
            "datasetName": dataset_name,
            "idField": id_field,
            "entityId": entity_id if entity_ids is None else None,
            "entityIds": entity_ids,
            "timeToLive": ttl,
            "checkDownloadRestriction": check_download_restriction,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        result = self._call_post("scene-list-add", data=post_payload)

        items_to_add: int = 1 if entity_ids is None else len(entity_ids)
        if result.data != items_to_add:
            raise RuntimeError(
                f"Number of scenes added {result.data} does not equal provided number of scenes {items_to_add}"
            )

    def scene_list_get(
        self,
        list_id: str,
        dataset_name: Optional[str] = None,
        starting_number: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> ApiResponse:
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
        :rtype: ApiResponse
        :raises HTTPError:

        :Example:

        Api.scene_list_get(list_id="my_scene_list")
        """
        payload: Dict = {
            "listId": list_id,
            "datasetName": dataset_name,
            "startingNumber": starting_number,
            "maxResults": max_results,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-list-get", data=post_payload)

    def scene_list_remove(
        self,
        list_id: str,
        dataset_name: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
    ) -> None:
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
        payload: Dict = {
            "listId": list_id,
            "datasetName": dataset_name,
            "entityId": entity_id,
            "entityIds": entity_ids,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        _ = self._call_post("scene-list-remove", data=post_payload)

    def scene_list_summary(
        self, list_id: str, dataset_name: Optional[str] = None
    ) -> ApiResponse:
        """
        Returns summary information for a given list.

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias, defaults to None
        :type dataset_name: Optional[str], optional
        :return: Dictionary containing a summary and datasets ({'summary', 'datasets'}).
        :rtype: ApiResponse
        :raises HTTPError:
        """
        payload: Dict = {
            "listId": list_id,
            "datasetName": dataset_name,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-list-summary", data=post_payload)

    def scene_list_types(self, list_filter: Optional[str]) -> ApiResponse:
        """
        Returns scene list types (exclude, search, order, bulk, etc).

        :param list_filter: If provided, only returns listIds that have the provided filter value within the ID
        :type list_filter: Optional[str]
        :return: List of scene list, each containing a dictionary describing a scene list.
        :rtype: ApiResponse
        """
        # TODO list_filter would likely have to be the result of the MetadataFilter types, no?
        payload: Dict = {"listFilter": list_filter}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-list-types", data=post_payload)

    def scene_metadata(
        self,
        dataset_name: str,
        entity_id: str,
        id_type: Optional[str] = "entityId",
        metadata_type: Optional[str] = None,
        include_null_metadata: Optional[bool] = None,
        use_customization: Optional[bool] = None,
    ) -> ApiResponse:
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
        :rtype: ApiResponse

        :raises HTTPError:
        """
        payload: Dict = {
            "datasetName": dataset_name,
            "entityId": entity_id,
            "idType": id_type,
            "metadataType": metadata_type,
            "includeNullMetadataValues": include_null_metadata,
            "useCustomization": use_customization,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-metadata", data=post_payload)

    def scene_metadata_list(
        self,
        list_id: str,
        dataset_name: Optional[str] = None,
        metadata_type: Optional[str] = None,
        include_null_metadata: Optional[bool] = None,
        use_customization: Optional[bool] = None,
    ) -> ApiResponse:
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
        :rtype: ApiResponse
        """
        payload: Dict = {
            "datasetName": dataset_name,
            "listId": list_id,
            "metadataType": metadata_type,
            "includeNullMetadataValues": include_null_metadata,
            "useCustomization": use_customization,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-metadata-list", data=post_payload)

    def scene_metadata_xml(
        self, dataset_name: str, entity_id: str, metadata_type: Optional[str] = None
    ) -> ApiResponse:
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
        :rtype: ApiResponse

        :raises HTTPError:
        """
        payload: Dict = {
            "datasetName": dataset_name,
            "entityId": entity_id,
            "metadataType": metadata_type,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-metadata-list", data=post_payload)

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
    ) -> ApiResponse:
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
        :rtype: ApiResponse

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
        payload: Dict = {
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
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-search", data=post_payload)

    def scene_search_delete(
        self,
        dataset_name: str,
        max_results: int = 100,
        starting_number: Optional[int] = None,
        sort_field: Optional[str] = None,
        sort_direction: Optional[Literal["ASC", "DEC"]] = None,
        temporal_filter: Optional[TemporalFilter] = None,
    ) -> ApiResponse:
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
        :rtype: ApiResponse

        :raises HTTPError:
        """
        payload: Dict = {
            "datasetName": dataset_name,
            "maxResults": max_results,
            "startingNumber": starting_number,
            "sortField": sort_field,
            "sortDirection": sort_direction,
            "temporalFilter": temporal_filter,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post(
            "scene-search-delete",
            post_payload,
            headers=self.headers,
        )

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
    ) -> ApiResponse:
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
        :rtype: ApiResponse

        :raise HTTPError:
        """
        # TODO continue with examples
        payload: Dict = {
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
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("scene-search-secondary", data=post_payload)

    def tram_order_detail_update(
        self, order_number: str, detail_key: str, detail_value: str
    ) -> ApiResponse:
        """
        This method is used to set metadata for an order.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param order_number: The order ID for the order to update
        :type order_number: str
        :param detail_key: The system detail key
        :type detail_key: str
        :param detail_value: The value to store under the detailKey
        :type detail_value: str
        :return: Updated key-value pair
        :rtype: ApiResponse
        """
        payload: Dict = {
            "orderNumber": order_number,
            "detailKey": detail_key,
            "detailValue": detail_value,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("tram-order-detail-update", data=post_payload)

    def tram_order_details(self, order_number: str) -> ApiResponse:
        """
        This method is used to view the metadata within an order.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param order_number: The order ID to get details for
        :type order_number: str
        :return: Metadata for order as dictionary
        :rtype: ApiResponse
        """
        payload: Dict = {"orderNumber": order_number}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("tram-order-details", data=post_payload)

    def tram_order_details_clear(self, order_number: str) -> ApiResponse:
        """
        This method is used to clear all metadata within an order.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param order_number: The order ID to clear details for
        :type order_number: str
        :return: Data section is Null
        :rtype: ApiResponse
        """
        payload: Dict = {"orderNumber": order_number}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("tram-order-details-clear", data=post_payload)

    def tram_order_details_remove(
        self, order_number: str, detail_key: str
    ) -> ApiResponse:
        """
        This method is used to remove the metadata within an order.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param order_number: The order ID to clear details for
        :type order_number: str
        :param detail_key: The system detail key
        :type detail_key: str
        :return: Previous value of deleted key
        :rtype: ApiResponse
        """
        payload: Dict = {"orderNumber": order_number, "detailKey": detail_key}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("tram-order-deatils-remove", data=post_payload)

    def tram_order_search(
        self,
        order_id: Optional[str] = None,
        max_results: Optional[int] = 25,
        system_id: Optional[str] = None,
        sort_asc: Optional[bool] = None,
        sort_field: Optional[
            Literal["order_id", "date_entered", "date_updated"]
        ] = None,
        status_filter: Optional[List[str]] = None,
    ) -> ApiResponse:
        """
        Search TRAM orders.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param order_id: The order ID to get status for (accepts '%' wildcard), defaults to None
        :type order_id: Optional[str], optional
        :param max_results: How many results should be returned on each page?, defaults to 25
        :type max_results: Optional[int], optional
        :param system_id: Limit results based on the application that order was submitted from, defaults to None
        :type system_id: Optional[str], optional
        :param sort_asc: True for ascending results, false for descending results, defaults to None
        :type sort_asc: Optional[bool], optional
        :param sort_field: Which field should sorting be done on?, defaults to None
        :type sort_field: Optional[Literal["order_id", "date_entered", "date_updated"]], optional
        :param status_filter: An array of status codes to..., defaults to None
        :type status_filter: Optional[List[str]], optional
        :return: List of order information
        :rtype: ApiResponse
        """
        payload: Dict = {
            "orderId": order_id,
            "maxResults": max_results,
            "systemId": system_id,
            "sortAsc": sort_asc,
            "sortField": sort_field,
            "statusFilter": status_filter,
        }
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("tram-order-search", data=post_payload)

    def tram_order_status(self, order_number: str) -> ApiResponse:
        """
        Gets the status of a TRAM order.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param order_number: The order ID to get status for
        :type order_number: str
        :return: Status for requested order
        :rtype: ApiResponse
        """
        payload: Dict = {"orderNumber": order_number}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("tram-order-status", data=post_payload)

    def tram_order_units(self, order_number: str) -> ApiResponse:
        """
        Lists units for a specified order.

        .. warning:: This method is only documented and accessible when having the MACHINE role assigned to your account.

        :param order_number: The order ID to get units for
        :type order_number: str
        :return: List of TRAM units
        :rtype: ApiResponse
        """
        payload: Dict = {"orderNumber": order_number}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("tram-order-units", data=post_payload)

    def user_preferences_get(
        self, system_id: Optional[str] = None, setting: Optional[List[str]] = None
    ) -> ApiResponse:
        """
        This method is used to retrieve user's preference settings.

        :param system_id: Used to identify which system to return preferences for. If null it will return all the users preferences, defaults to None
        :type system_id: Optional[str], optional
        :param setting: If populated, identifies which setting(s) to return, defaults to None
        :type setting: Optional[List[str]], optional
        :return: Dict containing, possibly subset, preferences of calling user
        :rtype: ApiResponse

        :raises HTTPError:
        """
        payload: Dict = {"systemId": system_id, "setting": setting}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        return self._call_post("user-preferences-get", data=post_payload)

    def user_preferences_set(
        self,
        system_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        This method is used to create or update user's preferences.

        :param system_id: Used to identify which system the preferences are for, defaults to None
        :type system_id: Optional[str], optional
        :param user_preferences: Used to set user preferences for various systems, defaults to None
        :type user_preferences: Optional[Dict[str]], optional

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
        payload: Dict = {"systemId": system_id, "userPreferences": user_preferences}
        post_payload = dumps(payload, default=vars)
        self.logger.debug(f"POST request body: {dumps(post_payload)}")

        _ = self._call_post("user-preferences-set", data=post_payload)
