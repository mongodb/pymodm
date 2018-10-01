Getting Started with PyMODM
===========================

This document provides a gentle introduction to ``pymodm`` and goes over
everything you'll need to write your first application.

Installation
------------

You can install ``pymodm`` with `pip <https://pypi.python.org/pypi/pip>`_::

    pip install pymodm

Of course, you'll probably want to have a copy of MongoDB itself running, so you
can test your app. You can download it for free from `www.mongodb.com
<http://www.mongodb.com>`_.

Connecting to MongoDB
---------------------

Now that we have all the components, let's connect them together. In ``pymodm``,
you connect to MongoDB by calling the :func:`~pymodm.connection.connect`
function::

    from pymodm.connection import connect

    # Connect to MongoDB and call the connection "my-app".
    connect("mongodb://localhost:27017/myDatabase", alias="my-app")

Let's go through what we just did above. First, we imported the
:func:`~pymodm.connection.connect` method from the :mod:`~pymodm.connection`
module. Then, we established a connection using a `MongoDB connection string
<http://docs.mongodb.org/manual/reference/connection-string>`_. A MongoDB
connection string always starts with ``mongodb://`` and can include a multitude
of connection options. It's important to note that the connection string
provided to ``connect`` **must** include a database name ("myDatabase"
above). This is the database where all data will reside within your PyMODM
application by default.

Another thing we did when we called ``connect`` is that we provided an *alias*
for the connection ("my-app"). Although providing an alias is optional, doing so
may come in handy later, if we ever need to refer to the connection by
name. This is useful if we want to have models that use different connection
options, or if we ever want to switch what connection a model is using.

Defining Models
---------------

Now that we have at least one connection to MongoDB open, we're ready to define
our model classes. :class:`~pymodm.MongoModel` is the base class for all
top-level models, which represent the data we have stored in MongoDB in a
convenient object-oriented way.

Basic Models
............

Typically, the definition of a MongoModel class will include one or more fields
and optionally some metadata, encapsulated in an inner class called
``Meta``. Take this example::

    from pymongo.write_concern import WriteConcern

    from pymodm import MongoModel, fields

    class User(MongoModel):
        email = fields.EmailField(primary_key=True)
        first_name = fields.CharField()
        last_name = fields.CharField()

        class Meta:
            write_concern = WriteConcern(j=True)
            connection_alias = 'my-app'

Our model, ``User``, represents documents in the ``myDatabase.user`` collection
in MongoDB. A few things to notice here:

- Our ``User`` model extends :class:`~pymodm.MongoModel`. This means that it
  will get its own collection in the database. Any class that inherits
  *directly* from MongoModel always gets its own collection.
- We gave ``User`` three fields: ``first_name``, ``last_name``, and
  ``email``. CharField and EmailField always store their values as unicode
  strings. The ``email`` field will also validate its contents as an email
  address.
- In the ``Meta`` class, we defined a couple pieces of metadata. First, we
  defined the ``write_concern`` attribute, which tells the Model what `write
  concern <https://docs.mongodb.com/manual/reference/write-concern/>`_ to use by
  default. We also set the ``connection_alias``, which tells the model what
  connection to use. In this case, we're using the connection that we defined
  earlier, which we gave the name of ``my-app``. Note that we have to call
  :func:`~pymodm.connection.connect` with the ``my-app`` alias before using this
  model, since it relies on the ``my-app`` connection.
- We set ``primary_key=True`` in the ``email`` field. This means that this field
  will be used as the id for documents of this MongoModel class. Note that this
  field will actually be called ``_id`` in the database.

.. seealso:: The :mod:`~pymodm.fields` module.
.. seealso:: The list of available :ref:`metadata attributes <metadata-attributes>`.

.. _GettingStartedReferenceExample:

Models that Reference Other Models
..................................

Sometimes, our models will need to reference other models. In MongoDB, there are
a couple approaches to this:

1. We can store the ``_id`` of the document we want to reference. When we later
   need the actual document, we can look it up based on this id. If we need to
   reference multiple documents, we can store these ids in a list.

2. If we don't need to query the referenced documents outside of our reference
   structure, we might just embed such documents directly inside the documents
   that reference them. Similarly, if we have multiple documents we need to
   reference, we can just have a list of these embedded documents.

