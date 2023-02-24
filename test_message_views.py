"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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



class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_home_page(self):
        """test the status code and html displayed on the homepage"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


            resp = c.get('/')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p class="small">Followers</p>', html)


    def test_message_view(self):
        '''test the message view page'''

        m = Message(id=1234, text='test message',user_id=self.testuser.id)

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message.query.get(1234)

            resp = c.get(f'/messages/{m.id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code,200)
            self.assertIn('<ul class="list-group no-hover" id="messages">', html)
            self.assertEqual(m.text, 'test message')


    def test_delete_message(self):
        '''test that the logged in user can delete own message'''

        m = Message(id=1234, text='test message',user_id=self.testuser.id)

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/messages/1234/delete')
            self.assertEqual(resp.status_code, 302)
            
            m = Message.query.get(1234)
            self.assertIsNone(m)


    def test_unauthorized_delete_message(self):
        """tests that a user can't delete anothers message, it doesnt work currently"""

        u = User.signup(username='user2',email='user2@email.com', password='password', image_url=None)
        uid = 2222
        u.id = uid

        m = Message(id=1234, text='hey dont delete this!',user_id=self.testuser.id)

        db.session.add_all([m,u])
        db.session.commit()

        u = User.query.get(uid)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = uid

            resp = c.post('/messages/1234/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)





