"""
Implementation of USGS's machine-to-machine API data types: https://m2m.cr.usgs.gov/api/docs/datatypes/
"""

from json import dumps
from typing import List, Any, Union, Optional, Dict

from callusgs.errors import ErrorCodes


class ApiResponse:
    """
    Custom data type to represent Api response objects.
    """

    def __init__(
        self,
        data: Optional[Union[Dict, List[Dict]]] = None,
        version: Optional[str] = None,
        errorCode: Optional[str] = None,
        requestId: Optional[str] = None,
        sessionId: Optional[str] = None,
        errorMessage: Optional[str] = None,
    ) -> None:
        self.data: Union[Dict, List[Dict]] = data
        self.version: str = version
        self.error_code: str = errorCode
        self.error_message: str = errorMessage
        self.request_id: str = requestId
        self.session_id: str = sessionId

    def raise_status(self) -> None:
        raise ErrorCodes()(self.error_code)


class EarthExplorerBaseType:
    def json(self) -> str:
        return dumps(self.__dict__, default=vars)


class AcquisitionFilter(EarthExplorerBaseType):
    def __init__(self, start: str, end: str) -> None:
        """
        Aquisition filter data type

        .. note:: General data type

        :param start: The date the scene began acquisition - ISO 8601 Formatted Date (YYYY-MM-DD)
        :type start: str
        :param end: The date the scene ended acquisition - ISO 8601 Formatted Date (YYYY-MM-DD)
        :type end: str
        """
        self.start: str = start
        self.end: str = end


class CloudCoverFilter(EarthExplorerBaseType):
    def __init__(self, _min: int, _max: int, include_unknown: bool) -> None:
        """
        Cloud cover filter data type

        .. note:: General data type

        :param min: Used to limit results by minimum cloud cover (for supported datasets)
        :type min: int
        :param max: Used to limit results by maximum cloud cover (for supported datasets)
        :type max: int
        :param include_unknown: Used to determine if scenes with unknown cloud cover values should be included in the results
        :type include_unknown: bool
        """
        self.min: int = _min
        self.max: int = _max
        self.includeUnknown: bool = include_unknown


class Coordinate(EarthExplorerBaseType):
    def __init__(self, latitude: float, longitude: float) -> None:
        """
        Coordinate data type

        .. note:: General data type

        :param latitude: Decimal degree coordinate in EPSG:4326 projection
        :type latitude: float
        :param longitude: Decimal degree coordinate in EPSG:4326 projection
        :type longitude: float
        """
        self.latitude: float = latitude
        self.longitude: float = longitude


class DateRange(EarthExplorerBaseType):
    def __init__(self, start_date: str, end_date: str) -> None:
        """
        Date Range data type

        .. note:: General data type

        :param start_date: Used to apply a temporal filter on the data - ISO 8601 Formatted Date
        :type start_date: str
        :param end_date: Used to apply a temporal filter on the data - ISO 8601 Formatted Date
        :type end_date: str
        """
        self.startDate: str = start_date
        self.endDate: str = end_date


class TemplateConfiguration(EarthExplorerBaseType):
    """This is an abstract data model, use ingestUpdateTemplate"""

    pass


class GeoJson(EarthExplorerBaseType):
    def __init__(
        self, type: str, coordinates: Union[List[float], List[List[List[float]]]]
    ) -> None:
        """
        GeoJson data type

        .. note:: General data type

        .. note:: A polygon is a list of linestrings.

        .. warning:: In contrast to the documentation, coordinates must be an array
            of floats (coordinate pairs) and not instances of Coordinate object!

        .. warning:: GeoJson expects coordinate pairs to be longitude, latidue!

        :param type: Geometry types supported by GeoJson, like polygon
        :type type: str
        :param coordinates: Coordinate array
        :type coordinates: Union[List[float], List[List[List[float]]]]
        """
        self.type: str = type
        self.coordinates: Union[List[float], List[List[List[float]]]] = coordinates


class IngestUpdateTemplate(EarthExplorerBaseType):
    def __init__(
        self,
        template_id: str,
        dar_id: str,
        scene_ids: List[str],
        view_name: str,
        id_field: str = "EE_DISPLAY_ID",
    ) -> None:
        """
        Ingest Update Template data type

        .. note:: General data type

        :param template_id: value must be 'ingestUpdate'
        :type template_id: str
        :param dar_id: The number of data acquisition request
        :type dar_id: str
        :param scene_ids: An array of Scene IDs
        :type scene_ids: List[str]
        :param view_name: The view name of the dataset
        :type view_name: str
        :param id_field: Used to determine the ID being used in EE, defaults to "EE_DISPLAY_ID"
        :type id_field: str
        """
        self.templateId: str = template_id
        self.darId: str = dar_id
        self.sceneIds: List[str] = scene_ids
        self.viewName: str = view_name
        self.idField: str = id_field


class IngestFilter(EarthExplorerBaseType):
    def __init__(self, start: str, end: str) -> None:
        """
        Ingest Filter data type

        .. note:: General data type

        :param start: Used to filter scenes by last metadata ingest, YYYY-MM-DD format
        :type start: str
        :param end: Used to filter scenes by last metadata ingest, YYYY-MM-DD format
        :type end: str
        """
        self.start: str = start
        self.end: str = end


class MetadataFilter(EarthExplorerBaseType):
    """This is an abstract data model, use MetadataAnd, MetadataBetween, MetadataOr, or MetadataValue"""

    pass


class Metadata(EarthExplorerBaseType):
    """This is an abstract data model, use MetadataAnd, MetadataBetween, MetadataOr, or MetadataValue"""

    pass


class MetadataAnd(EarthExplorerBaseType):
    def __init__(self, child_filters: List[Union[MetadataFilter, Metadata]]) -> None:
        """
        Metadata And data type

        .. note:: General data type

        :param child_filters: Joins any filter parameters together with the "and" logical operator
        :type child_filters: List[Union[MetadataFilter, Metadata]]
        """
        self.filterType: str = "and"
        self.childFilters: List[Union[MetadataFilter, Metadata]] = child_filters