Let's take a look at a couple examples of some models that reference the
``User`` model we wrote earlier::

    from pymodm import EmbeddedMongoModel, MongoModel, fields

    class Comment(EmbeddedMongoModel):
        author = fields.ReferenceField(User)
        content = fields.CharField()

    class Post(MongoModel):
        title = fields.CharField()
        author = fields.ReferenceField(User)
        revised_on = fields.DateTimeField()
        content = fields.CharField()
        comments = fields.EmbeddedModelListField(Comment)

Here we've defined two additional model types: ``Comment`` and ``Post``. These
two models demonstrate the two approaches discussed earlier: both ``Comment``
and ``Post`` have an author, which is a ``User`` model. The ``User`` that
represents the author in each case is stored among all the other Users in the
``myDatabase.user`` collection. In ``Comment`` and ``Post`` models, we're just
storing the ``_id`` of the ``User`` in the ``author`` field. This is actually
the same as the User's ``email`` field, since we set ``primary_key=True`` for
that field earlier.

``Post`` gets a little more interesting. In order to support commenting on a
``Post``, what we've done is added a ``comments`` field, which is an
:class:`~pymodm.fields.EmbeddedModelListField`. This represents the second
approach we discussed, where ``Comment`` objects are embedded directly into our
``Post`` object. The downside to doing this is that it is difficult to
query for individual ``Comment`` objects. The upside is that we won't have to
make an additional query to retrieve all the comments associated with a given
``Post``.

.. seealso:: `Model Relationships Between Documents <https://docs.mongodb.com/manual/applications/data-models-relationships/>`_

Deleted References
..................

Now that we've defined models that reference other model types, we face another
challenge: what happens if a ``User`` object is deleted? If one of our beloved
authors decides to quit the commenting/posting scene, what is to become of their
comments and posts? ``pymodm`` gives us a few options:

- Do nothing (this is the default behavior)
- Change fields that reference the deleted object to ``None``.
- Cascade the deletes: when a referenced object is deleted, recursively delete
  all objects that were referencing it.
- Don't allow deleting objects that still have references to them.
- If the deleted object was just one among potentially many other references
  stored in a list, remove the reference from this list.

In our case for the ``Comment`` and ``Post`` objects, let's delete any comments
and posts associated with a ``User`` after they're gone. This would be the
changed definition of the ``author`` field in each case::

    author = fields.ReferenceField(User, on_delete=ReferenceField.CASCADE)

.. seealso:: The :class:`~pymodm.fields.ReferenceField` class.

Creating Data
-------------

Alright, now that we've defined models for each MongoDB collection our app will
use, let's create some documents!

Saving a Single Instance
........................

Here's one way to set up our first User::

    User('user@email.com', 'Bob', 'Ross').save()

Above, we used positional arguments to construct an instance of
``User``. Positional arguments are assigned to fields in the order they were
defined in the ``User`` class. We can also use keyword arguments or a mix of
positional/keyword arguments to create MongoModel instances, so this would be
equivalent::

    User('user@email.com', last_name='Ross', first_name='Bob').save()

Finally, calling :meth:`~pymodm.MongoModel.save` on the instance persists it to
the database.

Saving Instances in Bulk
........................

We can also save documents to the database in bulk::

    users = [
        User('user@email.com', 'Bob', 'Ross'),
        User('anotheruser@email.com', 'David', 'Attenborough')
    ]
    User.objects.bulk_create(users)

Updating Documents
..................

There are two ways to update documents in MongoDB with ``pymodm``:

1. Change instance attributes to be the way we like, then call
   :meth:`~pymodm.MongoModel.save` on the instance.
2. Use the :meth:`~pymodm.queryset.QuerySet.update` method on the MongoModel's
   :class:`~pymodm.queryset.QuerySet`.

Let's say that we have an instance that looks like this::

    post = Post(author=some_author, content='This is the first post!').save()

Now we realize that we forgot to set the ``revised_on`` date on the
post... oops.  Let's fix that by setting the attribute directly per option (1)
above::

    import datetime

    # Set the revised_on attribute of our Post from earlier.
    post.revised_on = datetime.datetime.now()
    # Save the revised document.
    post.save()

Note that we have to call :meth:`~pymodm.MongoModel.save` in order to save any
changes we've made to a MongoModel. Setting the attribute just changes its value
on our local copy of the document.

