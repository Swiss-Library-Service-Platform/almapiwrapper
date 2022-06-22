Get started
===========

Installation
------------

.. code-block::

    pip install almapi


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
