# Copyright 2016 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test Embedded and Referenced documents."""
from bson.objectid import ObjectId

from pymodm.base import MongoModel, EmbeddedMongoModel
from pymodm.context_managers import no_auto_dereference
from pymodm.errors import ValidationError
from pymodm import fields

from test import ODMTestCase, DB


class Contributor(MongoModel):
    name = fields.CharField()
    thumbnail = fields.EmbeddedDocumentField('Image')


class Image(EmbeddedMongoModel):
    image_url = fields.CharField(required=True)
    alt_text = fields.CharField()
    photographer = fields.ReferenceField(Contributor)


class Post(MongoModel):
    body = fields.CharField()
    images = fields.EmbeddedDocumentListField(Image)


class Comment(MongoModel):
    body = fields.CharField()
    post = fields.ReferenceField(Post)


class RelatedFieldsTestCase(ODMTestCase):

    def test_basic_reference(self):
        post = Post(body='This is a post.')
        comment = Comment(body='Love your post!', post=post)
        post.save()
        self.assertTrue(post._id)

        comment.save()
        self.assertEqual(post, Comment.objects.first().post)

    def test_assign_id_to_reference_field(self):
        # No ValidationError raised.
        Comment(post="58b477046e32ab215dca2b57").full_clean()

    def test_validate_embedded_document(self):
        with self.assertRaisesRegex(ValidationError, 'field is required'):
            # Image has all fields left blank, which isn't allowed.
            Contributor(name='Mr. Contributor', thumbnail=Image()).save()
        # Test with a dict.
        with self.assertRaisesRegex(ValidationError, 'field is required'):
            Contributor(name='Mr. Contributor', thumbnail={
                'alt_text': 'a picture of nothing, since there is no image_url.'
            }).save()

    def test_validate_embedded_document_list(self):
        with self.assertRaisesRegex(ValidationError, 'field is required'):
            Post(images=[Image(alt_text='Vast, empty space.')]).save()
        with self.assertRaisesRegex(ValidationError, 'field is required'):
            Post(images=[{'alt_text': 'Vast, empty space.'}]).save()

    def test_reference_errors(self):
        post = Post(body='This is a post.')
        comment = Comment(body='Love your post!', post=post)

        # post has not yet been saved to the database.
        with self.assertRaises(ValidationError) as cm:
            comment.full_clean()
        message = cm.exception.message
        self.assertIn('post', message)
        self.assertEqual(
            ['Referenced Models must be saved to the database first.'],
            message['post'])

        # Cannot save document when reference is unresolved.
        with self.assertRaises(ValidationError) as cm:
            comment.save()
        self.assertIn('post', message)
        self.assertEqual(
            ['Referenced Models must be saved to the database first.'],
            message['post'])

    def test_embedded_document(self):
        contr = Contributor(name='Shep')
        # embedded field is not required.
        contr.full_clean()
        contr.save()

        # Attach an image.
        thumb = Image(image_url='/images/shep.png', alt_text="It's Shep.")
        contr.thumbnail = thumb
        contr.save()

        self.assertEqual(thumb, next(Contributor.objects.all()).thumbnail)

    def test_embedded_document_list(self):
        images = [
            Image(image_url='/images/kittens.png',
                  alt_text='some kittens'),
            Image(image_url='/images/blobfish.png',
                  alt_text='some kittens fighting a blobfish.')
        ]
        post = Post(body='Look at my fantastic photography.',
                    images=images)

        # Images get saved when the parent object is saved.
        post.save()

        # Embedded documents are converted to their Model type when retrieved.
        retrieved_posts = Post.objects.all()
        self.assertEqual(images, next(retrieved_posts).images)

    def test_refresh_from_db(self):
        post = Post(body='This is a post.')
        comment = Comment(body='This is a comment on the post.',
                          post=post)
        post.save()
        comment.save()

        comment.refresh_from_db()
        with no_auto_dereference(Comment):
            self.assertIsInstance(comment.post, ObjectId)

        # Use PyMongo to update the comment, then update the Comment instance's
        # view of itself.

        DB.comment.update_one(
            {'_id': comment.pk}, {'$set': {'body': 'Edited comment.'}})
        # Set the comment's "post" to something else.
        other_post = Post(body='This is a different post.')
        comment.post = other_post
        comment.refresh_from_db(fields=['body'])
        self.assertEqual('Edited comment.', comment.body)
        # "post" field is gone, since it wasn't part of the projection.
        self.assertIsNone(comment.post)

    def test_circular_reference(self):
        class ReferenceA(MongoModel):
            ref = fields.ReferenceField('ReferenceB')

        class ReferenceB(MongoModel):
            ref = fields.ReferenceField(ReferenceA)

        a = ReferenceA().save()
        b = ReferenceB().save()
        a.ref = b
        b.ref = a
        a.save()
        b.save()

        self.assertEqual(a, ReferenceA.objects.first())
        with no_auto_dereference(ReferenceA):
            self.assertEqual(b.pk, ReferenceA.objects.first().ref)
        self.assertEqual(b, ReferenceA.objects.select_related().first().ref)

    def test_cascade_save(self):
        photographer = Contributor('Curly').save()
        image = Image('kitten.png', 'kitten', photographer)
        post = Post('This is a post.', [image])
        # Photographer has already been saved to the database. Let's change it.
        photographer_thumbnail = Image('curly.png', "It's Curly.")
        photographer.thumbnail = photographer_thumbnail
        post.body += "edit: I'm a real author because I have a thumbnail now."
        # {'body': 'This is a post', 'images': [{
        #     'image_url': 'stew.png', 'photographer': {
        #         'name': 'Curly', 'thumbnail': {
        #             'image_url': 'curly.png', 'alt_text': "It's Curly."}
        #     }]
        # }
        post.save(cascade=True)
        post.refresh_from_db()
        self.assertEqual(
            post.images[0].photographer.thumbnail, photographer_thumbnail)

    def test_coerce_reference_type(self):
        post = Post('this is a post').save()
        post_id = str(post.pk)
        comment = Comment(body='this is a comment', post=post_id).save()
        comment.refresh_from_db()
        self.assertEqual('this is a post', comment.post.body)