The above update strategy works well if we just want to change this single
document. But what if we wanted to update documents in bulk or take advantage of
a particular MongoDB `update operator
<https://docs.mongodb.com/manual/reference/operator/update/>`_? The second
option grants us more flexibility: we can use the
:meth:`~pymodm.queryset.QuerySet.update` method on the MongoModel's
:class:`~pymodm.queryset.QuerySet`::

    Post.objects.raw({'revised_on': {'$exists': False}}).update(
        {'$set': {'revised_on': datetime.datetime.now()}})

We'll discuss QuerySet objects in more detail in the
:ref:`Accessing Data <accessing-data>` section.

.. _accessing-data:

Accessing Data
--------------

We've seen how to model the data in our database and how to create some
documents, so now it's time to query some of this data. Our primary way of
getting to our data happens through the :class:`~pymodm.queryset.QuerySet`
class, which can be accessed through the ``objects`` attribute on our Model
class. Here's how we could list all the Users we have, for example::

    for user in User.objects.all():
        print(user.first_name + ' ' + user.last_name)

We can do the same thing with ``Post`` objects. Let's narrow our search to posts
that were revised within the last month::

    import datetime

    month_ago = datetime.datetime.now() - datetime.timedelta(days=30)

    for post in Post.objects.raw({'revised_on': {'$gte': month_ago}}):
        print(post.title + ' by ' + post.author.first_name)

See what we did there? We accessed the ``first_name`` attribute on the ``User``
object, even though only the id of the User is technically stored in the
``author`` field on a Post. When we access the data stored in a
:class:`~pymodm.fields.ReferenceField`, it is dereferenced automatically. This
makes a separate query to the database. If we didn't want that to happen, we
would need to use the :func:`~pymodm.context_managers.no_auto_dereference`
context manager::

    from pymodm.context_managers import no_auto_dereference

    # Turn off automatic dereferencing for fields defined on "Post".
    with no_auto_dereference(Post):
        for post in Post.objects.raw({'revised_on': {'$gte': month_ago}}):
            print(post.title + ' by author with id ' + post.author)

Querying Model Subclasses
.........................

Earlier, we mentioned that every class that inherits *directly* from
:class:`~pymodm.MongoModel` gets its own collection in the database. But what
about classes that inherit from some other model class?

::

    class ImagePost(Post):
        image = fields.ImageField()

The above model subclasses the ``Post`` model we wrote earlier. Because it does
not inherit directly from MongoModel, it does *not* have its own
collection. Instead, it shares a collection among all the other ``Post``
objects. However, we are still able to distinguish between different types when
querying the database::

    for image_post in ImagePost.objects.all():
        assert isinstance(image_post, ImagePost)

    for post in Post.objects.all():
        if isinstance(post, ImagePost):
            print('image: ' + repr(post.image))
        print('post content: ' + post.content)

How does this work? For every model class that allows inheritance, ``pymodm``
creates another, hidden field called ``_cls`` that stores the class of the model
that the document refers to. This way, models of different types can be
collocated in the same collection while preserving type information.

What if we don't want this ``_cls`` field to be stored in our documents? This is
possible by declaring the model to be *final*, which means that it has to
inherit directly from MongoModel and cannot be extended::

    class PageTheme(MongoModel):
        theme_name = fields.CharField()
        background_color = fields.CharField()
        foreground_color = fields.CharField()

        class Meta:
            final = True

Advanced: Managers and Custom QuerySets
---------------------------------------

We can do a lot with just the tools the default
:class:`~pymodm.queryset.QuerySet` object provides, but sometimes we may find
the need for specialized collection-level functionality, or we might want to
write a shortcut for a very common query that we're performing on one or more
models.

Let's revisit our ``Post`` model and add a field called ``published``. This will
tell us whether the Post has been published or not. Most of the time, we'll
probably just want to work with those Post objects that have already been
published, but it's going to get annoying *fast* if we have to include
``{"published": True}`` with every query.

::

    class Post(MongoModel):
        title = fields.CharField()
        author = fields.ReferenceField(User)
        revised_on = fields.DateTimeField()
        content = fields.CharField()
        comments = fields.EmbeddedModelListField(Comment)
        published = fields.BooleanField(default=False)

There are two ways we can easily access only those Posts which aren't
drafts:

