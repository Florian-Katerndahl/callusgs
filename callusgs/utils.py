from argparse import Namespace
from time import sleep
from typing import Union, Tuple, List, Optional, Literal, Dict, Set, Iterable, TypeVar
from itertools import islice
import logging
from pathlib import Path
import re
import requests
import os

import fiona

from callusgs import Api
from callusgs.types import GeoJson, Coordinate, SceneFilter, AcquisitionFilter, CloudCoverFilter, SpatialFilterMbr, SpatialFilterGeoJson
from callusgs.errors import RateLimitEarthExplorerException
from callusgs.notifications import USGSNotificationParser

_T = TypeVar("_T")
SECONDS_PER_MINUTE = 60

utils_logger = logging.getLogger("callusgs.utils")


def ogr2internal(
    path: Path, type: Optional[Literal["Coordinates", "Mbr"]] = "Coordinates"
) -> Union[Tuple[Coordinate], GeoJson]:
    """
    Utility function to generate ogr compliant datasets to internal representation for API calls.

    .. note:: The supplied dataset must be in EPSG:4326.

    .. note:: Only 'Point' or 'Polygon' geometries are allowed.

    .. warning:: Should the supplied dataset contain either more than one layer and/or more than
        one feature, all but the first one are disregarded.

    :param path: File path to dataset
    :type path: Path
    :param type: What should be computed/accessed?, defaults to "Coordinates"
    :type type: Optional[Literal["Coordinates", "Mbr"]], optional
    :raises RuntimeError:
    :return: Return coordinate pair from minimal bounding rectangle (Mbr) or list of coordinates
    :rtype: Union[Tuple[Coordinate], GeoJson]
    """
    with fiona.open(path) as f:
        if fiona.crs.from_epsg(4326) != f.crs:
            raise RuntimeError("Supplied dataset is not in EPSG:426")
        if type == "Mbr":
            bbox = f.bounds
            ll, ur = bbox[:2], bbox[2:]
            return (Coordinate(*ll), Coordinate(*ur))

        n_features: int = len(f)
        if not n_features:
            raise RuntimeError("Dataset does not contain features.")
        if n_features > 1:
            raise RuntimeWarning(
                "Dataset provided contains more than one feature. Only using the first one!"
            )

        first_feature: fiona.Feature = next(iter(f))
        geometry_type: str = first_feature.geometry["type"]
        coordinates: Union[Tuple[float], List[List[Tuple[float]]]] = (
            first_feature.geometry["coordinates"]
        )
        if geometry_type not in ["Point", "Polygon"]:
            raise RuntimeError(
                f"Unsupported geometry type encountered: {geometry_type}, "
                "Only 'Point' and 'Polygon' are supported"
            )

        if isinstance(coordinates, tuple):
            return GeoJson(geometry_type, list(coordinates))

        out_coords: List[List[float]] = []
        for ring in coordinates:
            for coordinate in ring:
                out_coords.append(list(coordinate))
        return GeoJson(geometry_type, out_coords)


def month_names_to_index(month_list: List[str]) -> List[int]:
    mapping = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    out_list = []
    for month in month_list:
        if month != "all":
            out_list.append(mapping[month])
    return out_list


def report_usgs_messages(*messages) -> None:
    if not messages:
        return

    report_logger = logging.getLogger("callusgs.utils.reporter")
    message_set: Set[Tuple[str, str]] = set()
    for message in messages:
        if not isinstance(message, dict):
            continue
        parser = USGSNotificationParser()
        parser.feed(message['messageContent'])
        parser.close()
        message_set |= {(message['severityText'], str(parser)), }

    for message in message_set:
        report_logger.warning("%s: %s", message[0], message[1])


def report_dataset_messages(messages: Dict) -> None:
    report_logger = logging.getLogger("callusgs.utils.reporter")
    for id, message in messages.items():
        report_logger.warning("%s", message["dataset-select"]["message"])


def downloadable_and_preparing_scenes(data, available_entities=None):
    ueids = available_entities or set()
    preparing_ueids = set()
    download_dict = {}
    for i in data:
        if (eid := i["entityId"]) in ueids:
            continue
        if eid not in ueids and i["statusText"] in ["Proxied", "Available"]:
            ueids.add(eid)
            download_dict[i["downloadId"]] = {
                "displayId": i["displayId"],
                "entityId": eid,
                "url": i["url"],
            }
        elif i["statusText"] in ["Preparing", "Queued", "Staging"]:
            preparing_ueids.add(eid)
        else:
            raise RuntimeError("Don't know how you got here")

    return ueids, download_dict, preparing_ueids


