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

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

        self.testmessage2 = Message.add_message(text="Hello", user_id = self.testuser2.id)      

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

            msg = Message.query.filter_by(user_id=self.testuser.id)[0]
            self.assertEqual(msg.text, "Hello")


    def test_messages_show(self):
        """Test that message is shown correctly"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            resp = c.get(f"/messages/{msg.id}")
            html = resp.get_data(as_text=True)
            
            # Make sure status code 200
            self.assertEqual(resp.status_code, 200)

            # Make sure correct html returned
            self.assertIn('<p class="single-message">Hello</p>', html)


    def test_messages_destroy(self):
        """Test that messages are deleted"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            resp = c.post(f"/messages/{msg.id}/delete")

            # test redirect
            self.assertEqual(resp.status_code, 302)

            # test that message was deleted
            self.assertIsNone(Message.query.get(msg.id))

    def test_messages_destroy_redirect(self):
        """Test that messages are deleted"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # test redirect
            self.assertEqual(resp.status_code, 200)

            # test that message is no longer displayed
            self.assertNotIn(msg.text, html)


    def test_add_like(self):
        """test that likes are added to a message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser)
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            # like user2's message
            resp = c.post(f"/messages/like/{msg.id}")
            html = resp.get_data(as_text=True)

            # test status code
            self.assertEqual(resp.status_code, 302)

            # test that msg is in likes
            self.assertIn(msg, self.testuser.likes)

    def test_add_like_redirect(self):
        """test that likes are added to a message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser)
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            # like user2's message
            resp = c.post(f"/messages/like/{msg.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # test status code
            self.assertEqual(resp.status_code, 200)

            # test that msg is included in liked messages
            self.assertIn("Hello", html)
             

    def test_unlike(self):
        """test that message is unliked by signed in user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser)
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            # like message - tested above
            self.testuser.likes.append(msg)

            # unlike message
            resp = c.post(f"/messages/unlike/{msg.id}")
            html = resp.get_data(as_text=True)


            # test status code
            self.assertEqual(resp.status_code, 302)

            # test that msg is in likes
            self.assertNotIn(msg, self.testuser.likes)

    def test_unlike_redirect(self):
        """test that message is unliked by signed in user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser)
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            # like message - tested above
            self.testuser.likes.append(msg)

            # unlike message
            resp = c.post(f"/messages/unlike/{msg.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # test status code
            self.assertEqual(resp.status_code, 200)

            # test that msg icon shows as unliked
            self.assertNotIn("Hello", html)


    def test_show_likes(self):
        """test that all of users likes are showing"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            db.session.add(self.testuser)
            db.session.add(self.testuser2)
            db.session.add(self.testmessage2)

            msg = self.testmessage2

            # like message - tested above
            self.testuser.likes.append(msg)

            # go to likes
            resp = c.get(f"/users/{self.testuser.id}/likes")
            html = resp.get_data(as_text=True)

            # test status code
            self.assertEqual(resp.status_code, 200)

            # test that msg icon shows as unliked
            self.assertIn("Hello", html)


    