class MetadataBetween(EarthExplorerBaseType):
    def __init__(self, filter_id: str, first_value: int, second_value: int) -> None:
        """
        Matadata Between data type

        .. note:: General data type

        :param filter_id: Unique Identifier for the dataset criteria field and it can be retrieved by dataset-filters
        :type filter_id: str
        :param first_value: First value in between clause
        :type first_value: int
        :param second_value: Second value in between clause
        :type second_value: int
        """
        self.filterType: str = "between"
        self.filterId: str = filter_id
        self.firstValue: int = first_value
        self.secondValue: int = second_value


class MetadataOr(EarthExplorerBaseType):
    def __init__(self, child_filters: List[Union[MetadataFilter, Metadata]]) -> None:
        """
        Metadata Or data type

        .. note:: General data type

        :param child_filters: Joins any filter parameters with the "or" logical operator
        :type child_filters: List[Union[MetadataFilter, Metadata]]
        """
        self.filterType: str = "or"
        self.childFilters: List[Union[MetadataFilter, Metadata]] = child_filters


class MetadataValue(EarthExplorerBaseType):
    def __init__(
        self, filter_type: str, filter_id: str, value: str, operand: str
    ) -> None:
        """
        Metadata Value data type

        .. note:: General data type

        :param filter_type: Value must be "value"
        :type filter_type: str
        :param filter_id: Unique Identifier for the dataset criteria field and it can be retrieved by dataset-filters
        :type filter_id: str
        :param value: Value to use
        :type value: str
        :param operand: Determines what operand to search with - accepted values are "=" and "like"
        :type operand: str
        """
        self.filterType: str = filter_type
        self.filterId: str = filter_id
        self.value: str = value
        self.operand: str = operand


class SpatialFilter(EarthExplorerBaseType):
    """This is an abstract data model, use SpatialFilterMbr or SpatialFilterGeoJson"""

    pass


class SceneFilter(EarthExplorerBaseType):
    def __init__(
        self,
        acquisition_filter: Optional[AcquisitionFilter] = None,
        cloudcover_filter: Optional[CloudCoverFilter] = None,
        dataset_name: Optional[str] = None,
        ingest_filter: Optional[IngestFilter] = None,
        metadata_filter: Optional[MetadataFilter] = None,
        seasonal_filter: Optional[List[int]] = None,
        spatial_filter: Optional[SpatialFilter] = None,
    ) -> None:
        """
        Scene Filter data type

        .. note:: General data type

        :param acquisition_filter: Used to apply a acquisition filter on the data, defaults to None
        :type acquisition_filter: Optional[AcquisitionFilter], optional
        :param cloudcover_filter: Used to apply a cloud cover filter on the data, defaults to None
        :type cloudcover_filter: Optional[CloudCoverFilter], optional
        :param dataset_name: Dataset name, defaults to None
        :type dataset_name: Optional[str], optional
        :param ingest_filter: Used to apply an ingest filter on the data, defaults to None
        :type ingest_filter: Optional[IngestFilter], optional
        :param metadata_filter: Used to apply a metadata filter on the data, defaults to None
        :type metadata_filter: Optional[MetadataFilter], optional
        :param seasonal_filter: Used to apply month numbers from 1 to 12 on the data, defaults to None
        :type seasonal_filter: Optional[List[int]], optional
        :param spatial_filter: Used to apply a spatial filter on the data, defaults to None
        :type spatial_filter: Optional[SpatialFilter], optional
        """
        self.acquisitionFilter: AcquisitionFilter = acquisition_filter
        self.cloudCoverFilter: CloudCoverFilter = cloudcover_filter
        self.datasetName: str = dataset_name
        self.ingestFilter: IngestFilter = ingest_filter
        self.metadataFilter: MetadataFilter = metadata_filter
        self.seasonalFilter: List[int] = seasonal_filter
        self.spatialFilter: SpatialFilter = spatial_filter


class SceneDatasetFilter(EarthExplorerBaseType):
    def __init__(self, dataset_name: str, scene_filter: List[SceneFilter]) -> None:
        """
        Scene Dataset Filter data type

        .. note:: General data type

        :param dataset_name: Dataset name
        :type dataset_name: str
        :param scene_filter: Used to apply a scene filter on the data
        :type scene_filter: List[SceneFilter]
        """
        self.datasetName: str = dataset_name
        self.sceneFilter: List[SceneFilter] = scene_filter


class SceneMetadataConfig(EarthExplorerBaseType):
    def __init__(self, include_nulls: bool, type: str, template: str) -> None:
        """
        Scene Metadata Config data type

        .. note:: General data type

        :param include_nulls: Used to include or exclude null values
        :type include_nulls: bool
        :param type: Value can be 'full', 'summary' or null
        :type type: str
        :param template: Metadata template
        :type template: str
        """
        self.includeNulls: bool = include_nulls
        self.type: str = type
        self.template: str = template


class SpatialBounds(EarthExplorerBaseType):
    """This is an abstract data model, use spatialBoundsMbr or geoJson"""

    pass


class SpatialBoundsMbr(EarthExplorerBaseType):
    def __init__(self, north: str, east: str, south: str, west: str) -> None:
        """
        Spatial Bounds Mbr data type

        .. note:: General data type

        :param north: Decimal degree coordinate value in EPSG:4326 projection representing the northern most point of the MBR
        :type north: str
        :param east: Decimal degree coordinate value in EPSG:4326 projection representing the eastern most point of the MBR
        :type east: str
        :param south: Decimal degree coordinate value in EPSG:4326 projection representing the southern most point of the MBR
        :type south: str
        :param west: Decimal degree coordinate value in EPSG:4326 projection representing the western most point of the MBR
        :type west: str
        """
        self.nort: str = north
        self.east: str = east
        self.south: str = south
        self.west: str = west


