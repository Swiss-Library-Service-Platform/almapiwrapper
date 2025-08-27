Get started
===========

Installation
------------

.. code-block:: bash

    pip install almapiwrapper

You will then configure the API keys. You have to store them in a json file.
Here is a sample without the complete API keys:

.. code-block:: json

    {
      "apikeys": {
        "NZ": [
          {
            "API_Key": "l8xxkey1",
            "Name": "User management - Correction",
            "Supported_APIs": [
              {
                "Area": "Users",
                "Env": "S",
                "Permissions": "RW"
              }
            ]
          },
          {
            "API_Key": "l8xxkey2",
            "Name": "Get Analytics",
            "Supported_APIs": [
              {
                "Area": "Analytics",
                "Env": "P",
                "Permissions": "R"
              }
            ]
          }
        ],
        "BFH": [
          {
            "API_Key": "l8xxkey3",
            "Name": "User management - Correction",
            "Supported_APIs": [
              {
                "Area": "Users",
                "Env": "P",
                "Permissions": "RW"
              }
            ]
          }
        ]
      },
      "zones": {
        "NETWORK": "NZ",
        "EPFL": "EPF"
      }
    }


The API keys are grouped by IZ. Env can be either "P" for production or "S"
for sandbox. Permissions are either "RW" (read and write) or "R" (read). This file
can be stored anyway on the machine.

The "zones" section is optional. It is used to map the zone code to the IZ code.

.. note::
    You have to create a new environment variable **`alma_api_keys`** with the absolute path
    to this file.

Logs
----
It is possible to configure the logs. The log files are stored in the
`./log` folder.

.. code-block:: python

    from almapiwrapper import config_log

    # Will store the logs in the `./log/test.txt` file
    config_log("test")

Records backups
---------------
The `save` method of all records creates a backup of the record in the
`./records` folder.

Thresholds
----------
The program will exit if less than 5000 allowed API calls are remaining.
If the threshold of 25 API calls per second is exceeded the system waits
for 3 seconds. The API call is then sent again.

Inventory
---------
This mudule can use Alma APIs to manage bib records, holdings and items.

.. code-block:: python

    # Get bib record
    bib = IzBib('991000975799705520', 'HPH', 'S')

    # print XML data
    print(bib)

By changing the data of the `data` property, it is possible to make update
to the record.

.. code-block:: python


    # Get an item from barcode
    item = Item(barcode='03124510', zone='HPH', env='S')

    # Creat a backup of the record
    item.save()

    # Update the barcode using the property barcode (library and location also can be changed this way
    item.barcode = '03124510_NEW'

    # Update the internal note using the data property
    # We use lxml.etree.ElementTree to find the field and change its value
    item.data.find('item_data/internal_note_1').text = 'Note for testing'

    # Make the update in Alma
    item.update()


Users
-----
This module can use alma APIs to create, update and delete users. The data itself
are on json format stored in the :attr:`~.User.data` property of the :class:`almapi.users.User`
object.

.. code-block:: python

    # Load user data
    data = JsonData(filepath='test/data/user_test1.json')

    # Create object
    u = NewUser('UBS', 'S', data)

    # Create the user in Alma
    u.create()

    # Backup the record
    u.save()

    # Delete the record
    u.delete()

It is possible to chain all the methods.

.. code-block:: python

    data = JsonData(filepath='test/data/user_test1.json')

    NewUser('UBS', 'S', data).create().save().delete()

If there is any error, most methods are simply skipped. This way there is no
corruption, and the script should not encounter an interrupting exception.

Sets
----
This module can use Alma APIs to create and delete sets. It is also possible
to get the members of a set.

.. code-block:: python

    # Create a set
    s = NewLogicalSet('NZ',
                  'S',
                  'Series_1',
                  'Series_1',
                  'BIB_MMS where BIB_MMS ((mms_id GREATER_EQUAL "991020000000005501") AND BIB_MMS (mms_id LESS_THAN "991020001000005501") AND BIB_MMS (series NOT_EMPTY))',
                  'raphael.rey@slsp.ch',
                  True)
    # Create the set
    s = s.create()

    # Fetch the members
    members = s.get_members()

    # Delete the set
    s.delete()
