"""
This module is called when executing the 'callusgs' command after installing callusgs.
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
from os import environ

from callusgs.cli_funcs import download, geocode, grid2ll, clean

parent_parser = ArgumentParser(
    prog="callusgs",
    formatter_class=ArgumentDefaultsHelpFormatter,
    epilog="Copyright: Florian Katerndahl <florian@katerndahl.com>",
)
parent_parser.add_argument(
    "--auth-method",
    type=str,
    choices=["password", "token", "sso", "app-guest"],
    default="token",
    help="Login method to use",
)
parent_parser.add_argument(
    "--username",
    default=environ.get("USGS_USERNAME"),
    type=str,
    help="Username to use for authentication",
)
parent_parser.add_argument(
    "--auth",
    default=environ.get("USGS_AUTH"),
    type=str,
    help="Appropriate authentication key (e.g. password, app token, etc.)",
)
parent_parser.add_argument(
    "--no-relogin",
    action="store_true",
    help="The USGS tokens used after login are only valid for two hours. If this flag is set, "
    "no automatic re-login is attempted.",
)
parent_parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Print more logging messages (INFO level and above)",
)
parent_parser.add_argument(
    "-vv",
    "--very-verbose",
    action="store_true",
    help="Print even more logging messages (DEBUG level and above)",
)
parent_parser.add_argument(
    "-d", "--dry-run", action="store_true", help="Do not perform action"
)

subparsers = parent_parser.add_subparsers(required=True)

report_parser = subparsers.add_parser(
    "report",
    help="Report help",
    epilog="Copyright: Florian Katerndahl <florian@katerndahl.com>",
)
report_parser.set_defaults(func=exit)

download_parser = subparsers.add_parser(
    "download",
    help="Download help",
    description="",
    formatter_class=ArgumentDefaultsHelpFormatter,
    epilog="Copyright: Florian Katerndahl <florian@katerndahl.com>",
)
download_parser.set_defaults(func=download)
download_parser.add_argument(
    "--cloudcover",
    type=int,
    nargs=2,
    default=[0, 100],
    help="Cloud cover range",
)
download_parser.add_argument(
    "--include-unknown-clouds",
    action="store_true",
    help="If specfied, include imagery with unknown cloud cover",
)
download_parser.add_argument(
    "--date",
    type=str,
    nargs=2,
    default=["2000-01-01", "2023-01-01"],
    help="Date range for query in YYYY-MM-DD format",
)
download_parser.add_argument(
    "--months",
    type=str,
    choices=[
        "all",
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ],
    nargs="+",
    default="all",
    required=False,
    help="Limit query to certain months in date range",
)
download_parser.add_argument(
    "--aoi-coordinates",
    type=float,
    nargs="+",
    required=False,
    help="Coordinate pair(s) given as latitude longitude pairs seperated by space. "
    "If a polygon, i.e. more than one coordinate pair, is supplied, it must be closed. "
    "[lat1 lon1 lat2 lon2 lat3 lon3 lat1 lon1]. Is overridden when aoi-file is specfiied "
    "as well",
)
download_parser.add_argument(
    "--aoi-file",
    type=Path,
    required=False,
    help="File containing point or polygon geometry in EPSG:4326 for spatial query. "
    "Should the supplied dataset contain either more than one layer and/or more than one "
    "feature, "
    "all but the first one are disregarded. Takes precedence over aoi-coordinates",
)
download_parser.add_argument(
    "--aoi-type",
    choices=["Mbr", "Coordinates"],
    required=False,
    default="coordinates",
    help="",
)
download_parser.add_argument(
    "--product",
    type=str,
    choices=[
        "landsat_em_c2_l1",
        "landsat_em_c2_l2",
        "landsat_etm_c2_l1",
        "landsat_etm_c2_l2",
        "landsat_ot_c2_l1",
        "landsat_ot_c2_l2",
        "landsat_ba_tile_c2",
        "landsat_dswe_tile_c2",
        "landsat_fsca_tile_c2",
        "gmted2010",
    ],
    required=True,
    help="Data product to query. Mapping is: landsat_em_c2_l1 => "
    "Landsat 4/5 Collection 2 Level 1, "
    "landsat_em_c2_l2 => Landsat 4/5 Collection 2 Level 2, "
    "landsat_etm_c2_l1 => Landsat 7 Collection 2 Level 1, "
    "landsat_etm_c2_l2 => Landsat 7 Collection 2 Level 2, "
    "landsat_ot_c2_l1 => Landsat 8/9 Collection 2 Level 1, "
    "landsat_ot_c2_l2 => Landsat 8/9 Collection 2 Level 2, "
    "landsat_ba_tile_c2 => Landsat Burned Area Product, "
    "landsat_dswe_tile_c2 => Landsat Dynamic Surface Water Extent, "
    "landsat_fsca_tile_c2 => Landsat Fractional Snow Covered Area, "
    "gmted2010 => GMTED 2010 DEM",
)
download_parser.add_argument(
    "--dem-resolution",
    type=str,
    choices=["7.5", "15", "30"],
    default="7.5",
    help="Resoltuion for Digital Elevation Model",
)
download_parser.add_argument(
    "outdir",
    type=Path,
    help="Path to directory where downloaded data should be stored. "
    "May not exist prior to program invocation",
)

geocode_parser = subparsers.add_parser(
    "geocode",
    help="Query the USGS Geocoder.",
    description="Query the USGS Geocoder.",
    formatter_class=ArgumentDefaultsHelpFormatter,
    epilog="Copyright: Florian Katerndahl <florian@katerndahl.com>",
)
geocode_parser.set_defaults(func=geocode)
geocode_parser.add_argument(
    "--feature-type",
    type=str,
    choices=["US", "World"],
    default="World",
    dest="feature",
    help="Type of feature. Where to look for.",
)
geocode_parser.add_argument("name", type=str, help="Name of the feature")

grid2ll_parser = subparsers.add_parser(
    "grid2ll",
    help="Translate between known grids and coordinates.",
    description="Translate between known grids and coordinates.",
    formatter_class=ArgumentDefaultsHelpFormatter,
    epilog="Copyright: Florian Katerndahl <florian@katerndahl.com>",
)
grid2ll_parser.set_defaults(func=grid2ll)
grid2ll_parser.add_argument(
    "--grid",
    type=str,
    choices=["WRS1", "WRS2"],
    default="WRS2",
    help="Which grid system is being used?",
)
grid2ll_parser.add_argument(
    "--response-shape",
    type=str,
    choices=["polygon", "point"],
    default="point",
    help="What type of geometry should be returned - "
    "a bounding box polygon or a center point?",
)
grid2ll_parser.add_argument(
    "coordinates",
    type=str,
    nargs="+",
    help="The xy coordinate pairs in the grid system. "
    "Coordinate pairs must be given as X1,Y1 X2,Y2 ...",
)

clean_parser = subparsers.add_parser(
    "clean",
    help="",
    description="",
    formatter_class=ArgumentDefaultsHelpFormatter,
    epilog="Copyright: Florian Katerndahl <florian@katerndahl.com>",
)
clean_parser.set_defaults(func=clean)

def main() -> int:
    """
    Poetry installs this function to run when executing 'callusgs' on the commandline

    :return: status code
    :rtype: int
    """
    args = parent_parser.parse_args()
    args.func(args)
