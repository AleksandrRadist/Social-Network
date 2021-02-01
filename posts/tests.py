from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Comment, Follow, Group, Post, User


class TestRegistrationProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='sarah',
                                             email='flower@gmail.com',
                                             password='qazwsx1234')

    def test_user_has_profile(self):
        response = self.client.get(reverse('profile',
                                           kwargs={'username':
                                                   self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_unregistered_user_no_profile(self):
        response = self.client.get(
            reverse('profile', kwargs={'username': 'edwin'}))
        self.assertEqual(response.status_code, 404)

    def test_registration_user_has_profile(self):
        response = self.client.get(reverse('profile',
                                           kwargs={'username': 'edwin'}))
        self.assertEqual(response.status_code, 404)
        self.client.post(reverse('signup'), {'username': 'edwin',
                                             'password1': 'qazedc12',
                                             'password2': 'qazedc12'})
        response = self.client.get(reverse('profile',
                                           kwargs={'username': 'edwin'}))
        self.assertEqual(response.status_code, 200)


class TestPostCreate(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='sarah',
                                             email='flower@gmail.com',
                                             password='qazwsx1234')

    def test_unregistered_user_redirected_if_try_post(self):
        response = self.client.get(reverse('new_post'),
                                   follow=True)
        self.assertRedirects(response,
                             f'{reverse("login")}?next={reverse("new_post")}',
                             target_status_code=200)

    def test_unregistered_user_cannot_post(self):
        response = self.client.post(reverse('new_post'), {'text': 'q'},
                                    follow=True)
        self.assertRedirects(response,
                             f'{reverse("login")}?next={reverse("new_post")}',
                             target_status_code=200)
        self.assertEqual(Post.objects.count(), 0)

    def test_registered_user_can_post(self):
        self.client.force_login(self.user, backend=None)
        self.client.post(reverse('new_post'), {'text': 'Nice Try'})
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, 'Nice Try')
        self.assertEqual(post.author, self.user)


class TestNewPostView(TestCase):
    def setUp(self):
        self.client = Client()
        self.text = 'Miracle'
        self.user = User.objects.create_user(username='sarah',
                                             email='flower@gmail.com',
                                             password='qazwsx1234')
        self.post = Post.objects.create(text=self.text,
                                        author=self.user)
        cache.clear()

    def test_new_post_on_main_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['post'].text, self.text)
        self.assertEqual(response.status_code, 200)

    def test_new_post_on_profile_page(self):
        response = self.client.get(reverse('profile',
                                           kwargs={'username':
                                                   self.user.username}))
        self.assertEqual(response.context['post'].text, self.text)
        self.assertEqual(response.status_code, 200)

    def test_new_post_on_post_page(self):
        response = self.client.get(reverse('post_view',
                                           kwargs={'username':
                                                   self.user.username,
                                                   'post_id': self.post.id}))
        self.assertEqual(response.context['post'].text, self.text)
        self.assertEqual(response.status_code, 200)


class TestEditPostView(TestCase):
    def setUp(self):
        self.client = Client()
        self.client2 = Client()
        self.text = 'Miracle'
        self.user = User.objects.create_user(username='sarah',
                                             email='flower@gmail.com',
                                             password='qazwsx1234')
        self.user2 = User.objects.create_user(username='edwin',
                                             email='fire@gmail.com',
                                             password='qazwsx1234')
        self.post = Post.objects.create(text='Hello World',
                                        author=self.user)
        self.client.force_login(self.user, backend=None)
        self.client2.force_login(self.user2, backend=None)
        cache.clear()

    def test_author_can_edit_post(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                         {'text': 'Miracle'})
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, self.text)

    def test_no_author_user_cannot_edit_post(self):
        self.client2.post(reverse('post_edit',
                                  kwargs={'username': self.user.username,
                                          'post_id': self.post.id}),
                         {'text': 'Miracle'})
        post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(post.text, self.text)

    def test_edit_post_on_post_page(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                         {'text': self.text})
        response = self.client.get(reverse('post_view',
                                           kwargs={'username':
                                                   self.user.username,
                                                   'post_id':
                                                   self.post.id}))
        self.assertEqual(response.context['post'].text, self.text)
        self.assertEqual(response.status_code, 200)

    def test_edit_post_on_main_page(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                         {'text': self.text})
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['post'].text, self.text)
        self.assertEqual(response.status_code, 200)

    def test_edit_post_on_profile_page(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                         {'text': self.text})
        response = self.client.get(reverse('profile',
                                           kwargs={'username':
                                                   self.user.username}))
        self.assertEqual(response.context['post'].text, self.text)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, self.text)