1. Create a new :class:`~pymodm.queryset.QuerySet` class that has a method
   ``published`` that filters ``Post`` objects for ones that have been
   published.
2. Create a new :class:`~pymodm.manager.Manager` class that always creates
   instances of ``QuerySet`` that have the filter ``{"published": True}``
   already applied. This would be handy if we *only* ever cared about Posts that
   have been published.

We'll discuss each approach in turn.

Custom QuerySets
................

Let's take a look at the first approach, using a custom QuerySet class::

    from pymodm.queryset import QuerySet

    class PublishedPostQuerySet(QuerySet):
        def published(self):
            '''Return all published Posts.'''
            return self.raw({"published": True})

Now that we've defined a QuerySet that has the ``published`` method, we need to
hook it up with a :class:`~pymodm.manager.Manager` class so that we can easily
use this ``QuerySet`` type from our model::

    from pymodm.manager import Manager

    # Create the new Manager class.
    PublishedPostManager = Manager.from_queryset(PublishedPostQuerySet)

    class Post(MongoModel):
        title = fields.CharField()
        author = fields.ReferenceField(User)
        revised_on = fields.DateTimeField()
        content = fields.CharField()
        comments = fields.EmbeddedModelListField(Comment)
        published = fields.BooleanField(default=False)

        # Change the "objects" manager to use our own Manager, which returns
        # instances of PublishedPostQuerySet:
        objects = PublishedPostManager()

    # Get all published Posts.
    published_posts = Post.objects.published()

Custom Managers
...............

Now let's examine the second approach, where all ``QuerySet`` instances already
have their ``{"published": True}`` query applied.

When we call a QuerySet method from a Manager, as in ``Post.objects.all()``, the
:meth:`~pymodm.queryset.QuerySet.all` method is proxied through the ``objects``
Manager. The first thing the :class:`~pymodm.manager.Manager` does in this case
is get a QuerySet instance by calling its own
:meth:`~pymodm.manager.BaseManager.get_queryset` method, then it applies
whatever operation was called on the Manager.

What this means for us is that we can override
:meth:`~pymodm.manager.BaseManager.get_queryset` to do anything we want to this
QuerySet instance before it's returned. Any future operations we do with that
QuerySet will have these operations already applied.

The first thing we need to do is subclass :class:`~pymodm.manager.Manager`::

    class PostManager(Manager):
        def get_queryset(self):
            # Override get_queryset() to apply our filter, so that any
            # QuerySet method we call through the Manager already has our query
            # applied.
            return super(PostManager, self).get_queryset().raw(
                {"published": True})


Then, as before, we add this Manager to their MongoModel::

    class Post(MongoModel):
        title = fields.CharField()
        author = fields.ReferenceField(User)
        revised_on = fields.DateTimeField()
        content = fields.CharField()
        comments = fields.EmbeddedModelListField(Comment)
        published = fields.BooleanField(default=False)

        # Change the "objects" manager to use our own PostManager.
        objects = PostManager()

    # Get all published Posts.
    published_posts = Post.objects.all()

Of course, we can add whatever other methods we wish to our custom Manager,
and they don't all have to return QuerySets. For example, we might define a
Manager method to do some complex aggregation::

    from collections import OrderedDict

    class PostManager(Manager):
        def get_queryset(self):
            # Override get_queryset() to apply our filter, so that any
            # QuerySet method we call through the Manager already has our query
            # applied.
            return super(PostManager, self).get_queryset().raw(
                {"published": True})

        def comment_counts(self):
            '''Get a map of title -> # comments for each Post.'''
            aggregates = self.model.objects.aggregate(
                {'$project': {'title': 1, 'comments': {'$size': '$comments'}}},
                {'$sort': {'comments': -1}}
            )
            return OrderedDict((agg['title'], agg['comments'])
                               for agg in aggregates)

Now we can see easily what Posts have the most comments::

    >>> comment_counts = Post.objects.comment_counts()
    >>> print(comment_counts)
    OrderedDict([
      ('Getting Started with PyMODM', 9237),
      ('Custom QuerySets and Managers', 423)
    ])

What's Next?
------------

Congratulations! You've read through the Getting Started guide and understand
the basics of writing an application using PyMODM. For a more detailed reference
of tools that come with PyMODM, check out the
:ref:`API documentation <api-documentation>`.