class SpatialFilterMbr(EarthExplorerBaseType):
    def __init__(self, lower_left: Coordinate, upper_right: Coordinate) -> None:
        """
        Spatial Filter Mbr (minimum bound rectangle) data type

        :param lower_left: The southwest point of the minimum bounding rectangle
        :type lower_left: Coordinate
        :param upper_right: The northeast point of the minimum bounding rectangle
        :type upper_right: Coordinate
        """
        self.filterType: str = "mbr"
        self.lowerLeft = lower_left
        self.upperRight = upper_right


class SpatialFilterGeoJson(EarthExplorerBaseType):
    def __init__(self, geo_json: GeoJson) -> None:
        """
        Spatial Filter GeoJson data type

        .. note:: General data type

        :param geo_json: A GeoJson object representing a region of space
        :type geo_json: GeoJson
        """
        self.filterType: str = "geojson"
        self.geoJson: GeoJson = geo_json


class UserContext(EarthExplorerBaseType):
    def __init__(self, contact_id: str, ip_address: str) -> None:
        """
        User Context data type

        .. note:: General data type

        :param contact_id: Internal user Identifier
        :type contact_id: str
        :param ip_address: Ip address used to send the request
        :type ip_address: str
        """
        self.contactId: str = contact_id
        self.ipAddress: str = ip_address


class TemporalCoverage(EarthExplorerBaseType):
    def __init__(self, start_date: str, end_date: str) -> None:
        """
        Temporal Coverage data type

        .. note:: General data type

        :param start_date: Starting temporal extent of coverage - ISO 8601 Formatted Date
        :type start_date: str
        :param end_date: Ending temporal extent of the coverage - ISO 8601 Formatted Date
        :type end_date: str
        """
        self.startDate: str = start_date
        self.endDate: str = end_date


class TemporalFilter(EarthExplorerBaseType):
    def __init__(self, start: str, end: str) -> None:
        """
        Temporal Filter data type

        .. note:: General data type

        :param start: ISO 8601 Formatted Date
        :type start: datetime
        :param end: ISO 8601 Formatted Date
        :type end: datetime
        """
        self.start: str = start
        self.end: str = end


class DownloadResponse(EarthExplorerBaseType):
    def __init__(
        self,
        _id: int,
        display_id: str,
        entity_id: str,
        dataset_id: str,
        available: str,
        file_size: int,
        product_name: str,
        product_code: str,
        bulk_available: str,
        download_system: str,
        secondary_downloads: "DownloadResponse",
    ) -> None:
        """
        Download Response data type

        .. note:: Download data type

        :param _id: Scene Identifier
        :type _id: int
        :param display_id: Scene Identifier used for display
        :type display_id: str
        :param entity_id: Entity Identifier
        :type entity_id: str
        :param dataset_id: Dataset Identifier
        :type dataset_id: str
        :param available: Value is "Y" or "N". Denotes if the download option is available
        :type available: str
        :param file_size: The size of the download in bytes
        :type file_size: int
        :param product_name: The user friendly name for this download option
        :type product_name: str
        :param product_code: Internal product code to represent the download option
        :type product_code: str
        :param bulk_available: Value is "Y" or "N". Denotes if the download option is available for bulk
        :type bulk_available: str
        :param download_system: The system that is running the download
        :type download_system: str
        :param secondary_downloads: An array of related downloads
        :type secondary_downloads: DownloadResponse
        """
        self.id: int = _id
        self.displayId: str = display_id
        self.entityId: str = entity_id
        self.datasetId: str = dataset_id
        self.available: str = available
        self.filesize: int = file_size
        self.productName: str = product_name
        self.productCode: str = product_code
        self.bulkAvailable: str = bulk_available
        self.downloadSystem: str = download_system
        self.secondaryDownloads: "DownloadResponse" = secondary_downloads


class DownloadInput(EarthExplorerBaseType):
    def __init__(
        self, entity_id: str, product_id: str, data_use: str, label: str
    ) -> None:
        """
        Download Input data type

        .. note:: Download data type

        :param entity_id: Entity Identifier
        :type entity_id: str
        :param product_id: Product identifiers
        :type product_id: str
        :param data_use: The type of use of this data
        :type data_use: str
        :param label: The label name used when requesting the download
        :type label: str
        """
        self.entityId: str = entity_id
        self.productId: str = product_id
        self.dataUse: str = data_use
        self.label: str = label


class DownloadQueueDownload(EarthExplorerBaseType):
    def __init__(
        self,
        download_id: int,
        collection_name: str,
        dataset_id: str,
        display_id: str,
        entity_id: str,
        eula_code: Optional[str],
        file_size: int,
        label: str,
        product_code: str,
        product_name: str,
        status_code: str,
        status_text: str,
    ) -> None:
        """
        Download Queue Download data type

        .. note:: Download data type

        :param download_id: Download Identifier
        :type download_id: int
        :param collection_name: User friendly name of the collection
        :type collection_name: str
        :param dataset_id: Dataset Identifier
        :type dataset_id: str
        :param display_id: Scene Identifier used for display
        :type display_id: str
        :param entity_id: Entity Identifier
        :type entity_id: str
        :param eula_code: A EULA Code to use for EULA retrieval - only populated when loading download orders
        :type eula_code: Optional[str]
        :param file_size: The size of the download in bytes
        :type file_size: int
        :param label: The label name used when requesting the download
        :type label: str
        :param product_code: Internal product code to represent the download option
        :type product_code: str
        :param product_name: The user friendly name for this product
        :type product_name: str
        :param status_code: Internal status code
        :type status_code: str
        :param status_text: User friendly status
        :type status_text: str
        """
        self.downloadId: int = download_id
        self.collectionName: str = collection_name
        self.datasetId: str = dataset_id
        self.displayId: str = display_id
        self.entityId: str = entity_id
        self.eulCode: str = eula_code
        self.filesize: int = file_size
        self.label: str = label
        self.productCode: str = product_code
        self.productName: str = product_name
        self.statusCode: str = status_code
        self.statusText: str = status_text