class Test404IfNoPageFound(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404_if_no_page_found(self):
        response = self.client.get('qwe')
        self.assertEqual(response.status_code, 404)


class TestImage(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='sarah',
                                             email='flower@gmail.com',
                                             password='qazwsx1234')
        self.group = Group.objects.create(title='Sun', slug='sun')
        self.post = Post.objects.create(text='Mainland',
                                        author=self.user, group=self.group)
        self.client.force_login(self.user, backend=None)
        image = (b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21'
                 b'\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00'
                 b'\x01\x00\x00\x02\x02\x4c\x01\x00\x3b')
        self.image = SimpleUploadedFile(
            name='test3.jpg', content=image, content_type='image/jpg'
        )
        cache.clear()

    def test_non_graphic_type_image_load(self):
        image = SimpleUploadedFile(name='test.txt', content=b'q')
        response = self.client.post(reverse('post_edit',
                                    kwargs={'username': self.user.username,
                                            'post_id': self.post.id}),
                         {'text': 'post with image', 'image': image})
        self.assertFormError(response, 'form', 'image',
                             'Загрузите правильное изображение. Файл, который '
                             'вы загрузили, поврежден или не является '
                             'изображением.')

    def test_main_page_has_image(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                                {'text': 'post with image', 'image': self.image})
        response = self.client.get(reverse('index'))
        self.assertContains(response, '<img class="card-img"')

    def test_post_page_has_image(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                                {'text': 'post with image', 'image': self.image})
        response = self.client.get(reverse('post_view',
                                           kwargs={'username':
                                                   self.user.username,
                                                   'post_id': self.post.id}))
        self.assertContains(response, '<img class="card-img"')

    def test_profile_page_has_image(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                                {'text': 'post with image', 'image': self.image})
        response = self.client.get(reverse('profile',
                                           kwargs={'username':
                                                   self.user.username}))
        self.assertContains(response, '<img class="card-img"')

    def test_group_page_has_image(self):
        self.client.post(reverse('post_edit',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                         {'text': 'post with image',
                          'image': self.image,
                          'group': self.group.id})
        response = self.client.get(reverse('group_posts',
                                           kwargs={'slug':
                                                   self.group.slug}))
        self.assertContains(response, '<img class="card-img"')


class TestComment(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='sarah',
                                             email='flower@gmail.com',
                                             password='qazwsx1234')
        self.post = Post.objects.create(text='Hello',
                                        author=self.user)
        self.text = 'giant cat'

    def test_unlogged_user_cannot_post(self):
        self.client.post(reverse('add_comment',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                         {'text': self.text})
        comments = Comment.objects.all()
        self.assertEqual(comments.count(), 0)

    def test_logged_user_can_comment(self):
        self.client.force_login(self.user, backend=None)
        self.client.post(reverse('add_comment',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
                         {'text': self.text})
        response = self.client.get(reverse('post_view',
                                           kwargs={'username':
                                                   self.user.username,
                                                   'post_id': self.post.id}))
        comments = Comment.objects.all()
        self.assertEqual(comments.count(), 1)
        self.assertContains(response, self.text)
        self.assertEqual(response.context['items'][0].text, self.text)
        self.assertEqual(response.status_code, 200)


class TestFollow(TestCase):
    def setUp(self):
        self.client = Client()
        self.client2 = Client()
        self.user = User.objects.create_user(username='sarah',
                                             email='flower@gmail.com',
                                             password='qazwsx1234')
        self.user2 = User.objects.create_user(username='edwin',
                                              email='flour@gmail.com',
                                              password='qazwsx1234')
        self.user3 = User.objects.create_user(username='erick',
                                              email='tots@gmail.com',
                                              password='qazwsx1234')
        self.text = 'Transaction'
        self.post = Post.objects.create(text=self.text,
                                        author=self.user3)
        self.client.force_login(self.user, backend=None)

    def test_registered_user_can_follow(self):
        self.client.get(reverse('profile_follow',
                                kwargs={'username': self.user3.username}))
        follows = Follow.objects.filter(user=self.user)
        self.assertEqual(follows.count(), 1)
        self.assertEqual(follows.first().author, self.user3)

    def test_registered_user_can_unfollow(self):
        self.client.get(reverse('profile_follow',
                                kwargs={'username': self.user3.username}))
        self.client.get(reverse('profile_unfollow',
                                kwargs={'username': self.user3.username}))
        follows = Follow.objects.filter(user=self.user)
        self.assertEqual(follows.count(), 0)

    def test_unregistered_user_cannot_follow(self):
        self.client2.get(reverse('profile_follow',
                                 kwargs={'username': self.user3.username}))
        follows = Follow.objects.filter(user=self.user)
        self.assertEqual(follows.count(), 0)

    def test_user_who_follow_update_follow_index(self):
        self.client.get(reverse('profile_follow',
                                kwargs={'username': self.user3.username}))
        response = self.client.get(reverse('follow_index'))
        self.assertEqual(response.context['post'].text, self.text)
        self.assertEqual(response.status_code, 200)

    def test_user_not_follow_not_update_follow_index(self):
        self.client.get(reverse('profile_follow',
                                kwargs={'username': self.user3.username}))
        self.client2.force_login(self.user2, backend=None)
        response = self.client2.get(reverse('follow_index'))
        self.assertNotContains(response, self.text)

