"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser_id = 9999
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u4 = User.signup("testing", "test4@test.com", "password", None)

        db.session.commit()


    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp
    


    def test_users_index(self):
        '''test user list route and html'''
        with self.client as c:
            resp = c.get("/users")
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))
            self.assertIn("@hij", str(resp.data))
            self.assertIn("@testing", str(resp.data))

    
    def test_show_user(self):
        '''tests a single users display page'''
        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', str(resp.data))
            self.assertIn('location', str(resp.data))
            self.assertIn('<a href="/users/9999/following">0</a>', str(resp.data))


    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()


    
    def test_user_following(self):
        '''test the users following page'''

        self.setup_followers()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            resp = c.get(f'/users/{self.testuser.id}/following')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@abc', str(resp.data))
            self.assertIn('@efg', str(resp.data))



    def test_user_followers(self):
        '''test the users followers page'''

        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/followers')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@abc', str(resp.data))


    def setup_likes(self):
        m1 = Message(text="trending warble", user_id=self.testuser_id)
        m2 = Message(text="Eating some lunch", user_id=self.testuser_id)
        m3 = Message(id=9876, text="likable warble", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=9876)

        db.session.add(l1)
        db.session.commit()


    def test_show_likes(self):
        self.setup_likes()

        l1 = Likes.query.one()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        resp = c.get(f'/users/{self.testuser.id}/likes', data={'likes': l1})
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('href="https://unpkg.com/bootstrap/dist/css/bootstrap.css"', html)


    def test_add_like(self):
        """tests adding a like"""
        m = Message(id=1234, text='like me', user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


        resp = c.post('/users/add_like/1234')

        self.assertEqual(resp.status_code, 302)
        likes = Likes.query.filter(Likes.message_id==1234).all()
        self.assertEqual(len(likes),1)
        self.assertEqual(likes[0].user_id, self.testuser.id)



    def test_remove_like(self):
        """tests removing a like"""
        m = Message(id=1234, text='like me', user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


        c.post('/users/add_like/1234')
        resp = c.post('/users/remove_like/1234')

        self.assertEqual(resp.status_code, 302)
        likes = Likes.query.filter(Likes.message_id==1234).all()
        self.assertEqual(len(likes),0) 


        



    