class Eula(EarthExplorerBaseType):
    def __init__(
        self, eula_code: Optional[str], agreement_content: Optional[str]
    ) -> None:
        """
        Eula data type

        .. note:: Download data type

        :param eula_code: A EULA Code to use for EULA retrieval - only populated when loading download orders
        :type eula_code: Optional[str]
        :param agreement_content: Agreement clauses to use the data - only populated when loading download orders
        :type agreement_content: Optional[str]
        """
        self.eulaCode: Optional[str] = eula_code
        self.agreementContent: Optional[str] = agreement_content


class FilegroupDownload(EarthExplorerBaseType):
    def __init__(
        self,
        dataset_name: str,
        file_groups: List[str],
        list_id: str,
        data_use: str,
        label: str,
    ) -> None:
        """
        Filegroup Download data type

        .. note:: Download data type

        :param dataset_name: Dataset name
        :type dataset_name: str
        :param file_groups: Internal codes used to represent the file groups
        :type file_groups: List[str]
        :param list_id: The name of scene list to request from
        :type list_id: str
        :param data_use: The type of use of this data
        :type data_use: str
        :param label: The label name used when requesting the download
        :type label: str
        """
        self.datasetName: str = dataset_name
        self.fileGroups: List[str] = file_groups
        self.listId: str = list_id
        self.dataUse: str = data_use
        self.label: str = label


class FilepathDownload(EarthExplorerBaseType):
    def __init__(
        self,
        dataset_name: str,
        product_code: str,
        data_path: str,
        data_use: str,
        label: str,
    ) -> None:
        """
        Filepath Download

        .. note:: Download data type

        :param dataset_name: Dataset name
        :type dataset_name: str
        :param product_code: Internal code used to represent this product during ordering
        :type product_code: str
        :param data_path: The data location to stream the download from
        :type data_path: str
        :param data_use: The type of use of this data
        :type data_use: str
        :param label: The label name used when requesting the download
        :type label: str
        """
        self.datasetName: str = dataset_name
        self.productCode: str = product_code
        self.dataPath: str = data_path
        self.dataUse: str = data_use
        self.label: str = label


class Options(EarthExplorerBaseType):
    def __init__(
        self, bulk: bool, order: bool, download: bool, secondary: bool
    ) -> None:
        """
        Options data type

        .. note:: Download data type

        :param bulk: Denotes if the scene is available for bulk
        :type bulk: bool
        :param order: Denotes if the scene is available for order
        :type order: bool
        :param download: Denotes if the scene is available for download
        :type download: bool
        :param secondary: Denotes if the scene is available for secondary download
        :type secondary: bool
        """
        self.bulk: bool = bulk
        self.order: bool = order
        self.download: bool = download
        self.secondary: bool = secondary


class ProductDownload(EarthExplorerBaseType):
    def __init__(
        self, dataset_name: str, product_ids: List[str], scene_filter: SceneFilter
    ) -> None:
        """
        Product Download data type

        .. note:: Download data type

        :param dataset_name: Dataset name
        :type dataset_name: str
        :param product_ids: Product identifiers
        :type product_ids: List[str]
        :param scene_filter: Used to apply a scene filter on the data
        :type scene_filter: SceneFilter
        """
        self.datasetName: str = dataset_name
        self.productIds: List[str] = product_ids
        self.sceneFilter: SceneFilter = scene_filter


class ProxiedDownload(EarthExplorerBaseType):
    def __init__(self, download_id: int, downloaded_size: int) -> None:
        """
        Proxied Download data type

        .. note:: Download data type

        :param download_id: Download Identifier
        :type download_id: int
        :param downloaded_size: Total downloaded size of the file
        :type downloaded_size: int
        """
        self.downloadId: int = download_id
        self.downloadedSize: int = downloaded_size


class Selected(EarthExplorerBaseType):
    def __init__(self, bulk: bool, order: bool, compare: bool) -> None:
        """
        Selected data type

        .. note:: Download data type

        :param bulk: Denotes if the scene is selected for bulk
        :type bulk: bool
        :param order: Denotes if the scene is selected for order
        :type order: bool
        :param compare: Denotes if the scene is selected for compare
        :type compare: bool
        """
        self.bulk: bool = bulk
        self.order: bool = order
        self.compare: bool = compare


class MetadataExport(EarthExplorerBaseType):
    def __init__(
        self,
        export_id: str,
        export_name: str,
        dataset_id: str,
        dataset_name: str,
        scene_filter: SceneFilter,
        custom_message: str,
        export_type: str,
        status: str,
        status_name: str,
        date_entered: str,
        date_updated: str,
    ) -> None:
        """
        Metadata Export data type

        .. note:: Export data type

        :param export_id: Identifier of this export
        :type export_id: str
        :param export_name: Name of this export
        :type export_name: str
        :param dataset_id: Dataset Identifier
        :type dataset_id: str
        :param dataset_name: Dataset name
        :type dataset_name: str
        :param scene_filter: Used to apply a scene filter on the data
        :type scene_filter: SceneFilter
        :param custom_message: The content of the custom message
        :type custom_message: str
        :param export_type: Type of this export
        :type export_type: str
        :param status: Internal Status Code
        :type status: str
        :param status_name: User Friendly Status
        :type status_name: str
        :param date_entered: The date this export was entered
        :type date_entered: str
        :param date_updated: Date the export was last updated
        :type date_updated: str
        """
        self.exportId: str = export_id
        self.exportName: str = export_name
        self.datasetId: str = dataset_id
        self.sceneFilter: SceneFilter = scene_filter
        self.customMessage: str = custom_message
        self.exportType: str = export_type
        self.status: str = status
        self.statusName: str = status_name
        self.dateEntered: str = date_entered
        self.dateUpdated: str = date_updated


