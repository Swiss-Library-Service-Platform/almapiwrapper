****************************
Almapi wrapper documentation
****************************

This python module is a tool to use Alma APIs. it manages the logs and the
backup of the records.

* Author: Raphaël Rey (raphael.rey@slsp.ch)
* Year: 2022
* Version: 0.5.0
* License: GNU General Public License v3.0

Introduction
============

How to import modules
---------------------

.. code-block:: python

    # Import libraries
    from almapiwrapper.users import User, NewUser, fetch_users, fetch_user_in_all_iz
    from almapiwrapper.inventory import IzBib, NzBib, Holding, Item
    from almapiwrapper.record import JsonData, XmlData
    from almapiwrapper.configlog import config_log
    from almapiwrapper import ApiKeys


Contents
--------

.. toctree::
   :maxdepth: 1

   getstarted
   tests


Module Almapi
-------------

.. toctree::
   :maxdepth: 2

   inventory
   users
   apikeys
   configlog
   jsonxmldata


Indices and tables
==================

* :ref:`genindex`
