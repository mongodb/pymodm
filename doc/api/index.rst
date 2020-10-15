.. _api-documentation:

API Documentation
=================

.. warning::
   **MongoDB has paused the development of PyMODM.** If there are any users who want
   to take over and maintain this project, or if you just have questions, please respond
   to `this forum post <https://developer.mongodb.com/community/forums/t/updates-on-pymodm/9363>`_.

Welcome to the PyMODM API documentation.

Connecting
----------

.. automodule:: pymodm.connection

  .. autofunction:: connect

Defining Models
---------------

.. autoclass:: pymodm.MongoModel
   :members:
   :undoc-members:
   :inherited-members:

.. autoclass:: pymodm.EmbeddedMongoModel
   :members:
   :undoc-members:
   :inherited-members:

Model Fields
------------

.. autoclass:: pymodm.base.fields.MongoBaseField
   :members:

.. automodule:: pymodm.fields
   :members:
   :exclude-members: GeoJSONField, ReferenceField, GenericIPAddressField

   .. autoclass:: GenericIPAddressField
      :members:
      :member-order: bysource

   .. autoclass:: ReferenceField
      :members:
      :member-order: bysource

Managers
--------

.. automodule:: pymodm.manager
   :members:
   :undoc-members:

QuerySet
--------

.. automodule:: pymodm.queryset
   :members:
   :undoc-members:

Working with Files
------------------

.. automodule:: pymodm.files
   :members:
   :undoc-members:

Context Managers
----------------

.. automodule:: pymodm.context_managers
   :members:

Errors
------

.. automodule:: pymodm.errors
   :members:
