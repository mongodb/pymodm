Changelog
=========

.. warning::
   **MongoDB has paused the development of PyMODM.** If there are any users who want
   to take over and maintain this project, or if you just have questions, please respond
   to `this forum post <https://developer.mongodb.com/community/forums/t/updates-on-pymodm/9363>`_.

Version 0.5.0.dev0
------------------

This release fixes a number of bug-fixes and improvements, including:

* Rename EmbeddedDocumentField to EmbeddedModelField and
  EmbeddedDocumentListField to EmbeddedModelListField.
* Deprecate EmbeddedDocumentField and EmbeddedDocumentListField.

For full list of the issues resolved in this release, visit
https://jira.mongodb.org/secure/ReleaseNote.jspa?projectId=13381&version=21201.


Version 0.4.1
-------------

This release includes a number of bug-fixes and improvements, including:

* Improve documentation.
* Improved support defining models before calling
  :meth:`~pymodm.connection.connect`.
* A field's :meth:`~pymodm.base.fields.MongoBaseField.to_python` method is no
  longer called on every access. It is only called on the first access after a
  call to :meth:`~pymodm.MongoModel.refresh_from_db` or, on the
  first access after a field is set.
* Fixed bug when appending to an empty :class:`~pymodm.fields.ListField`.

For full list of the issues resolved in this release, visit
https://jira.mongodb.org/secure/ReleaseNote.jspa?projectId=13381&version=18194.


Version 0.4.0
-------------

This release fixes a couple problems from the previous 0.3 release and adds a
number of new features, including:

* Support for callable field defaults.
* Change default values for DictField, OrderedDictField, ListField, and
  EmbeddedDocumentListField to be the empty value for their respective
  containers instead of None.
* Add the `ignore_unknown_fields`
  :ref:`metadata attribute <metadata-attributes>` which allows unknown
  fields when parsing documents into a :class:`~pymodm.MongoModel`.
  Note that with this option enabled, calling :meth:`~pymodm.MongoModel.save`
  will erase these fields for that model instance.
* Add :meth:`pymodm.queryset.QuerySet.reverse`.
* Properly check that the `mongo_name` parameter to
  :class:`~pymodm.base.fields.MongoBaseField`
  and all keys in :class:`~pymodm.fields.DictField` and
  :class:`~pymodm.fields.OrderedDictField` are valid MongoDB field names.
* Fix multiple issues in dereferencing fields thanks to
  https://github.com/ilex.


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
