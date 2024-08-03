.. _user_guide:

User Guide
==========

What should be added here???

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
