Changelog
=========

Version 0.4.0
-------------

This release fixes a couple problems from the previous 0.3 release and adds a
number of new features, including:

* Support for callable field defaults.
* Change default values for DictField, OrderedDictField, ListField, and
  EmbeddedDocumentListField to be the empty value for their respective
  containers instead of None.
* Add :data:`pymodm.base.options.MongoOptions.ignore_unknown_fields` method
  to allow unknown fields when parsing documents into model. Note that with
  this option enabled, calling :meth:`~pymodm.MongoModel.save` will erase
  these fields for that model instance.
* Add :meth:`pymodm.queryset.QuerySet.reverse`.
* Stricter validation of MongoDB field names in
  :class:`~pymodm.fields.DictField` and
  :class:`~pymodm.fields.OrderedDictField`.
* Properly check that :attr:`pymodm.base.fields.MongoBaseField.mongo_name`
  and all keys in :class:`~pymodm.fields.DictField` and
  :class:`~pymodm.fields.OrderedDictField` are valid MongoDB field names.


For full list of the issues resolved in this release, visit
https://jira.mongodb.org/browse/PYMODM/fixforversion/17785.

Version 0.3.0
-------------

This release fixes a couple problems from the previous 0.2 release and adds a
number of new features, including:

* Support for `collations`_ in MongoDB 3.4
* Add a :meth:`pymodm.queryset.QuerySet.project` method to
  :class:`pymodm.queryset.QuerySet`.
* Allow :class:`~pymodm.fields.DateTimeField` to parse POSIX timestamps
  (i.e. seconds from the epoch).
* Fix explicit validation of blank fields.

For full list of the issues resolved in this release, visit
https://jira.mongodb.org/browse/PYMODM/fixforversion/17662.

.. _collations: https://docs.mongodb.com/manual/reference/collation/

Version 0.2.0
-------------

This version fixes a few issues and allows defining indexes inside the `Meta`
class in a model.

For a complete list of the issues resolved in this release, visit
https://jira.mongodb.org/browse/PYMODM/fixforversion/17609.

Version 0.1.0
-------------

This version is the very first release of PyMODM.
