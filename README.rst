======
PyMODM
======


.. image:: http://jenkins.bci.10gen.cc:8080/job/pymodm/badge/icon
   :alt: View build status
   :target: http://jenkins.bci.10gen.cc:8080/job/pymodm

.. image:: https://badges.gitter.im/mongodb/pymodm.svg
   :alt: Join the chat at https://gitter.im/mongodb/pymodm
   :target: https://gitter.im/mongodb/pymodm?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

A generic ODM around PyMongo_, the MongoDB Python driver. Its goal is to provide
an easy, object-oriented interface to MongoDB documents. PyMODM works on Python
2.7 as well as Python 3.3 and up. To learn more, you can browse the `official
documentation`_ or take a look at some `examples`_.

.. _PyMongo: https://pypi.python.org/pypi/pymongo
.. _official documentation: https://pymodm.readthedocs.io
.. _examples: https://github.com/mongodb/pymodm/tree/master/example

Support / Feedback
==================

For issues with, questions about, or feedback for PyMODM, please look into
our `support channels <http://www.mongodb.org/about/support>`_. Please do not
email any of the PyMODM developers directly with issues or questions -
you're more likely to get an answer on the `mongodb-user
<http://groups.google.com/group/mongodb-user>`_ list on Google Groups.

Bugs / Feature Requests
=======================

Think you’ve found a bug? Want to see a new feature in PyMODM? open
a case in our issue management tool, JIRA:

- `Create an account and login <https://jira.mongodb.org>`_.
- Navigate to `the PYMODM project <https://jira.mongodb.org/browse/PYMODM>`_.
- Click **Create Issue** - Please provide as much information as possible about the issue type and how to reproduce it.

Bug reports in JIRA for all driver projects (e.g. PYMODM, PYTHON, JAVA) and the
Core Server (i.e. SERVER) project are **public**.

How To Ask For Help
-------------------

Please include all of the following information when opening an issue:

- Detailed steps to reproduce the problem, including full traceback, if possible.
- The exact python version used, with patch level::

  $ python -c "import sys; print(sys.version)"

- The exact version of PyMODM used, with patch level::

  $ python -c "import pymodm; print(pymodm.version)"

- The PyMongo version used, with patch level::

  $ python -c "import pymongo; print(pymongo.version)"

- The operating system and version (e.g. Windows 7, OSX 10.8, ...)
- Web framework or asynchronous network library used, if any, with version (e.g.
  Django 1.7, mod_wsgi 4.3.0, gevent 1.0.1, Tornado 4.0.2, ...)

Security Vulnerabilities
------------------------

If you’ve identified a security vulnerability in a driver or any other
MongoDB project, please report it according to the `instructions here
<http://docs.mongodb.org/manual/tutorial/create-a-vulnerability-report>`_.

Example
=======

Here's a basic example of how to define some models and connect them to MongoDB:

.. code-block:: python

  from pymodm import connect, fields, MongoModel, EmbeddedMongoModel


  # Connect to MongoDB first. PyMODM supports all URI options supported by
  # PyMongo. Make sure also to specify a database in the connection string:
  connect('mongodb://localhost:27017/myApp')


  # Now let's define some Models.
  class User(MongoModel):
      # Use 'email' as the '_id' field in MongoDB.
      email = fields.EmailField(primary_key=True)
      fname = fields.CharField()
      lname = fields.CharField()


  class BlogPost(MongoModel):
      # This field references the User model above.
      # It's stored as a bson.objectid.ObjectId in MongoDB.
      author = fields.ReferenceField(User)
      title = fields.CharField(max_length=100)
      content = fields.CharField()
      tags = fields.ListField(fields.StringField(max_length=20))
      # These Comment objects will be stored inside each Post document in the
      # database.
      comments = fields.EmbeddedDocumentListField('Comment')


  # This is an "embedded" model and will be stored as a sub-document.
  class Comment(EmbeddedMongoModel):
      author = fields.ReferenceField(User)
      body = fields.CharField()
      vote_score = fields.IntegerField(min_value=0)


  # Start the blog.
  # We need to save these objects before referencing them later.
  han_solo = User('mongoblogger@reallycoolmongostuff.com', 'Han', 'Solo').save()
  chewbacca = User(
      'someoneelse@reallycoolmongostuff.com', 'Chewbacca', 'Thomas').save()


  post = BlogPost(
      # Since this is a ReferenceField, we had to save han_solo first.
      author=han_solo,
      title="Five Crazy Health Foods Jabba Eats.",
      content="...",
      tags=['alien health', 'slideshow', 'jabba', 'huts'],
      comments=[
          Comment(author=chewbacca, body='Rrrrrrrrrrrrrrrr!', vote_score=42)
      ]
  ).save()


  # Find objects using familiar MongoDB-style syntax.
  slideshows = BlogPost.objects.raw({'tags': 'slideshow'})

  # Only retrieve the 'title' field.
  slideshow_titles = slideshows.only('title')

  # u'Five Crazy Health Foods Jabba Eats.'
  print(slideshow_titles.first().title)