class MetadataField(EarthExplorerBaseType):
    def __init__(
        self, _id: int, field_name: str, dictionary_link: str, value: str
    ) -> None:
        """
        Metadata Field data type

        .. note:: Export data type

        :param _id: Metadata Identifier
        :type _id: int
        :param field_name: The name of the metadata field
        :type field_name: str
        :param dictionary_link: A link to the data dictionary entry for this field
        :type dictionary_link: str
        :param value: The value for this metadata field
        :type value: str
        """
        self.id: int = _id
        self.fieldName: str = field_name
        self.dictionaryLink: str = dictionary_link
        self.value: str = value


class Browse(EarthExplorerBaseType):
    def __init__(
        self,
        browse_rotation_enabled: bool,
        browse_name: str,
        browse_path: str,
        overlay_path: str,
        overlay_type: str,
        thumbnail_path: str,
    ) -> None:
        """
        Browse data type

        .. note:: Inventory data type

        :param browse_rotation_enabled: Denotes if the rotation is enabled for browse
        :type browse_rotation_enabled: bool
        :param browse_name: Name for browse
        :type browse_name: str
        :param browse_path: Path for browse
        :type browse_path: str
        :param overlay_path: Path of overlay
        :type overlay_path: str
        :param overlay_type: Type of overlay
        :type overlay_type: str
        :param thumbnail_path: Path of thumbnail
        :type thumbnail_path: str
        """
        self.browseRotationEnabled: bool = browse_rotation_enabled
        self.browseName: str = browse_name
        self.browsePath: str = browse_path
        self.overlayPath: str = overlay_path
        self.overlayType: str = overlay_type
        self.thumbnailPath: str = thumbnail_path


class Dataset(EarthExplorerBaseType):
    def __init__(
        self,
        abstract_text: str,
        acquisition_start: str,
        acquisition_end: str,
        catalogs: List[str],
        collection_name: str,
        collection_long_name: str,
        dataset_id: str,
        dataset_alias: str,
        dataset_category_name: str,
        data_owner: str,
        date_updated: str,
        doi_number: str,
        ingest_frequency: str,
        keywords: str,
        scene_count: int,
        spatial_bounds: SpatialBounds,
        temporal_coverage: TemporalCoverage,
        support_cloud_cover: bool,
        support_deletion_search: bool,
    ) -> None:
        """
        Dataset data type

        .. note:: Inventory data type

        :param abstract_text: Abstract of the dataset
        :type abstract_text: str
        :param acquisition_start: Start date the scene was acquired, ISO 8601 Formatted Date
        :type acquisition_start: str
        :param acquisition_end: End date the scene was acquired, ISO 8601 Formatted Date
        :type acquisition_end: str
        :param catalogs: The Machine-to-Machine dataset catalogs including "EE", "GV", "HDDS", "LPCS"
        :type catalogs: List[str]
        :param collection_name: User friendly name of the collection
        :type collection_name: str
        :param collection_long_name: Full User friendly dataset name
        :type collection_long_name: str
        :param dataset_id: Dataset Identifier
        :type dataset_id: str
        :param dataset_alias: Short User friendly dataset name
        :type dataset_alias: str
        :param dataset_category_name: Category this dataset belongs to
        :type dataset_category_name: str
        :param data_owner: Owner of the data
        :type data_owner: str
        :param date_updated: Date the dataset was last updated, ISO 8601 Formatted Date
        :type date_updated: str
        :param doi_number: DOI name of the dataset
        :type doi_number: str
        :param ingest_frequency: Interval to ingest this dataset (ISO-8601 formmated string)
        :type ingest_frequency: str
        :param keywords: Keywords of the dataset
        :type keywords: str
        :param scene_count: The number of scenes under the dataset
        :type scene_count: int
        :param spatial_bounds: Dataset Spatial Extent
        :type spatial_bounds: SpatialBounds
        :param temporal_coverage: Temporal extent of the dataset (ISO 8601 Formatted Date)
        :type temporal_coverage: TemporalCoverage
        :param support_cloud_cover: Denotes if the dataset supports cloud cover searching (via cloudCover filter in the scene search parameters)
        :type support_cloud_cover: bool
        :param support_deletion_search: Denotes if the dataset supports deletion searching
        :type support_deletion_search: bool
        """
        self.abstractText: str = abstract_text
        self.acquisitionStart: str = acquisition_start
        self.acquisitionEnd: str = acquisition_end
        self.catalogs: List[str] = catalogs
        self.collectionName: str = collection_name
        self.collectionLongName: str = collection_long_name
        self.datasetId: str = dataset_id
        self.datasetAlias: str = dataset_alias
        self.dataOwner: str = data_owner
        self.dateUpdated: str = date_updated
        self.ingestFrequency: str = ingest_frequency
        self.keywords: str = keywords
        self.sceneCount: int = scene_count
        self.spatialBounds: SpatialBounds = spatial_bounds
        self.temporalCoverage: TemporalCoverage = temporal_coverage
        self.supportCloudCover: bool = support_cloud_cover
        self.supportDeletionSearch: bool = support_deletion_search


class DatasetCategory(EarthExplorerBaseType):
    def __init__(
        self,
        _id: int,
        category_name: str,
        category_description: str,
        parent_category_id: int,
        parent_category_name: str,
        reference_link: str,
    ) -> None:
        """
        Dataset Category data type

        .. note:: Inventory data type

        :param _id: Dataset category Identifier
        :type _id: int
        :param category_name: Name of the category
        :type category_name: str
        :param category_description: Description of the category
        :type category_description: str
        :param parent_category_id: Parent category Identifier
        :type parent_category_id: int
        :param parent_category_name: Name of the parent category
        :type parent_category_name: str
        :param reference_link: Information for the category
        :type reference_link: str
        """
        self.id: int = _id
        self.categoryName: str = category_name
        self.categoryDescription: str = category_description
        self.parentCategoryId: int = parent_category_id
        self.parentCategoryName: str = parent_category_name
        self.referenceLink: str = reference_link


