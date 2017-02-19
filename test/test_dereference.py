from collections import OrderedDict
from bson import ObjectId, DBRef

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

        # check auto_dereferncing
        # hand.refresh_from_db()
        # self.assertIsInstance(hand.cards[0], Card)
        # self.assertIsInstance(hand.cards[1], Card)

        with no_auto_dereference(hand):
            hand.refresh_from_db()
            dereference(hand)
            self.assertIsInstance(hand.cards[0], Card)
            self.assertIsInstance(hand.cards[1], Card)

    def test_reference_not_found(self):
        post = Post(title='title').save()
        comment = Comment(body='this is a comment', post=post).save()
        post.delete()
        self.assertEqual(Post.objects.count(), 0)
        comment.refresh_from_db()
        self.assertIsNone(comment.post)

    def test_list_embedded_reference_dereference(self):
        # Test dereferencing items stored in a
        # ListField(EmbeddedDocument(ReferenceField(X)))
        class OtherModel(MongoModel):
            name = fields.CharField()

        class OtherRefModel(EmbeddedMongoModel):
            ref = fields.ReferenceField(OtherModel)

        class Container(MongoModel):
            lst = fields.EmbeddedDocumentListField(OtherRefModel)

        m1 = OtherModel('Aaron').save()
        m2 = OtherModel('Bob').save()

        container = Container(lst=[OtherRefModel(ref=m1),
                                   OtherRefModel(ref=m2)])
        container.save()

        # Force ObjectIds.
        container.refresh_from_db()
        dereference(container)

        # access through raw dicts not through __get__ of the field
        # cause __get__ can perform a query to db for reference fields
        # to dereference them using dereference_id function
        self.assertEqual(
            container._data['lst'][0]._data['ref']['name'],
            'Aaron')

        self.assertEqual(container.lst[0].ref.name, 'Aaron')

    def test_embedded_reference_dereference(self):
        # Test dereferencing items stored in a
        # EmbeddedDocument(ReferenceField(X))
        class OtherModel(MongoModel):
            name = fields.CharField()

        class OtherRefModel(EmbeddedMongoModel):
            ref = fields.ReferenceField(OtherModel)

        class Container(MongoModel):
            emb = fields.EmbeddedDocumentField(OtherRefModel)

        m1 = OtherModel('Aaron').save()

        container = Container(emb=OtherRefModel(ref=m1))
        container.save()

        # Force ObjectIds.
        with no_auto_dereference(container):
            container.refresh_from_db()
            self.assertIsInstance(container.emb.ref, ObjectId)
            dereference(container)
            self.assertIsInstance(container.emb.ref, OtherModel)
            self.assertEqual(container.emb.ref.name, 'Aaron')

    def test_dereference_reference_not_found(self):
        post = Post(title='title').save()
        comment = Comment(body='this is a comment', post=post).save()
        post.delete()
        self.assertEqual(Post.objects.count(), 0)
        comment.refresh_from_db()
        with no_auto_dereference(comment):
            dereference(comment)
            self.assertIsNone(comment.post)

    def test_dereference_models_with_same_id(self):
        class User(MongoModel):
            name = fields.CharField(primary_key=True)

        class CommentWithUser(MongoModel):
            body = fields.CharField()
            post = fields.ReferenceField(Post)
            user = fields.ReferenceField(User)

        post = Post(title='Bob').save()
        user = User(name='Bob').save()

        comment = CommentWithUser(
            body='this is a comment',
            post=post,
            user=user).save()

        comment.refresh_from_db()
        with no_auto_dereference(CommentWithUser):
            dereference(comment)
            self.assertIsInstance(comment.post, Post)
            self.assertIsInstance(comment.user, User)

    def test_dereference_dbrefs(self):
        class User(MongoModel):
            post = fields.DictField()
            posts = fields.OrderedDictField()

        post = Post(title='title1').save()
        collection_name = Post._mongometa.collection_name

        post_value = {
            'dbref': DBRef(id=post.title, collection=collection_name)
        }
        posts_value = OrderedDict([('dbref', [post_value['dbref'], ])])

        user = User(post=post_value, posts=posts_value).save()

        user.refresh_from_db()
        with no_auto_dereference(user):
            dereference(user)
            self.assertIsInstance(user.post['dbref'], dict)
            self.assertEqual(user.post['dbref']['_id'], post.title)
            self.assertIsInstance(user.posts['dbref'][0], dict)
            self.assertEqual(user.posts['dbref'][0]['_id'], post.title)

    def test_dereference_missed_reference_field(self):
        comment = Comment(body='Body Comment').save()
        with no_auto_dereference(comment):
            comment.refresh_from_db()
            dereference(comment)
            self.assertIsNone(comment.post)

    def test_dereference_dereferenced_reference(self):
        class CommentContainer(MongoModel):
            ref = fields.ReferenceField(Comment)

        post = Post(title='title').save()
        comment = Comment(body='Comment Body', post=post).save()

        container = CommentContainer(ref=comment).save()

        with no_auto_dereference(comment), no_auto_dereference(container):
            comment.refresh_from_db()
            container.refresh_from_db()
            container.ref = comment
            self.assertEqual(container.ref.post, 'title')
            dereference(container)
            self.assertIsInstance(container.ref.post, Post)
            self.assertEqual(container.ref.post.title, 'title')
            dereference(container)
            self.assertIsInstance(container.ref.post, Post)
            self.assertEqual(container.ref.post.title, 'title')
