"""
API Class representing USGS's machine-to-machine API: https://m2m.cr.usgs.gov/api/docs/reference/
"""
from typing import Optional, Any, Dict, List, Literal
from datetime import datetime
from json import loads
import sys
import warnings
import requests

from callusgs.types import UserContext

class Api:
    ENDPOINT: str = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    def __init__(self) -> None:
        self.key: Optional[str] = None
        self.login_timestamp: Optional[datetime] = None
        self.headers: Dict[str, str] = None

    
    def _call(self, url: str):
        # TODO should check if 2 hours have passed since login_timestamp was set. => see docstring of login method
        pass


    def check_login_timestamp(self, *args, **kwargs) -> Any:
        pass

    
    def data_owner(self):
        pass

    
    def dataset(self):
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
        Upon a successful login, an API key will be returned. This key will be active for two hours and should be destroyed upon final use of the service by calling the logout method. 

        .. note:: This request requires an HTTP POST request instead of a HTTP GET request as a security measure to prevent username and password information from being logged by firewalls, web servers, etc.

        :param username: ERS Username
        :type username: str
        :param password: ERS Password
        :type password: str
        :param user_context: Metadata describing the user the request is on behalf of, defaults to None
        :type user_context: Any, optional
        :raises HTTPError:
        """
        payload: Dict = {
            "username": username,
            "password": password
        }
        if user_context:
            payload += {"userContext": user_context}
        with requests.post(Api.ENDPOINT + "login", json=payload) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

            _ = r.raise_for_status()

            self.key = message_content["data"]
            self.login_timestamp = datetime.now()
            self.headers = {"X-Auth-Token": self.key}


    def login_app_guest(self, application_token: str, user_token: str):
        """
        This endpoint assumes that the calling application has generated a single-use token to complete the authentication and return an API Key specific to that guest user. All subsequent requests should use the API Key under the 'X-Auth-Token' HTTP header as the Single Sign-On cookie will not authenticate those requests. The API Key will be active for two hours, which is restarted after each subsequent request, and should be destroyed upon final use of the service by calling the logout method.

        The 'appToken' field will be used to verify the 'Referrer' HTTP Header to ensure the request was authentically sent from the assumed application. 

        :param application_token: The token for the calling application
        :type application_token: str
        :param user_token: The single-use token generated for this user
        :type user_token: str
        :raises HTTPError:
        """        
        payload: Dict = {
            "application_token": application_token,
            "user_token": user_token
        }
        with requests.post(Api.ENDPOINT + "login-app-guest", json=payload) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

            _ = r.raise_for_status()

            self.key = message_content["data"]
            self.login_timestamp = datetime.now()
            self.headers = {"X-Auth-Token": self.key}


    def login_sso(self, user_context: UserContext = None):
        """
        This endpoint assumes that a user has an active ERS Single Sign-On Cookie in their browser or attached to this request. Authentication will be performed from the Single Sign-On Cookie and return an API Key upon successful authentication. All subsequent requests should use the API Key under the 'X-Auth-Token' HTTP header as the Single Sign-On cookie will not authenticate those requests. The API Key will be active for two hours, which is restarted after each subsequent request, and should be destroyed upon final use of the service by calling the logout method. 

        :param user_context: Metadata describing the user the request is on behalf of, defaults to None
        :type user_context: UserContext, optional
        :raises NotImplementedError:
        """        
        raise NotImplementedError()


    def login_token(self, username: str, token: str):
        """
        This login method uses ERS application tokens to allow for authentication that is not directly tied the users ERS password. Instructions for generating the application token can be found [here](https://www.usgs.gov/media/files/m2m-application-token-documentation).

        Upon a successful login, an API key will be returned. This key will be active for two hours and should be destroyed upon final use of the service by calling the logout method.

        .. note:: This request requires an HTTP POST request instead of a HTTP GET request as a security measure to prevent username and password information from being logged by firewalls, web servers, etc.

        :param username: ERS Username
        :type username: str
        :param token: Application Token
        :type token: str
        :raises HTTPError:
        """        
        payload: Dict = {
            "username": username,
            "token": token
        }
        with requests.post(Api.ENDPOINT + "login-token", json=payload) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

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
        Returns a list of user permissions for the authenticated user. This method does not accept any input. 

        :return: List of user permissions
        :rtype: List[str]
        :raises HTTPError:
        """        
        with requests.get(Api.ENDPOINT  + "permissions") as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

            _ = r.raise_for_status()

        return message_content["data"]


    def placename(self, feature_type: Optional[Literal["US", "World"]] = None, name: Optional[str] = None) -> Dict:
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
        payload = {
            "featureType": feature_type, 
            "name": name
        }
        with requests.get(Api.ENDPOINT + "placename", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

            _ = r.raise_for_status()
        
        return message_content["data"]["results"]


    def scene_list_add(self, list_id: str, dataset_name: str, id_field: Optional[Literal["entityId", "displayId"]] = "entityId", entity_id: Optional[str] = None, entity_ids: Optional[List[str]] = None, ttl: Optional[str] = None, check_download_restriction: Optional[bool] = None):
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

        Api.scene_list_add(list_id="my_scene_list", dataset_name="landsat_ot_c2_l2", id_field="displayId", entity_id="LC08_L2SP_012025_20201231_20210308_02_T1")
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
            "checkDownloadRestriction": check_download_restriction
        }
        with requests.get(Api.ENDPOINT + "scene-list-add", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

            _ = r.raise_for_status()
        
        items_to_add: int = 1 if entity_ids is None else len(entity_ids)
        if message_content["data"] != items_to_add:
            raise RuntimeError(f"Number of scenes added {message_content["data"]} does not equal provided number of scenes {items_to_add}")


    def scene_list_get(self, list_id: str, dataset_name: Optional[str], starting_number: Optional[int], max_results: Optional[int]) -> List[Dict]:
        """
        Returns items in the given scene list. 

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
            "maxResults": max_results
        }
        with requests.get(Api.ENDPOINT + "scene-list-get", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

            _ = r.raise_for_status()
        
        return message_content["data"]


    def scene_list_remove(self, list_id: str, dataset_name: Optional[str], entity_id: Optional[str], entity_ids: Optional[List[str]]):
        """
        Removes items from the given list. If no datasetName is provided, the call removes the whole list. If a datasetName is provided but no entityId, this call removes that dataset with all its IDs. If a datasetName and entityId(s) are provided, the call removes the ID(s) from the dataset. 

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

        Api.scene_list_remove(list_id="my_scene_list", dataset_name="landsat_ot_c2_l2", entity_id="LC80120252020366LGN00")
        """        
        if entity_id is not None and entity_ids is not None:
            warnings.warn("Both entityId and entityIds given. Passing both to API.")
        payload = {
            "listID": list_id,
            "datasetName": dataset_name,
            "entityId": entity_id,
            "entityIds": entity_ids
        }
        with requests.get(Api.ENDPOINT + "scene-list-remove", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

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
        with requests.get(Api.ENDPOINT + "scene-list-summary", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

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
        payload = {
            "listFilter": list_filter
        }
        with requests.get(Api.ENDPOINT + "scene-list-types", json=payload, headers=self.headers) as r:
            message_content: Dict = loads(r.text)
            
            if message_content["errorCode"] is not None:
                print(f"{message_content['errorCode']}: {message_content['errorMessage']}", file=sys.stderr)

            _ = r.raise_for_status()
        
        return message_content["data"]


    def scene_metadata(self):
        pass


    def scene_metadata_list(self):
        pass


    def scene_metadata_xml(self):
        pass


    def scene_search(self):
        pass


    def scene_search_delete(self):
        pass


    def scene_search_secondary(self):
        pass


    def user_preferences_get(self):
        pass

    
    def user_preferences_set(self):
        pass