class InventoryMetadata(EarthExplorerBaseType):
    def __init__(self, metadata_type: str, _id: str, sort_order: int) -> None:
        """
        Inventory Metadata data type

        .. note:: Inventory data type

        :param metadata_type: Value can be 'export', 'res_sum', 'shp', or 'full'
        :type metadata_type: str
        :param _id: Used to identify which field your referencing.
        :type _id: str
        :param sort_order: Used to change the order in which the fields are sorted.
        :type sort_order: int
        """
        self.metadataType: str = metadata_type
        self.id: str = _id
        self.sortOrder: int = sort_order


class SearchSort(EarthExplorerBaseType):
    def __init__(self, _id: str, direction: str) -> None:
        """
        Search Sort data type

        .. note:: Inventory data type

        :param _id: Used to identify which field you want to sort by.
        :type _id: str
        :param direction: Used to determine which directions to sort (ASC, DESC).
        :type direction: str
        """
        # TODO wouldn't a Choice make the most sense here?
        self.id: str = _id
        self.direction: str = direction


class FileGroups(EarthExplorerBaseType):
    def __init__(self, file_group_id: str, product_ids: List[str]) -> None:
        """
        File Groups data type

        .. note:: Inventory data type

        :param file_group_id: Values are the internal file group IDs
        :type file_group_id: str
        :param product_ids: An array of product IDs within the file group
        :type product_ids: List[str]
        """
        self.fileGroupId: str = file_group_id
        self.productIds: List[str] = product_ids


class DatasetCustomization(EarthExplorerBaseType):
    def __init__(
        self,
        dataset_name: str,
        excluded: bool,
        metadata: InventoryMetadata,
        search_sort: SearchSort,
        file_groups: FileGroups,
    ) -> None:
        """
        Dataset Customization data type

        .. note:: Inventory data type

        :param dataset_name: Alias of the dataset
        :type dataset_name: str
        :param excluded: Used to include or exclude a dataset
        :type excluded: bool
        :param metadata: Used to customize the layout of a datasets metadata
        :type metadata: InventoryMetadata
        :param search_sort: Used to sort the datasets results
        :type search_sort: SearchSort
        :param file_groups: Used to customize the downloads by file groups
        :type file_groups: FileGroups
        """
        self.datasetName: str = dataset_name
        self.excluded: bool = excluded
        self.metadata: InventoryMetadata = metadata
        self.searchSort: SearchSort = search_sort
        self.fileGroups: FileGroups = file_groups


class SortCustomization(EarthExplorerBaseType):
    def __init__(self, filed_name: str, direction: str) -> None:
        """
        Sort Customization data type

        .. note:: Inventory data type

        :param filed_name: Used to identify which field you want to sort by.
        :type filed_name: str
        :param direction: Used to determine which directions to sort (ASC, DESC).
        :type direction: str
        """
        # TODO wouldn't a Choice make the most sense here?
        self.fieldName: str = filed_name
        self.direction: str = direction


class FieldConfig(EarthExplorerBaseType):
    def __init__(
        self, type: str, filters: List[Any], validators: List[Any], display_list_id: str
    ) -> None:
        """
        Field Config data type

        .. note:: Inventory data type

        :param type: Value can be 'Select", 'Text', 'Range'
        :type type: str
        :param filters: Reference only. Describes the input for a query
        :type filters: List[Any]
        :param validators: Reference only. Describes various validation the input data is put through prior to being used in the query
        :type validators: List[Any]
        :param display_list_id: Internal reference. Used to reference where provided value lists are sourced from
        :type display_list_id: str
        """
        self.type: str = type
        self.filters: List[Any] = filters
        self.validators: List[Any] = validators
        self.displayListId: str = display_list_id


class DatasetFilter(EarthExplorerBaseType):
    def __init__(
        self,
        _id: int,
        legacy_field_id: int,
        dictionary_link: str,
        field_config: FieldConfig,
        field_label: str,
        search_sql: str,
    ) -> None:
        """
        Dataset Filter data type

        .. note:: Inventory data type

        :param _id: Dataset Identifier
        :type _id: int
        :param legacy_field_id: Legacy field Identifier
        :type legacy_field_id: int
        :param dictionary_link: A link to the data dictionary entry for this field
        :type dictionary_link: str
        :param field_config: Configuration of the field
        :type field_config: FieldConfig
        :param field_label: The label name used when requesting the field
        :type field_label: str
        :param search_sql: WHERE clause when searching in the database
        :type search_sql: str
        """
        self.id: int = _id
        self.legacyFieldId: int = legacy_field_id
        self.dictionaryLink: str = dictionary_link
        self.fieldConfig: FieldConfig = field_config
        self.fieldLabel: str = field_label
        self.searchSql: str = search_sql


class Notifaction(EarthExplorerBaseType):
    def __init__(
        self,
        _id: int,
        subject: str,
        message_content: str,
        severity_code: str,
        severity_css_class: str,
        severity_text: str,
        date_updated: str,
    ) -> None:
        """
        Notification data type

        .. note:: Notification data type

        :param _id: Notification Identifier
        :type _id: int
        :param subject: The subject of the notification
        :type subject: str
        :param message_content: The content of the notification message
        :type message_content: str
        :param severity_code: Internal severity code
        :type severity_code: str
        :param severity_css_class: Class of the severity
        :type severity_css_class: str
        :param severity_text: The user friendly name for this severity
        :type severity_text: str
        :param date_updated: Date the notification was last updated
        :type date_updated: str
        """
        self.id: int = _id
        self.subject: str = subject
        self.messageContent: str = message_content
        self.severityCode: str = severity_code
        self.severityCssClass: str = severity_css_class
        self.severityText: str = severity_text
        self.dateUpdated: str = date_updated


