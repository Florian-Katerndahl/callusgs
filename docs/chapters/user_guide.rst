.. _user_guide:

User Guide
==========

This chapter provides a brief overview of *gotchas* and things to watch out for when using ``callusgs``.

.. _api_restrictions:

API Restrictions
----------------

As outlined in :ref:`the setup section <setup>`, your account needs access to the MACHINE role in order
to use the Api to its full potential.

.. table:: Api functionality without access to the MACHINE role
    :widths: auto
    :align: center

    +-----------------------------------------------+--------+---------------------------------------+
    | Feature/Functionality                         | Usable | Note                                  |
    +===============================================+========+=======================================+
    | Searching for scenes                          | Yes    |                                       |
    +-----------------------------------------------+--------+---------------------------------------+
    | Creating scene lists out of search results    | Yes    |                                       |
    +-----------------------------------------------+--------+---------------------------------------+
    | | Generate orders from scene searches         | No     | | Downloading orders from list, when  |
    | | or scene lists                              |        | | order was placed via webinterface   |
    | |                                             |        | | is possible                         |
    +-----------------------------------------------+--------+---------------------------------------+
    | Geocoding                                     | Yes    |                                       |
    +-----------------------------------------------+--------+---------------------------------------+
    | WRS1/WRS2 to coordinate transformation        | Yes    |                                       |
    +-----------------------------------------------+--------+---------------------------------------+

All Api methods of ``callUSGS`` that are only accessible when have the MACHINE role assigned to your account
are marked the warning below:

.. warning:: This method is only documented and accessible, when having the MACHINE role assigned to your account.

.. _gotchas:

Gotchas
-------

- Specifying coordinates on the command line instead of providing a file requries the use of ``--`` to
  signal ``argparse`` the end of input
- blocking download queue
- ...