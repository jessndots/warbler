"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from sqlalchemy import null

from models import db, User, Message, Follows

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
    
    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url="imgurl")        

        self.client = app.test_client()

    def test_repr(self):
        msg = Message.add_message("test text", self.testuser.id)

        self.assertEqual(msg.__repr__(), f"<Message #{msg.id}: {msg.user}, {msg.timestamp}>")
    
    def test_add_message(self):
        msg = Message.add_message("test text", self.testuser.id)

        self.assertIsInstance(msg, Message)

    def test_create_w_missing_args(self):
        self.assertRaises(TypeError, Message.add_message, "test text")
        self.assertRaises(TypeError, Message.add_message, null, 1)
    
    def test_create_w_wrong_type(self):
        self.assertRaises(TypeError, Message.add_message, 3, True)

    def test_create_w_invalid_user_id(self):
        self.assertRaises(ValueError, Message.add_message, "test text", 40)

    def test_create_exceed_max_len(self):
        self.assertRaises(ValueError, Message.add_message, "test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test ", 1)
    

    

    # id = db.Column(
    #     db.Integer,
    #     primary_key=True,
    # )

    # text = db.Column(
    #     db.String(140),
    #     nullable=False,
    # )

    # timestamp = db.Column(
    #     db.DateTime,
    #     nullable=False,
    #     default=datetime.utcnow(),
    # )

    # user_id = db.Column(
    #     db.Integer,
    #     db.ForeignKey('users.id', ondelete='CASCADE'),
    #     nullable=False,
    # )

    # user = db.relationship('User')

    # def __repr__(self):
        # return f"<Message #{self.id}: {self.user}, {self.timestamp}>"

    # @classmethod
    # def add_message(cls, text, user_id):
    #     """Add message for user.
    #     """

    #     message = Message(
    #         text=text,
    #         user_id=user_id
    #     )

    #     db.session.add(message)
    #     db.session.commit()
    #     return message