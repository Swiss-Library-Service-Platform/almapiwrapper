**********************************
Almapi wrapper documentation |doc|
**********************************


This python module is a tool to use Alma APIs. it manages the logs and the
backup of the records.

* Author: Raphaël Rey (raphael.rey@slsp.ch)
* Year: 2024
* Version: 1.2.0
* License: GNU General Public License v3.0

Introduction
============

How to import modules
---------------------

.. code-block:: python

    # Import libraries
    from almapiwrapper.users import User, NewUser, fetch_users, fetch_user_in_all_iz, Fee, Loan, Request, check_synchro, force_synchro
    from almapiwrapper.inventory import IzBib, NzBib, Holding, Item, Collection
    from almapiwrapper.config import RecSet, ItemizedSet, LogicalSet, NewLogicalSet, NewItemizedSet, Job, Library, Location, Desk, fetch_libraries
    from almapiwrapper.config import Reminder, fetch_reminders, Library, fetch_libraries, Location, OpenHours
    from almapiwrapper.record import JsonData, XmlData
    from almapiwrapper.analytics import AnalyticsReport
    from almapiwrapper.acquisitions import POLine, Vendor, Invoice, fetch_invoices
    from almapiwrapper.configlog import config_log
    from almapiwrapper import ApiKeys

    # Config logs
    config_log()


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
   acquisitions
   users
   config
   analytics
   apikeys
   configlog
   jsonxmldata


Indices and tables
==================

* :ref:`genindex`

.. |doc| image:: https://readthedocs.org/projects/almapi-wrapper/badge/?version=latest
    :target: https://almapi-wrapper.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
