"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from sqlite3 import IntegrityError
from unittest import TestCase
from xml.dom import InvalidCharacterErr

import sqlalchemy
import psycopg2.errors

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_attributes(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does repr method work as expected"""
        u = User(email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD")

        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.__repr__(), f"<User #{u.id}: {u.username}, {u.email}>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is or isn't following user2"""
        u1 = User(email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD")

        u2 = User(email="test2@test.com", 
            username="testuser2", 
            password="HASHED_PASSWORD_2")

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.assertFalse(u1.is_following(u2))
        
        u1.following.append(u2)

        self.assertTrue(u1.is_following(u2))


    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is and is not followed by user2?"""

        u1 = User(email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD")

        u2 = User(email="test2@test.com", 
            username="testuser2", 
            password="HASHED_PASSWORD_2")

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.assertFalse(u1.is_followed_by(u2))

        u1.followers.append(u2)

        self.assertTrue(u1.is_followed_by(u2))


    def test_create_valid_user(self):
        user = User.signup("test", "email@email.com", "password", "image.jpg")

        db.session.add(user)
        db.session.commit()

        self.assertIsInstance(user, User)

    def test_signup_duplicate_username(self):
        user = User.signup("test", "test@test.com", "password", "imageurl") 

        db.session.add(user)
        db.session.commit()

        self.assertRaises(ValueError, User.signup, "test", "test@test.com", "password", "imageurl")

    def test_signup_required_fields(self):

        self.assertRaises(ValueError, User.signup, "", "test@test.com", "password", "imageurl")

        self.assertRaises(ValueError, User.signup, "username", "", "password", "imageurl")

        self.assertRaises(ValueError, User.signup, "username", "test@test.com", "", "imageurl")

        self.assertRaises(ValueError, User.signup, "username", "test@test.com", "password", "")

    def test_signup_min_length_fields(self):
        self.assertRaises(ValueError, User.signup, "u", "test@test.com", "password", "imageurl")

        self.assertRaises(ValueError, User.signup, "username", "test@test.com", "pw", "imageurl")

    def test_signup_field_types(self):
        self.assertRaises(TypeError, User.signup, [], "test@test.com", "password", "imageurl")
        self.assertRaises(TypeError, User.signup, "username", True, "password", "imageurl")
        self.assertRaises(TypeError, User.signup, "username", "test@test.com", 7, "imageurl")
        self.assertRaises(TypeError, User.signup, "username", "test@test.com", "password", {})

    def test_authenticate_valid_user(self):
        user = User.signup("username", "test@test.com", "password", "imageurl")

        db.session.add(user)
        db.session.commit()

        self.assertIsInstance(User.authenticate("username", "password"), User)

    def test_authenticate_invalid_user(self):

        user = User.signup("username", "test@test.com", "password", "imageurl")

        db.session.add(user)
        db.session.commit()

        self.assertFalse(User.authenticate("username", "wrong"))

        self.assertFalse(User.authenticate("wrong", "password"))
    

        

    

