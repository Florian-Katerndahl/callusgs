.. callUSGS documentation master file, created by
   sphinx-quickstart on Wed Jun 12 11:21:07 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

   # with overline, for parts
   * with overline, for chapters
   = for sections
   - for subsections
   ^ for subsubsections
   " for paragraphs

.. _main:

Home
====

.. is setup a good name? is user guide better? I don't know..; maybe Api Access should be a section within User Guide and/or setuo
.. toctree::
   :maxdepth: 2
   :caption: Contents
   :hidden:

   chapters/setup.rst
   User Guide <chapters/user_guide.rst>
   CLI Tools <chapters/cli.rst>
   chapters/cookbook.rst
   API Documentation <chapters/modules.rst>


``callusgs`` aims to be a complete and (mostly) typed implementation of USGS's machine-to-machine API (v1.5.0).
In addition, ``callusgs`` provides a suite of command line tools that can be used to query and download scenes, 
use the geocoding service provided by the USGSS and convert WRS 1/2 *coordinates* to geographic coordinates.

.. seealso::
   :ref:`setup`
      More detailed setup information for ``callusgs`` 

   :ref:`user_guide`
      How to provide ``callUSGS`` with your login credentials and other login methods.

   :ref:`api_restrictions`
      What can be expected to function when not applying for the MACHINE role.

Features
--------

``callusgs`` is both a Python package and a suite of command line tools that allows

#. Downloading of select products (see table below)
#. Access to the USGS *geocoding* API
#. Conversion between the WRS1 and WRS2 grids to geographic coordinates and
#. clean up of download order queues (mainly as utility functionality)

Currently supported products for download are:

+------------------------+--------------------------------------+
|   **Product string**   |           **Prodcut Name**           |
+========================+======================================+
| `landsat_em_c2_l1`     | Landsat 4/5 Collection 2 Level 1     |
+------------------------+--------------------------------------+
| `landsat_em_c2_l2`     | Landsat 4/5 Collection 2 Level 1     |
+------------------------+--------------------------------------+
| `landsat_etm_c2_l1`    | Landsat 7 Collection 2 Level 1       |
+------------------------+--------------------------------------+
| `landsat_etm_c2_l2`    | Landsat 7 Collection 2 Level 2       |
+------------------------+--------------------------------------+
| `landsat_ot_c2_l1`     | Landsat 8/9 Collection 2 Level 1     |
+------------------------+--------------------------------------+
| `landsat_ot_c2_l2`     | Landsat 8/9 Collection 2 Level 2     |
+------------------------+--------------------------------------+
| `landsat_ba_tile_c2`   | Landsat Burned Area Product          |
+------------------------+--------------------------------------+
| `landsat_dswe_tile_c2` | Landsat Dynamic Surface Water Extent |
+------------------------+--------------------------------------+
| `landsat_fsca_tile_c2` | Landsat Fractional Snow Covered Area |
+------------------------+--------------------------------------+
| `gmted2010`            | GMTED 2010 DEM                       |
+------------------------+--------------------------------------+

Installation
------------

Install the package together with the respective command line applications from pip.

.. code-block:: bash

   pip install callusgs

Alternatively, if you're only interested in the CLI functionality of this tool the best choice is probably to use `pipx <https://github.com/pypa/pipx>`_ for installation.

.. code-block:: bash

   pipx install callusgs

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
