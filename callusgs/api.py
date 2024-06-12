"""
API Class representing USGS's machine-to-machine API: https://m2m.cr.usgs.gov/api/docs/reference/
"""
from typing import Optional, Any, Dict, List, Literal
from datetime import datetime
from json import loads
import sys
import warnings
import requests

from callusgs.types import UserContext, SortCustomization, SceneFilter, TemporalFilter


class Api:
    ENDPOINT: str = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    def __init__(self) -> None:
        self.key: Optional[str] = None
        self.login_timestamp: Optional[datetime] = None
        self.headers: Dict[str, str] = None

    def _call_get(
        self, endpoint: str, conversion: Optional[Literal["text", "binary"]] = "text", /, **kwargs
    ) -> Dict:
        """
        Abstract method to call API endpoints

        :param endpoint: Endpoint to call
        :type endpoint: str
        :param conversion: How respinse should be interpreted, defaults to "text"
        :type conversion: Optional[Literal["text", "binary"]], optional
        :raises RuntimeError: If login is older than two hours, the api token used is not valid anymore
        :raises AttributeError: Paramter passed onto 'conversion' must be either 'text' or 'binary'
        :raises HTTPError:
        :return: Complete API response dictionary
        :rtype: Dict
        """
        if (datetime.now() - self.login_timestamp).hour >= 2:
            raise RuntimeError(
                "Two hours have passed since you logged in, api session token expired. Please login again!"
            )

        with requests.get(Api.ENDPOINT + endpoint, **kwargs) as r:
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

    def check_login_timestamp(self, *args, **kwargs) -> Any:
        pass

    def data_owner(self):
        pass

    def dataset(self):
        # Input datasetId or datasetName and get dataset description (including the respective other part)
        pass

    def dataset_browse(self):
        pass

    def dataset_catalogs(self):
        pass

    def dataset_categories(self):
        pass

    def dataset_clear_categories(self):
        pass

    def dataset_coverage(self):
        pass

    def dataset_filters(self):
        pass

    def dataset_get_customization(self):
        pass

    def dataset_get_customizations(self):
        pass

    def dataset_messages(self):
        pass

    def dataset_metadata(self):
        pass

    def dataset_search(self):
        # can be used to transfrom "natural language description" to datasetId
        pass

    def dataset_set_customization(self):
        pass

    def dataset_set_customizations(self):
        pass

    def download_complete_proxied(self):
        pass

    def download_labels(self):
        pass

    def download_order_load(self):
        pass

    def download_order_remove(self):
        pass

    def download_remove(self):
        pass

    def download_retrieve(self):
        pass

    def grid2ll(self):
        pass

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
        with requests.post(Api.ENDPOINT + "login", json=payload) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

            self.key = message_content["data"]
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
        with requests.post(Api.ENDPOINT + "login-app-guest", json=payload) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

            self.key = message_content["data"]
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
        with requests.post(Api.ENDPOINT + "login-token", json=payload) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

            self.key = message_content["data"]
            self.login_timestamp = datetime.now()
            self.headers = {"X-Auth-Token": self.key}

    def logout(self) -> None:
        """
        This method is used to remove the users API key from being used in the future.
        :raises HTTPError:
        """
        # TODO also call request.delete/close whatever it is. Can/should be bundled in _logout()
        with requests.post(Api.ENDPOINT + "logout", headers=self.headers) as r:
            _ = r.raise_for_status()
        self.key = None
        self.headers = None
        self.login_timestamp = None

    def notifications(self):
        pass

    def permissions(self) -> List[str]:
        """
        Returns a list of user permissions for the authenticated user.
        This method does not accept any input.

        :return: List of user permissions
        :rtype: List[str]
        :raises HTTPError:
        """
        with requests.get(Api.ENDPOINT + "permissions") as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

        return message_content["data"]

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
        with requests.get(Api.ENDPOINT + "placename", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

        return message_content["data"]["results"]

    def scene_list_add(
        self,
        list_id: str,
        dataset_name: str,
        id_field: Optional[Literal["entityId", "displayId"]] = "entityId",
        entity_id: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        ttl: Optional[str] = None,
        check_download_restriction: Optional[bool] = None,
    ):
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
            "listID": list_id,
            "datasetName": dataset_name,
            "idField": id_field,
            "entityId": entity_id if entity_ids is None else None,
            "entityIds": entity_ids,
            "timeToLive": ttl,
            "checkDownloadRestriction": check_download_restriction,
        }
        with requests.get(Api.ENDPOINT + "scene-list-add", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

        items_to_add: int = 1 if entity_ids is None else len(entity_ids)
        if message_content["data"] != items_to_add:
            raise RuntimeError(
                f"Number of scenes added {message_content['data']} does not equal provided number of scenes {items_to_add}"
            )

    def scene_list_get(
        self,
        list_id: str,
        dataset_name: Optional[str],
        starting_number: Optional[int],
        max_results: Optional[int],
    ) -> List[Dict]:
        """
        Returns items in the given scene list.

        .. note:: starting_number is 1-indexed

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias
        :type dataset_name: Optional[str]
        :param starting_number: Used to identify the start number to search from
        :type starting_number: Optional[int]
        :param max_results: How many results should be returned?
        :type max_results: Optional[int]
        :return: List of items in requested scene list. Each entry is a dictionary in the form of {'entityId', 'datasetName'}.
        :rtype: List[Dict]
        :raises HTTPError:

        :Example:

        Api.scene_list_get(list_id="my_scene_list")
        """
        payload = {
            "listID": list_id,
            "datasetName": dataset_name,
            "startingNumber": starting_number,
            "maxResults": max_results,
        }
        with requests.get(Api.ENDPOINT + "scene-list-get", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

        return message_content["data"]

    def scene_list_remove(
        self,
        list_id: str,
        dataset_name: Optional[str],
        entity_id: Optional[str],
        entity_ids: Optional[List[str]],
    ):
        """
        Removes items from the given list. If no datasetName is provided, the call removes
        the whole list. If a datasetName is provided but no entityId, this call removes that
        dataset with all its IDs. If a datasetName and entityId(s) are provided,
        the call removes the ID(s) from the dataset.

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias
        :type dataset_name: Optional[str]
        :param entity_id: Scene Identifier
        :type entity_id: Optional[str]
        :param entity_ids: A list of Scene Identifiers
        :type entity_ids: Optional[List[str]]
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
            "listID": list_id,
            "datasetName": dataset_name,
            "entityId": entity_id,
            "entityIds": entity_ids,
        }
        with requests.get(
            Api.ENDPOINT + "scene-list-remove", json=payload, headers=self.headers
        ) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

    def scene_list_summary(self, list_id: str, dataset_name: Optional[str]) -> Dict:
        """
        Returns summary information for a given list.

        :param list_id: User defined name for the list
        :type list_id: str
        :param dataset_name: Dataset alias
        :type dataset_name: Optional[str]
        :return: Dictionary containing a summary and datasets ({'summary', 'datasets'}).
        :rtype: Dict
        :raises HTTPError:
        """
        payload = {
            "listID": list_id,
            "datasetName": dataset_name,
        }
        with requests.get(
            Api.ENDPOINT + "scene-list-summary", json=payload, headers=self.headers
        ) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

        return message_content["data"]

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
        with requests.get(
            Api.ENDPOINT + "scene-list-types", json=payload, headers=self.headers
        ) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()

        return message_content["data"]

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
        with requests.get(Api.ENDPOINT + "scene-metadata", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()
        return message_content["data"]

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
        with requests.get(
            Api.ENDPOINT + "scene-metadata-list", json=payload, headers=self.headers
        ) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()
        return message_content["data"]

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
        with requests.get(
            Api.ENDPOINT + "scene-metadata-list", json=payload, headers=self.headers
        ) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()
        return message_content["data"]

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
        :return: Dictionary containing search results as List[Dict] together with some additional search meatadata
        :rtype: Dict

        :raises HTTPError:

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
        with requests.get(Api.ENDPOINT + "scene-search", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()
        return message_content["data"]

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
        with requests.get(
            Api.ENDPOINT + "scene-search-delete", json=payload, headers=self.headers
        ) as r:
            message_content: Dict = loads(r.text)

            if message_content["errorCode"] is not None:
                print(
                    f"{message_content['errorCode']}: {message_content['errorMessage']}",
                    file=sys.stderr,
                )

            _ = r.raise_for_status()
        return message_content["data"]

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
        pass

    def user_preferences_get(self):
        pass

    def user_preferences_set(self):
        pass
