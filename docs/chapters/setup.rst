.. _setup:

Setup
=====

Installation
------------

``callUSGS`` can easily be installed via pip by running the following command:

.. code-block:: bash

    pip install callusgs

Alternatively, clone this repository and run ``poetry install`` to create a new virtual environment from which the package and programs are accessible.

Installing Extras
^^^^^^^^^^^^^^^^^

*To be filled*

EROS/USGS Account
-----------------

In order to use ``callUSGS``, an EROS/USSG account is needed. Please visit the `EROS registration system <https://ers.cr.usgs.gov/register>`_
if you don't already have an account. Additionally, access to "*EE's Machine to Machine interface (MACHINE)*" role is needed. To request access,
which is not automatically granted, visit the `Access Request page <https://ers.cr.usgs.gov/profile/access>`_ from your profile settings.

For fine-grained access control, it's recommended to authenticate with unique application tokens. They can be generated
`here <https://ers.cr.usgs.gov/password/appgenerate>`_. 

.. seealso::
    :ref:`user_guide`
        How to provide ``callUSGS`` with your login credentials and other login methods.

    :ref:`api_restrictions`
        What can be expected to function when not applying for the MACHINE role.

.. note::
    At the time of writing, it is unclear to me if the datasets spcifed at the time of registration have any impact on API access.