def singular_download(download_item: Dict, connection: Api, outdir: Path) -> None:
    """
    _summary_

    .. note:: Concurrency is not reduced in case of reached rate limit!

    :param download_item: _description_
    :type download_item: Dict
    :param connection: _description_
    :type connection: Api
    :param outdir: _description_
    :type outdir: Path
    :return: _description_
    :rtype: _type_
    """
    k, v = download_item
    try:
        connection.download(v["url"], outdir)
        ## use download-remove with downloadId after successfull download to remove it from download queue
        connection.download_remove(k)
    except RateLimitEarthExplorerException:
        utils_logger.error("Rate Limit reached")
        download_count, _, _ = get_user_rate_limits(connection)
        if download_count == 0:
            utils_logger.error(
                "Maximum number of downloads (15 000) reached for the past 15 minutes. "
                "Thread will sleep for 15 minutes before continuing with download requests."
            )
            sleep(15 * SECONDS_PER_MINUTE)
    except RuntimeError as e:
        utils_logger.error("Failed to download %s: %s", v["entityId"], e)

    return k


def get_user_rate_limits(connection: Api) -> Tuple[int]:
    rate_limit_results = connection.rate_limit_summary()
    user_limits = [
        i
        for i in rate_limit_results.data["remainingLimits"]
        if i["limitType"] == "user"
    ].pop()
    return (
        user_limits["recentDownloadCount"],
        user_limits["pendingDownloadCount"],
        user_limits["unattemptedDownloadCount"],
    )


def product_is_gmted(product: str) -> bool:
    gmted_pattern: re.Pattern = re.compile(r"^gmted2010")
    if gmted_pattern.search(product):
        return True
    return False


def product_is_landsat(product: str) -> bool:
    ls_pattern: re.Pattern = re.compile(r"^landsat")
    if ls_pattern.search(product):
        return True
    return False


def product_is_srtm(product: str) -> bool:
    srtm_pattern: re.Pattern = re.compile(r"^srtm")
    if srtm_pattern.search(product):
        return True
    return False


def product_is_dem(product: str) -> bool:
    return product_is_gmted(product) or product_is_srtm(product)


def get_citation(doi_url: str) -> str:
    """
    Query doi.org webserver in order to retrieve complete bibtex entry

    .. note:: In general, the webserver queried does not matter. However,
      only objects of type ``application/x-bibtex`` are accepted.

    .. note:: The encoding is hardcoded to UTF-8.

    :param doi_url: URL to query (e.g. "https://doi.org/10.5066/P9IAXOVV")
    :type doi_url: str
    :return: Bibtex entry, possibly formatted.
    :rtype: str
    """
    bib_response = requests.get(doi_url, headers={"Accept": "application/x-bibtex"})
    bib_response.encoding = "utf-8"

    return bib_response.text


def cleanup_and_exit(connection: Api, label: str) -> None:
    connection.download_order_remove(label=label)
    utils_logger.debug("Removed order %s", label)

    exit(0)


def determine_log_level(verbose: bool, very_verbose: bool) -> int:
    """
    Determine the appropriate log level given user input

    :param verbose: User requested verbose output (info)
    :type verbose: bool
    :param very_verbose: User requested verbose output (debug)
    :type very_verbose: bool
    :return: Log level enum of logging library
    :rtype: int
    """
    info_or_warn: int = logging.INFO if verbose else logging.WARNING
    return logging.DEBUG if very_verbose else info_or_warn


def get_auth_from_environment() -> Tuple[str]:
    return os.environ.get("USGS_USERNAME"), os.environ.get("USGS_AUTH")


def get_every_other(iter: Iterable[_T], start: int) -> List[_T]:
    return list(islice(iter, start, len(iter), 2))


def zip_lists(*lists: Iterable[_T]) -> List[_T]:
    return list(zip(*lists))


def pack_list(in_list: List[_T]) -> List[List[_T]]:
    return [in_list]


def construct_aoi(aoi_coordinates: Optional[List[float]], aoi_path: Optional[Path], aoi_type: str) -> Union[GeoJson, Tuple[Coordinate]]:
    if aoi_coordinates:
        if len(aoi_coordinates) == 2:
            coordinates = GeoJson("Point", aoi_coordinates[::-1])
        else:
            coordinates = GeoJson(
                "Polygon",
                pack_list(
                    zip_lists(
                        get_every_other(aoi_coordinates, 1),
                        get_every_other(aoi_coordinates, 0)
                    )
                )
            )

        if coordinates.type == "Polygon" and aoi_type == "Mbr":
            coordinates = coordinates.mbr()
    elif aoi_path:
        coordinates = ogr2internal(aoi_path, aoi_type)
    else:
        raise ValueError("Either aoi_coordinates or aoi_path must NOT be None")
    
    return coordinates


def construct_filter(args: Namespace) -> SceneFilter:
    coordinates: Union[GeoJson, Tuple[Coordinate]] = construct_aoi(args.aoi_coordinates, args.aoi_file, args.aoi_type)

    s_filter: SceneFilter = SceneFilter(        
        acquisition_filter=AcquisitionFilter(*args.date),
        cloudcover_filter=CloudCoverFilter(
            *args.cloudcover, args.include_unknown_clouds
        ),
        dataset_name=args.product,
        ingest_filter=None,
        metadata_filter=None,
        seasonal_filter=(
            None if "all" in args.months else month_names_to_index(args.months)
        ),
        spatial_filter=(
            SpatialFilterMbr(*coordinates)
            if args.aoi_type == "Mbr"
            else SpatialFilterGeoJson(coordinates)
        ),
    )

    return s_filter
