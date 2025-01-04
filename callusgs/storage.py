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

NO_CONNECTION_WARNING: str = "No connection to database established"

class PersistentMetadata:
    """
    Class to handle and store metadata from landsat images
    """
    TABLE_NAME: str = "callusgs"
    FIELDS_DICT: Dict[str, Union[str, float]] = {
        "Landsat Scene Identifier": "landsat-scene-identifier",
        "Date Acquired": "date-acquired",
        "Collection Category": "collection-category",
        "Collection Number": "collection-number",
        "WRS Path": "wrs-path",
        "WRS Row": "wrs-row",
        "Land Cloud Cover": "land-cloud-cover",
        "Scene Cloud Cover L1": "scene-cloud-cover-l1",
        "Sensor Identifier": "sensor-identifier",
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
            landsat_scene_identifier TEXT PRIMARY KEY,
            date_acquired DATE,
            collection_category TEXT,
            collection_number INTEGER,
            wrs_path TEXT,
            wrs_row TEXT,
            land_cloud_cover REAL,
            scene_cloud_cover_l1 REAL,
            sensor_identifier TEXT,
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

    def write_scene_metadata(self, data: List, link: Optional[str]) -> None:
        """
        Insert scene metadata in addition to a download link to the metadata database

        :param data: raw JSON array returned from querying the ``scene-metadata`` endpoint
        :type data: List
        :param link: Download link to resource
        :type link: str
        """
        assert self.__connection_established(), NO_CONNECTION_WARNING

        db_data = self.__usgs_metadata_to_dict(data)
        db_data.update({"link": link, "download_successful": False})

        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO callusgs VALUES(
            :landsat_scene_identifier,
            :date_acquired,
            :collection_category,
            :collection_number,
            :wrs_path,
            :wrs_row,
            :land_cloud_cover,
            :scene_cloud_cover_l1,
            :sensor_identifier,
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
        assert self.__connection_established(), NO_CONNECTION_WARNING

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
        assert self.__connection_established(), NO_CONNECTION_WARNING

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
        assert self.__connection_established(), NO_CONNECTION_WARNING

        self.cursor.execute(
            "UPDATE callusgs SET download_successful = TRUE WHERE landsat_scene_identifier = ?;",
            (scene_identifier,),
        )
        self.connection.commit()

    def set_download_link(self, scene_identifier: str, link: str) -> None:
        assert self.__connection_established(), NO_CONNECTION_WARNING
        
        self.cursor.execute(
            "UPDATE callusgs set link = ? WHERE landsat_scene_identifier = ?;",
            (link, scene_identifier)
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
            if item["fieldName"] not in PersistentMetadata.FIELDS_DICT.keys():
                continue
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
