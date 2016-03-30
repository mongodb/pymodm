from bson.objectid import ObjectId

from pymodm.base import MongoModel, EmbeddedMongoModel
from pymodm.context_managers import no_auto_dereference
from pymodm.dereference import dereference
from pymodm import fields

from test import ODMTestCase


class Post(MongoModel):
    title = fields.CharField(primary_key=True)
    body = fields.CharField()


class Comment(MongoModel):
    body = fields.CharField()
    post = fields.ReferenceField(Post)


# Contrived models to test highly-nested structures.
class CommentWrapper(EmbeddedMongoModel):
    comments = fields.ListField(fields.ReferenceField(Comment))


class CommentWrapperList(MongoModel):
    wrapper = fields.EmbeddedDocumentListField(CommentWrapper)


class DereferenceTestCase(ODMTestCase):

    def test_leaf_field_dereference(self):
        # Test basic dereference of a ReferenceField directly in the Model.
        post = Post(title='This is a post.').save()
        comment = Comment(
            body='This is a comment on the post.', post=post).save()

        # Force ObjectIds on comment.
        comment.refresh_from_db()
        with no_auto_dereference(Comment):
            self.assertEqual(comment.post, post.title)

            dereference(comment)
            self.assertEqual(comment.post, post)

    def test_list_dereference(self):
        # Test dereferencing items stored in a ListField(ReferenceField(X))
        class OtherModel(MongoModel):
            name = fields.CharField()

        class Container(MongoModel):
            one_to_many = fields.ListField(fields.ReferenceField(OtherModel))

        m1 = OtherModel('a').save()
        m2 = OtherModel('b').save()
        container = Container([m1, m2]).save()

        # Force ObjectIds.
        container.refresh_from_db()
        with no_auto_dereference(container):
            for item in container.one_to_many:
                self.assertIsInstance(item, ObjectId)

        dereference(container)
        self.assertEqual([m1, m2], container.one_to_many)

    def test_highly_nested_dereference(self):
        # Test {outer: [{inner:[references]}]}
        comments = [
            Comment('comment 1').save(),
            Comment('comment 2').save()
        ]
        wrapper = CommentWrapper(comments)
        wrapper_list = CommentWrapperList([wrapper]).save()

        # Force ObjectIds.
        wrapper_list.refresh_from_db()

        dereference(wrapper_list)

        for comment in wrapper_list.wrapper[0].comments:
            self.assertIsInstance(comment, Comment)

    def test_dereference_fields(self):
        # Test dereferencing only specific fields.

        # Contrived Models that contains more than one ReferenceField at
        # different levels of nesting.
        class MultiReferenceModelEmbed(MongoModel):
            comments = fields.ListField(fields.ReferenceField(Comment))
            posts = fields.ListField(fields.ReferenceField(Post))

        class MultiReferenceModel(MongoModel):
            comments = fields.ListField(fields.ReferenceField(Comment))
            posts = fields.ListField(fields.ReferenceField(Post))
            embeds = fields.EmbeddedDocumentListField(MultiReferenceModelEmbed)

        post = Post(title='This is a post.').save()
        comments = [
            Comment('comment 1', post).save(),
            Comment('comment 2').save()
        ]
        embed = MultiReferenceModelEmbed(
            comments=comments,
            posts=[post])
        multi_ref = MultiReferenceModel(
            comments=comments,
            posts=[post],
            embeds=[embed]).save()

        # Force ObjectIds.
        multi_ref.refresh_from_db()

        dereference(multi_ref, fields=['embeds.comments', 'posts'])

        post.refresh_from_db()
        for comment in comments:
            comment.refresh_from_db()
        with no_auto_dereference(MultiReferenceModel):
            self.assertEqual([post], multi_ref.posts)
            self.assertEqual(comments, multi_ref.embeds[0].comments)
            # multi_ref.comments has not been dereferenced.
            self.assertIsInstance(multi_ref.comments[0], ObjectId)

    def test_auto_dereference(self):
        # Test automatic dereferencing.

        post = Post(title='This is a post.').save()
        comments = [
            Comment('comment 1', post).save(),
            Comment('comment 2', post).save()
        ]
        wrapper = CommentWrapper(comments)
        wrapper_list = CommentWrapperList([wrapper]).save()

        wrapper_list.refresh_from_db()

        self.assertEqual(
            'This is a post.',
            wrapper_list.wrapper[0].comments[0].post.title
        )

    def test_unhashable_id(self):
        # Test that we can reference a model whose id type is unhashable
        # e.g. a dict, list, etc.
        class CardIdentity(EmbeddedMongoModel):
            HEARTS, DIAMONDS, SPADES, CLUBS = 0, 1, 2, 3

            rank = fields.IntegerField(min_value=0, max_value=12)
            suit = fields.IntegerField(
                choices=(HEARTS, DIAMONDS, SPADES, CLUBS))

        class Card(MongoModel):
            id = fields.EmbeddedDocumentField(CardIdentity, primary_key=True)
            flavor = fields.CharField()

        class Hand(MongoModel):
            cards = fields.ListField(fields.ReferenceField(Card))

        cards = [
            Card(CardIdentity(4, CardIdentity.CLUBS)).save(),
            Card(CardIdentity(12, CardIdentity.SPADES)).save()
        ]
        hand = Hand(cards).save()
        hand.refresh_from_db()
        dereference(hand)
