Tests
=====
The module has unittest test cases. These tests will only work in
SLSP environment.

To launch them all:

.. code-block:: bash

    python -m unittest discover

If you want to launch only specific tests:

.. code-block:: bash

    # Example for fetch_users function
    python -m test.test_fetchusers
