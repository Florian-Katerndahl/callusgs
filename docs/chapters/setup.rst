.. _setup:

Setup
=====

Installation
------------

``callUSGS`` can easily be installed via pip by running the following command:

.. code-block:: bash

    pip install callusgs

Alternatively, if you're only interested in the CLI functionality of this tool the best choice is probably to use `pipx <https://github.com/pypa/pipx>`_ for installation.

.. code-block:: bash

   pipx install callusgs

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
