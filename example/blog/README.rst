PyMODM Blog Example
-------------------

This example is a simple blog that demonstrates how to define models, query and
save objects using PyMODM. You are invited to run this example, make
modifications, and use this as a learning tool or even a template to get started
with your own project.


Project Structure
.................

This project is divided into several files:

- ``blog.py``: This is where the main application logic lives.
- ``blog_models.py``: MongoModel definitions live here.
- ``static``: This directory contains static files, like css.
- ``templates``: This directory contains `Jinja2`_ HTML templates.

.. _Jinja2: https://pypi.python.org/pypi/Jinja2


Running the Example
...................

Follow these directions to start the blog:

1. Make sure that MongoDB is running on ``localhost:27017``. `Download MongoDB
   <www.mongodb.com/download-center>`_ if you don't have it installed already.

2. Install prerequisite software: this example depends on `flask`_ and
   `pymodm`_. You can install these dependencies automatically by running ``pip
   install -r requirements.txt``.

3. Start the blog by running ``python blog.py``.

4. Visit the main page in your browser at `http://localhost:5000
   <http://localhost:5000>`_.

.. _pymodm: https://pypi.python.org/pypi/pymodm
.. _flask: https://pypi.python.org/pypi/Flask


Site Map
........

After the blog application has been started, there are several URLs available:

- **http://localhost:5000**: This is the home page. It displays all of the posts
  in a summarized form.
- **http://localhost:5000/posts/<post_id>**: This displays the long form of the
  post with the id ``post_id``. It also displays a form for submitting comments
  on the post.
- **http://localhost:5000/posts/new**: When sent a ``GET`` request, this returns
  a page that displays a form for creating a new post. When sent a ``POST``
  request, this endpoint creates a new post from the form data.
- **http://localhost:5000/comments/new**: This is the endpoint for creating a
  new comment object. This endpoint only accepts ``POST`` requests (the form for
  creating a new comment is rendered at ``posts/post_id``).
- **http://localhost:5000/users/new**: When sent a ``GET`` request, this returns
  a page that displays a form for creating a new user (every post is associated
  with a user). When sent a ``POST`` request, this endpoint creates a new user
  from the form data.
- **http://localhost:5000/login**: When sent a ``GET`` request, this returns a
  page that displays a form for logging in. When sent a ``POST`` request, this
  endpoint logs the user in and sets a cookie for the session.
- **http://localhost:5000/logout**: This endpoint logs the user out. This
  endpoint only accepts ``POST`` requests.
