from typing import Union, Tuple, List, Optional, Literal
from pathlib import Path
import fiona

# TODO should be renamed to callusgs.Types
from callusgs.types import GeoJson, Coordinate


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
        coordinates: Union[Tuple[float], List[List[Tuple[float]]]] = first_feature.geometry[
            "coordinates"
        ]
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
