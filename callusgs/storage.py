"""
The PersistentMetadata class is used to store metadata from queried
landsat images and track their download status
"""

import csv
import sqlite3
from pathlib import Path
import logging
from typing import Optional, Dict, List, Union, Tuple, Any

api_logger = logging.getLogger("callusgs.persistent")


class PersistentMetadata:
    """
    Class to handle and store metadata from landsat images
    """

    TABLE_NAME: str = "callusgs"
    FIELDS_DICT: Dict[str, Union[str, float]] = {
        "Landsat Product Identifier L2": "landsat-product-identifier-l2",
        "Landsat Product Identifier L1": "landsat-product-identifier-l1",
        "Landsat Scene Identifier": "landsat-scene-identifier",
        "Date Acquired": "date-acquired",
        "Collection Category": "collection-category",
        "Collection Number": "collection-number",
        "WRS Path": "wrs-path",
        "WRS Row": "wrs-row",
        "Target WRS Path": "target-wrs-path",
        "Target WRS Row": "target-wrs-row",
        "Nadir/Off Nadir": "nadir-off-nadir",
        "Roll Angle": "roll-angle",
        "Date Product Generated L2": "date-product-generated-l2",
        "Date Product Generated L1": "date-product-generated-l1",
        "Start Time": "start-time",
        "Stop Time": "stop-time",
        "Station Identifier": "station-identifier",
        "Day/Night Indicator": "day-night-indicator",
        "Land Cloud Cover": "land-cloud-cover",
        "Scene Cloud Cover L1": "scene-cloud-cover-l1",
        "Ground Control Points Model": "ground-control-points-model",
        "Ground Control Points Version": "ground-control-points-version",
        "Geometric RMSE Model": "geometric-rmse-model",
        "Geometric RMSE Model X": "geometric-rmse-model-x",
        "Geometric RMSE Model Y": "geometric-rmse-model-y",
        "Processing Software Version": "processing-software-version",
        "Sun Elevation L0RA": "sun-elevation-l0ra",
        "Sun Azimuth L0RA": "sun-azimuth-l0ra",
        "TIRS SSM Model": "tirs-ssm-model",
        "Data Type L2": "data-type-l2",
        "Sensor Identifier": "sensor-identifier",
        "Satellite": "satellite",
        "Product Map Projection L1": "product-map-projection-l1",
        "UTM Zone": "utm-zone",
        "Datum": "datum",
        "Ellipsoid": "ellipsoid",
        "Scene Center Lat DMS": "scene-center-lat-dms",
        "Scene Center Long DMS": "scene-center-long-dms",
        "Corner Upper Left Lat DMS": "corner-upper-left-lat-dms",
        "Corner Upper Left Long DMS": "corner-upper-left-long-dms",
        "Corner Upper Right Lat DMS": "corner-upper-right-lat-dms",
        "Corner Upper Right Long DMS": "corner-upper-right-long-dms",
        "Corner Lower Left Lat DMS": "corner-lower-left-lat-dms",
        "Corner Lower Left Long DMS": "corner-lower-left-long-dms",
        "Corner Lower Right Lat DMS": "corner-lower-right-lat-dms",
        "Corner Lower Right Long DMS": "corner-lower-right-long-dms",
        "Scene Center Latitude": "scene-center-latitude",
        "Scene Center Longitude": "scene-center-longitude",
        "Corner Upper Left Latitude": "corner-upper-left-latitude",
        "Corner Upper Left Longitude": "corner-upper-left-longitude",
        "Corner Upper Right Latitude": "corner-upper-right-latitude",
        "Corner Upper Right Longitude": "corner-upper-right-longitude",
        "Corner Lower Left Latitude": "corner-lower-left-latitude",
        "Corner Lower Left Longitude": "corner-lower-left-longitude",
        "Corner Lower Right Latitude": "corner-lower-right-latitude",
        "Corner Lower Right Longitude": "corner-lower-right-longitude",
        "link": "link",
        "download_successful": "download_successful",
    }

    def __init__(self, db: Path) -> None:
        """
        Constructor of "PersistentMetadata" class

        :param db: Path to database, may not exist prior to invocation
        :type db: Path
        """
        self.db: Path = db
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.logger = logging.getLogger("callusgs.persistent.DB")
        self.logger.setLevel(logging.DEBUG)

    def connect_database(self) -> None:
        """
        Connect to database

        :raises RuntimeError: If connection was already established.
        """
        if self.__connection_established():
            raise RuntimeError("Connection to database already established")
        self.logger.debug(f"Creating database {self.db}")
        self.connection = sqlite3.connect(self.db)
        self.cursor = self.connection.cursor()

    def disconnect_database(self) -> None:
        """
        Close connection to database
        """
        self.connection.close()

    def create_metadata_table(self) -> None:
        """
        Create metadata table, if it does not exist already
        """
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS callusgs (                
            landsat_product_identifier_l2 TEXT,
            landsat_product_identifier_l1 TEXT,
            landsat_scene_identifier TEXT PRIMARY KEY,
            date_acquired DATE,
            collection_category TEXT,
            collection_number INTEGER,
            wrs_path TEXT,
            wrs_row TEXT,
            target_wrs_path TEXT,
            target_wrs_row TEXT,
            nadir_off_nadir TEXT,
            roll_angle REAL,
            date_product_generated_l2 DATE,
            date_product_generated_l1 DATE,
            start_time DATETIME,
            stop_time DATETIME,
            station_identifier TEXT,
            day_night_indicator TEXT,
            land_cloud_cover REAL,
            scene_cloud_cover_l1 REAL,
            ground_control_points_model INTEGER,
            ground_control_points_version INTEGER,
            geometric_rmse_model REAL,
            geometric_rmse_model_x REAL,
            geometric_rmse_model_y REAL,
            processing_software_version TEXT,
            sun_elevation_l0ra REAL,
            sun_azimuth_l0ra REAL,
            tirs_ssm_model TEXT,
            data_type_l2 TEXT,
            sensor_identifier TEXT,
            satellite INTEGER,
            product_map_projection_l1 TEXT,
            utm_zone INTEGER,
            datum TEXT,
            ellipsoid TEXT,
            scene_center_lat_dms TEXT,
            scene_center_long_dms TEXT,
            corner_upper_left_lat_dms TEXT,
            corner_upper_left_long_dms TEXT,
            corner_upper_right_lat_dms TEXT,
            corner_upper_right_long_dms TEXT,
            corner_lower_left_lat_dms TEXT,
            corner_lower_left_long_dms TEXT,
            corner_lower_right_lat_dms TEXT,
            corner_lower_right_long_dms TEXT,
            scene_center_latitude REAL,
            scene_center_longitude REAL,
            corner_upper_left_latitude REAL,
            corner_upper_left_longitude REAL,
            corner_upper_right_latitude REAL,
            corner_upper_right_longitude REAL,
            corner_lower_left_latitude REAL,
            corner_lower_left_longitude REAL,
            corner_lower_right_latitude REAL,
            corner_lower_right_longitude REAL,
            link TEXT,
            download_successful BOOL DEFAULT FALSE
            );            
            """
        )

    def check_for_metadata_table(self) -> bool:
        """
        Check if metadata table is present in database

        :return: True if table is present, False otherwise
        :rtype: bool
        """
        res: List = self.cursor.execute("SELECT name FROM sqlite_master")
        table_present = any(
            [PersistentMetadata.TABLE_NAME in table for table in res.fetchall()]
        )
        return table_present

    def write_scene_metadata(self, data: List, link: str) -> None:
        """
        Insert scene metadata in addition to a download link to the metadata database

        :param data: raw JSON array returned from querying the ``scene-metadata`` endpoint
        :type data: List
        :param link: Download link to resource
        :type link: str
        """
        assert self.__connection_established(), "No connection to database established"

        db_data = self.__usgs_metadata_to_dict(data)
        db_data.update({"link": link, "download_successful": False})

        self.cursor.executemany(
            """
            INSERT INTO callusgs VALUES(
            :landsat_product_identifier_l2,
            :landsat_product_identifier_l1,
            :landsat_scene_identifier,
            :date_acquired,
            :collection_category,
            :collection_number,
            :wrs_path,
            :wrs_row,
            :target_wrs_path,
            :target_wrs_row,
            :nadir_off_nadir,
            :roll_angle,
            :date_product_generated_l2,
            :date_product_generated_l1,
            :start_time,
            :stop_time,
            :station_identifier,
            :day_night_indicator,
            :land_cloud_cover,
            :scene_cloud_cover_l1,
            :ground_control_points_model,
            :ground_control_points_version,
            :geometric_rmse_model,
            :geometric_rmse_model_x,
            :geometric_rmse_model_y,
            :processing_software_version,
            :sun_elevation_l0ra,
            :sun_azimuth_l0ra,
            :tirs_ssm_model,
            :data_type_l2,
            :sensor_identifier,
            :satellite,
            :product_map_projection_l1,
            :utm_zone,
            :datum,
            :ellipsoid,
            :scene_center_lat_dms,
            :scene_center_long_dms,
            :corner_upper_left_lat_dms,
            :corner_upper_left_long_dms,
            :corner_upper_right_lat_dms,
            :corner_upper_right_long_dms,
            :corner_lower_left_lat_dms,
            :corner_lower_left_long_dms,
            :corner_lower_right_lat_dms,
            :corner_lower_right_long_dms,
            :scene_center_latitude,
            :scene_center_longitude,
            :corner_upper_left_latitude,
            :corner_upper_left_longitude,
            :corner_upper_right_latitude,
            :corner_upper_right_longitude,
            :corner_lower_left_latitude,
            :corner_lower_left_longitude,
            :corner_lower_right_latitude,
            :corner_lower_right_longitude,
            :link,
            :download_successful
            );
            """,
            (db_data,),
        )
        self.connection.commit()

    def query_unfinished_downloads(self) -> List[Tuple[str]]:
        """
        Query all scenes that are not marked as downloaded

        :return: _description_
        :rtype: List[Tuple[str]]
        """
        assert self.__connection_established(), "No connection to database established"

        res = self.cursor.execute(
            """
            SELECT landsat_scene_identifier, link
            FROM callusgs
            WHERE download_successful = FALSE;
            """
        )
        return res.fetchall()

    def query_database(
        self, query_string: str, placeholders: Optional[Union[Tuple, Dict]] = None
    ) -> Union[List[Tuple[Any]], List]:
        """
        Arbitrary query into metadata database

        :param query_string: SQL query
        :type query_string: str
        :param placeholders: Placeholders used in query, defaults to None
        :type placeholders: Optional[Union[Tuple, Dict]], optional
        :return: All database row that were returned according to ``query_string``
        :rtype: Union[List[Tuple[Any]], List]
        """
        assert self.__connection_established(), "No connection to database established"

        if placeholders is None:
            res = self.cursor.execute(query_string)
        else:
            res = self.cursor.execute(query_string, parameters=placeholders)
        return res.fetchall()

    def export_summary_csv(self, destination: Path) -> None:
        """
        Export entire metadata database as a flat csv file

        .. note:: Exported CSV file uses 'excel' dialect.

        .. warning:: This operation may be slow on large databases

        :param destination: Output file path
        :type destination: Path
        """
        with open(destination, "wt", encoding="utf-8") as csvfile:
            summary_writer = csv.writer(csvfile, dialect="excel")
            summary_writer.writerow(PersistentMetadata.FIELDS_DICT.values())
            for row in self.cursor.execute("SELECT * FROM callusgs"):
                summary_writer.writerow(row)

    def mark_scene_as_done(self, scene_identifier: str) -> None:
        """
        Set the ``download_successful`` field to True for a given scene_identifier

        :param scene_identifier: Scene to update
        :type scene_identifier: str
        """
        assert self.__connection_established(), "No connection to database established"

        self.cursor.execute(
            "UPDATE callusgs SET download_successful = TRUE WHERE landsat_scene_identifier = ?;",
            (scene_identifier,),
        )
        self.connection.commit()

    def delete_completed_scens(self) -> None:
        """
        Remove all sucessfully downloaded scences from the database
        """
        self.cursor.execute("DELETE FROM callusgs WHERE download_successful = TRUE;")
        self.connection.commit()

    def __connection_established(self) -> bool:
        """
        Check if there is an active connection to a database

        :return: True if a connection is found, False otherwise
        :rtype: bool
        """
        return self.connection is not None

    def __usgs_metadata_to_dict(self, data: List) -> Dict:
        """
        Convert the list of metadata items returned by the ``scene-metadata`` endpoint
          into internal dict representation with parsing of numerics

        :param data: List of metadata items the USGS provides
        :type data: List
        :return: Internal dict representation
        :rtype: Dict
        """
        out = {}
        for item in data:
            k = item["fieldName"].lower().replace(" ", "_").replace("/", "_")
            v = item["value"]
            try:
                if not isinstance(v, int):
                    v = float(v) if "." in v else int(v)
            except ValueError:
                pass
            finally:
                out[k] = v

        return out