class ProductResponse(EarthExplorerBaseType):
    def __init__(
        self,
        _id: int,
        entity_id: str,
        dataset_id: str,
        available: str,
        price: float,
        product_name: str,
        product_code: str,
    ) -> None:
        """
        Product Response data type

        .. note:: Order data type

        :param _id: Product Identifier
        :type _id: int
        :param entity_id: Entity Identifier
        :type entity_id: str
        :param dataset_id: Dataset Identifier
        :type dataset_id: str
        :param available: Denotes if the download option is available
        :type available: str
        :param price: The price for ordering this product, less the $5.00 handling fee per order(Handling Fee - Applies to Orders that require payment)
        :type price: float
        :param product_name: User friendly name for this product
        :type product_name: str
        :param product_code:  	Internal code used to represent this product during ordering
        :type product_code: str
        """
        self.id: int = _id
        self.entityId: str = entity_id
        self.datasetId: str = dataset_id
        self.available: str = available
        self.price: float = price
        self.productName: str = product_name
        self.procuct_code: str = product_code


class ProductInput(EarthExplorerBaseType):
    def __init__(
        self, dataset_name: str, entity_id: str, product_id: str, product_code: str
    ) -> None:
        """
        Prodcut Input data type

        .. note:: Order data type

        :param dataset_name: Dataset name
        :type dataset_name: str
        :param entity_id: Entity Identifier
        :type entity_id: str
        :param product_id: Product identifiers
        :type product_id: str
        :param product_code: Internal product code to represent the download option
        :type product_code: str
        """
        self.datasetName: str = dataset_name
        self.entityId: str = entity_id
        self.productId: str = product_id
        self.productCode: str = product_code


class RunOptions(EarthExplorerBaseType):
    def __init__(self, result_formats: List[str]) -> None:
        """
        Run Options data type

        .. note:: Order data type

        :param result_formats: The valid values are 'metadata', 'email', 'kml', 'shapefile', 'geojson'
        :type result_formats: List[str]
        """
        self.resultFormats: List[str] = result_formats


class Scene(EarthExplorerBaseType):
    def __init__(
        self,
        browse: List[Browse],
        cloud_cover: str,
        entity_id: str,
        display_id: str,
        metadata: List[MetadataField],
        options: Options,
        selected: Selected,
        spatial_bounds: SpatialBounds,
        spatial_coverage: SpatialBounds,
        temporal_coverage: TemporalCoverage,
        publish_date: str,
    ) -> None:
        """
        Scene data type

        .. note:: Order data type

        :param browse: An array of browse options
        :type browse: List[Browse]
        :param cloud_cover: The cloud cover score for this scene (-1 if score does not exist)
        :type cloud_cover: str
        :param entity_id: Entity Identifier
        :type entity_id: str
        :param display_id: Scene Identifier used for display
        :type display_id: str
        :param metadata: An array of metadata field for this scene
        :type metadata: List[MetadataField]
        :param options: An array of available download options for this scene
        :type options: Options
        :param selected: Denotes if the scene is selected for various systems
        :type selected: Selected
        :param spatial_bounds: Dataset Spatial Extent
        :type spatial_bounds: SpatialBounds
        :param spatial_coverage: Dataset spatial coverage
        :type spatial_coverage: SpatialBounds
        :param temporal_coverage: Dataset temporal coverage
        :type temporal_coverage: TemporalCoverage
        :param publish_date: The date the scene was published
        :type publish_date: str
        """
        self.browse: List[Browse] = browse
        self.cloudCover: str = cloud_cover
        self.entityId: str = entity_id
        self.displayId: str = display_id
        self.metadata: List[MetadataField] = metadata
        self.options: Options = options
        self.selected: Selected = selected
        self.spatialBounds: SpatialBounds = spatial_bounds
        self.spatialCoverage: SpatialBounds = spatial_coverage
        self.temporalCoverage: TemporalCoverage = temporal_coverage
        self.publishDate: str = publish_date


class IngestSubscription(EarthExplorerBaseType):
    def __init__(
        self,
        subscription_id: int,
        subscription_name: str,
        username: str,
        catalog_id: str,
        datasets: str,
        run_options: RunOptions,
        run_start_date: str,
        run_end_date: str,
        request_app: str,
        request_app_reference_id: str,
        run_frequency: str,
        status: str,
        date_entered: str,
        last_run_date: str,
        last_attempty_date: str,
    ) -> None:
        """
        Ingest Subscription data type

        .. note:: Subscription data type

        :param subscription_id: The unique Identifier for the subscription
        :type subscription_id: int
        :param subscription_name: Used for user reference to name a request
        :type subscription_name: str
        :param username: The user who created this subscription
        :type username: str
        :param catalog_id: The Machine-to-Machine dataset catalog being used
        :type catalog_id: str
        :param datasets: Used to identify datasets to search and the parameters specific to each dataset
        :type datasets: str
        :param run_options: Used to set subscription runtime configurations
        :type run_options: RunOptions
        :param run_start_date: Used to apply a temporal filter on the data based on ingest date
        :type run_start_date: str
        :param run_end_date: Used to apply a temporal filter on the data based on ingest date
        :type run_end_date: str
        :param request_app:
        :type request_app: str
        :param request_app_reference_id: The application that is creating the subscription
        :type request_app_reference_id: str
        :param run_frequency: Run this subscription at this interval
        :type run_frequency: str
        :param status: The status of the subscription
        :type status: str
        :param date_entered: The date this subscription was entered
        :type date_entered: str
        :param last_run_date: The date of the last run for this subscription
        :type last_run_date: str
        :param last_attempty_date: The date of the last attempt for this subscription
        :type last_attempty_date: str
        """
        self.subscriptionId: int = subscription_id
        self.subscriptionName: str = subscription_name
        self.username: str = username
        self.catalogId: str = catalog_id
        self.datasets: str = datasets
        self.runOptions: RunOptions = run_options
        self.runStartDate: str = run_start_date
        self.runEndDate: str = run_end_date
        self.requestApp: str = request_app
        self.requestAppReferenceId: str = request_app_reference_id
        self.runFrequency: str = run_frequency
        self.status: str = status
        self.dateEntered: str = date_entered
        self.lastRunDate: str = last_run_date
        self.lastAttemptDate: str = last_attempty_date


