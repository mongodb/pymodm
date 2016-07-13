.. _api-documentation:

API Documentation
=================

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
