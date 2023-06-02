**********************************
Almapi wrapper documentation |doc|
**********************************


This python module is a tool to use Alma APIs. it manages the logs and the
backup of the records.

* Author: Raphaël Rey (raphael.rey@slsp.ch)
* Year: 2022
* Version: 0.13.5
* License: GNU General Public License v3.0

Introduction
============

How to import modules
---------------------

.. code-block:: python

    # Import libraries
    from almapiwrapper.users import User, NewUser, fetch_users, fetch_user_in_all_iz, Fee, Loan, check_synchro
    from almapiwrapper.inventory import IzBib, NzBib, Holding, Item
    from almapiwrapper.record import JsonData, XmlData
    from almapiwrapper.config import RecSet, NewRecSet, Job, Reminder, fetch_reminders
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
   users
   config
   apikeys
   configlog
   jsonxmldata


Indices and tables
==================

* :ref:`genindex`

.. |doc| image:: https://readthedocs.org/projects/almapi-wrapper/badge/?version=latest
    :target: https://almapi-wrapper.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
