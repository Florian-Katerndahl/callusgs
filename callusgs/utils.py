from time import sleep
from typing import Union, Tuple, List, Optional, Literal, Dict
import logging
from pathlib import Path
import re

import fiona

from callusgs import Api
from callusgs.types import GeoJson, Coordinate
from callusgs.errors import RateLimitEarthExplorerException

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


def report_usgs_messages(messages) -> None:
    report_logger = logging.getLogger("callusgs.utils.reporter")
    if not messages:
        return

    for message in messages:
        if not isinstance(message, dict):
            continue
        report_logger.warning(
            f"USGS at {message['dateUpdated']} with severity '{message['severityText']}': {message['messageContent'].rstrip()}"
        )


def downloadable_and_preparing_scenes(data, available_entities=None):
    """
    _summary_

    :param data: _description_
    :type data: _type_
    :param available_entities: _description_, defaults to None
    :type available_entities: _type_, optional
    :return: _description_
    :rtype: _type_
    """
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
        utils_logger.error(f"Failed to download {v['entityId']}: {e}")

    return k


def get_user_rate_limits(connection: Api) -> List[int]:
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


def product_is_dem(product: str) -> bool:
    dem_pattern: re.Pattern = re.compile(r"^gmted2010")
    if dem_pattern.search(product):
        return True
    return False


def product_is_landsat(product: str) -> bool:
    ls_pattern: re.Pattern = re.compile(r"^landsat")
    if ls_pattern.search(product):
        return True
    return False
