from pymodm import MongoModel, EmbeddedMongoModel, fields, connect


# Establish a connection to the database.
connect('mongodb://localhost:27017/blog')


class User(MongoModel):
    # Make all these fields required, so that if we try to save a User instance
    # that lacks one of these fields, we'll get a ValidationError, which we can
    # catch and render as an error on a form.
    #
    # Use the email as the "primary key" (will be stored as `_id` in MongoDB).
    email = fields.EmailField(primary_key=True, required=True)
    handle = fields.CharField(required=True)
    # `password` here will be stored in plain text! We do this for simplicity of
    # the example, but this is not a good idea in general. A real authentication
    # system should only store hashed passwords, and queries for a matching
    # user/password will need to hash the password portion before of the query.
    password = fields.CharField(required=True)


# This is an EmbeddedMongoModel, which means that it will be stored *inside*
# another document (i.e. a Post), rather than getting its own collection. This
# makes it very easy to retrieve all comments with a Post, but we might consider
# breaking out Comment into its own top-level MongoModel if we were expecting to
# have very many comments for every Post.
class Comment(EmbeddedMongoModel):
    # For comments, we just want an email. We don't require signup like we do
    # for a Post, which has an 'author' field that is a ReferenceField to User.
    # Again, we make all fields required so that we get a ValidationError if we
    # try to save a Comment instance that lacks one of these fields. We can
    # catch this error and render it in a form, telling the user that one or
    # more fields still need to be filled.
    author = fields.EmailField(required=True)
    date = fields.DateTimeField(required=True)
    body = fields.CharField(required=True)


class Post(MongoModel):
    # We set "blank=False" so that values like the empty string (i.e. u'')
    # aren't considered valid. We want a real title.  As above, we also make
    # most fields required here.
    title = fields.CharField(required=True, blank=False)
    body = fields.CharField(required=True)
    date = fields.DateTimeField(required=True)
    author = fields.ReferenceField(User, required=True)
    # Comments will be stored as a list of embedded documents, rather than
    # documents in their own collection. We also set "default=[]" so that we can
    # always do:
    #
    #     post.comments.append(Comment(...))
    #
    # instead of:
    #
    #     if post.comments:
    #         post.comments.append(Comment(...))
    #     else:
    #         post.comments = [Comment(...)]
    comments = fields.EmbeddedDocumentListField(Comment, default=[])

    @property
    def summary(self):
        """Return at most 100 characters of the body."""
        if len(self.body) > 100:
            return self.body[:97] + '...'
        return self.body