class IngestSubscriptionLog(EarthExplorerBaseType):
    def __init__(
        self,
        run_id: int,
        subscription_id: int,
        run_date: str,
        execution_time: str,
        num_scenes_matched: str,
        result_code: str,
        run_script_output: str,
        run_summary: str,
        run_options: RunOptions,
        datasets: str,
        catalog_id: str,
        last_run_date: str,
        order_ids: str,
        bulld_ids: str,
    ) -> None:
        """
        Ingest Subscription Log data type

        .. note:: Subscription data type

        :param run_id: The unique Identifier for this subscription run
        :type run_id: int
        :param subscription_id: The unique Identifier for the subscription
        :type subscription_id: int
        :param run_date: The date of this subscription run
        :type run_date: str
        :param execution_time: The number of seconds this subscription took to run
        :type execution_time: str
        :param num_scenes_matched: The number of scenes this subscription run matched
        :type num_scenes_matched: str
        :param result_code: The result of this subscription run
        :type result_code: str
        :param run_script_output: The output of this subscription run
        :type run_script_output: str
        :param run_summary: Any summary text associated with this subscription run
        :type run_summary: str
        :param run_options: Runtime configurations of this subscription run
        :type run_options: RunOptions
        :param datasets: Datasets of this subscription run
        :type datasets: str
        :param catalog_id: The Machine-to-Machine dataset catalog being used
        :type catalog_id: str
        :param last_run_date: The date of the last run for this subscription
        :type last_run_date: str
        :param order_ids: Tram order Identifier
        :type order_ids: str
        :param bulld_ids: Bulk order Identifier
        :type bulld_ids: str
        """
        self.runId: int = run_id
        self.subscriptionId: int = subscription_id
        self.runDate: str = run_date
        self.executionTime: str = execution_time
        self.numScencesMathed: str = num_scenes_matched
        self.resultCode: str = result_code
        self.runScriptOutput: str = run_script_output
        self.runSummary: str = run_summary
        self.runOptions: RunOptions = run_options
        self.datasets: str = datasets
        self.catalogId: str = catalog_id
        self.lastRunDate: str = last_run_date
        self.orderIds: str = order_ids
        self.bulkIds: str = bulld_ids


class SubscriptionDataset(EarthExplorerBaseType):
    def __init__(self, dataset_name: str) -> None:
        """
        Subscription Dataset data type

        .. note:: Subscription data type

        :param dataset_name: Dataset name
        :type dataset_name: str
        """
        self.datasetName: str = dataset_name


class TramOrder(EarthExplorerBaseType):
    def __init__(
        self,
        order_id: int,
        username: str,
        processing_priority: int,
        order_comment: str,
        status_code: str,
        status_code_text: str,
        date_entered: str,
        last_updated_date: str,
    ) -> None:
        """
        Tram Order data type

        .. note:: TRAM data type

        :param order_id: Order Identifier
        :type order_id: int
        :param username: The user who created this order
        :type username: str
        :param processing_priority: Processing priority for the order
        :type processing_priority: int
        :param order_comment: Comment contents of the order
        :type order_comment: str
        :param status_code: Internal status code
        :type status_code: str
        :param status_code_text: User friendly status
        :type status_code_text: str
        :param date_entered: The date this order was entered
        :type date_entered: str
        :param last_updated_date: Date the order was last updated
        :type last_updated_date: str
        """
        self.orderId: int = order_id
        self.username: str = username
        self.processingPriority: int = processing_priority
        self.orderComment: str = order_comment
        self.statusCode: str = status_code
        self.statusCodeText: str = status_code_text
        self.dateEntered: str = date_entered
        self.lastUpdatedDate: str = last_updated_date


class TramUnit(EarthExplorerBaseType):
    def __init__(
        self,
        unit_number: int,
        product_code: str,
        product_name: str,
        dataset_id: str,
        dataset_name: str,
        collection_name: str,
        ordering_id: str,
        unit_price: str,
        unit_comment: str,
        status_code: str,
        status_code_text: str,
        last_updated_date: str,
    ) -> None:
        """
        Tram Unit data type

        .. note:: TRAM data type

        :param unit_number: The unit Identifier
        :type unit_number: int
        :param product_code: Internal product code
        :type product_code: str
        :param product_name: The user friendly name for the product
        :type product_name: str
        :param dataset_id: Dataset identifer
        :type dataset_id: str
        :param dataset_name: Dataset name
        :type dataset_name: str
        :param collection_name: User friendly name of the collection
        :type collection_name: str
        :param ordering_id: Scene Identifier used within the ordering system
        :type ordering_id: str
        :param unit_price: The price for ordering this unit
        :type unit_price: str
        :param unit_comment: Any comments that should be retained with this product
        :type unit_comment: str
        :param status_code: Internal status code
        :type status_code: str
        :param status_code_text: User friendly status
        :type status_code_text: str
        :param last_updated_date: Date the unit was last updated
        :type last_updated_date: str
        """
        self.unitNumber: int = unit_number
        self.productCode: str = product_code
        self.productName: str = product_name
        self.datasetId: str = dataset_id
        self.datasetName: str = dataset_name
        self.collectionName: str = collection_name
        self.orderingId: str = ordering_id
        self.unitPrice: str = unit_price
        self.unitComment: str = unit_comment
        self.statusCode: str = status_code
        self.statusCodeText: str = status_code_text
        self.lastUpdatedDate: str = last_updated_date
