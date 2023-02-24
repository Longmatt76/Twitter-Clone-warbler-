"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup('test1','user1@email.com','password',None)
        u1id = 1111
        u1.id = u1id

        u2 = User.signup('test2', 'user2@eamil.com','password',None)
        u2id = 2222
        u2.id = u2id

        db.session.commit()

        u1 = User.query.get(u1id)
        u2 = User.query.get(u2id)

        self.u1 = u1
        self.u2 = u2
      
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res    


    def test_message_model(self):
        '''test basic model'''

        m= Message(text='test,test,test', user_id=self.u1.id)
        m2 = Message(text='testing 123', user_id=self.u2.id)
        m3 = Message(text='seriously again?', user_id=self.u2.id)

        db.session.add_all([m,m2,m3])
        db.session.commit()

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(len(self.u2.messages), 2)
        self.assertEqual(self.u1.messages[0].text, 'test,test,test')
        self.assertEqual(self.u2.messages[0].text, 'testing 123')
        self.assertNotEqual(self.u2.messages[1].text, 'monkey buttz')


    def test_message_likes(self):
        '''tests likes on messages'''

        m= Message(text='test,test,test', user_id=self.u1.id)
        m2 = Message(text='testing 123', user_id=self.u2.id)
        m3 = Message(text='seriously again?', user_id=self.u2.id)

        db.session.add_all([m,m2,m3])
        db.session.commit()

        self.u1.likes.append(m)
        self.u1.likes.append(m2)
        self.u2.likes.append(m3)

        l = Likes.query.filter(Likes.user_id == self.u1.id).all()
        self.assertEqual(len(self.u1.likes), 2)
        self.assertEqual(len(self.u2.likes), 1)
        self.assertEqual(l[0].message_id, m.id)





