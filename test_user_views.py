"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


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


class LoggedInUserViewTestCase(TestCase):
    """Test views for user when logged in."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url="imageurl")

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url="imageurl")

        self.testmessage2 = Message.add_message(text="Hello", user_id = self.testuser2.id)      

        db.session.commit()


    def test_list_users(self):
        """Test that users are being listed"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            # Test that status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test that test user is listed
            self.assertIn(self.testuser.username, html)

    def test_users_show(self):
        """Test that a user profile is properly displayed"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            user = self.testuser2
            db.session.add(user)
            resp = c.get(f"/users/{user.id}")
            html = resp.get_data(as_text=True)

            # Test status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test that user profile is displayed
            self.assertIn('<h4 id="sidebar-username">@testuser2</h4>', html)
    

    def test_show_following(self):
        """Test that following is properly displayed"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            user = self.testuser2
            following = self.testuser

            db.session.add(user)

            # Follow user
            user.following.append(following)

            # Display following
            resp = c.get(f"/users/{user.id}/following")
            html = resp.get_data(as_text=True)

            # Test status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test that following list is displayed
            self.assertIn('<p>@testuser</p>', html)


    def test_show_followers(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            user = self.testuser2
            follower = self.testuser

            db.session.add(follower)

            # Add follower
            follower.following.append(user)

            # Display followers
            resp = c.get(f"/users/{user.id}/followers")
            html = resp.get_data(as_text=True)

            # Test status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test that followers list is displayed
            self.assertIn('<p>@testuser</p>', html)


    def test_add_follow(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            user = self.testuser
            following = self.testuser2

            db.session.add(user)
            db.session.add(following)

            # Follow
            resp = c.post(f"/users/follow/{following.id}")

            # Test status code is 302
            self.assertEqual(resp.status_code, 302)

            # Test user was followed
            self.assertIn(following, user.following)


    def test_stop_following(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            user = self.testuser
            following = self.testuser2

            db.session.add(user)
            db.session.add(following)

            # Follow
            user.following.append(following)
            self.assertIn(following, user.following)

            # Unfollow
            resp = c.post(f"/users/stop-following/{following.id}")

            # Test status code is 302
            self.assertEqual(resp.status_code, 302)

            # Test user was unfollowed
            self.assertNotIn(following, user.following)


    def test_update_profile(self):
        """Test that edit profile form is properly displayed"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Get resp
            resp = c.get(f"/users/profile")
            html = resp.get_data(as_text=True)

            # Test that status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test that edit profile form is shown
            self.assertIn('id="user_form"', html)

            # Test that form is populated with original values
            self.assertIn("test@test.com", html)
             
        
    def test_update_profile_post(self):
        """Test that user info is properly updated in db"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            db.session.add(self.testuser)

            # Get resp
            resp = c.post(f"/users/profile", data={"username": "testtest", "email": "testuser@test.com", "bio":"this is a test", "password":"testuser"})
            html = resp.get_data(as_text=True)

            # Test that status code is 302
            self.assertEqual(resp.status_code, 302)

            # Test that db was updated
            self.assertEqual(self.testuser.email, "testuser@test.com")
            self.assertEqual(self.testuser.username, "testtest")
            self.assertEqual(self.testuser.bio, "this is a test")


    def test_update_profile_post_redirect(self):
        """Test that displayed user profile was edited after redirect"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            db.session.add(self.testuser)

            # Get resp
            resp = c.post(f"/users/profile", data={"username": "testtest", "email": "testuser@test.com", "bio":"this is a test", "password":"testuser"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test that status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test that updated info is displayed on profile view
            self.assertIn("@testtest", html)
            self.assertIn("this is a test", html)


    def test_delete_user(self):
        """Test that user is properly deleted from database"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            db.session.add(self.testuser)

            # Delete user
            resp = c.post(f"/users/delete")

            # Test status code 302
            self.assertEqual(resp.status_code, 302)

            # Test that user was removed from db
            self.assertNotIn(self.testuser, User.query.all())

    def test_delete_user_redirect(self):
        """Test redirect to signup page upon profile deletion"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            db.session.add(self.testuser)

            # Delete user
            resp = c.post(f"/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test status code 200
            self.assertEqual(resp.status_code, 200)

            # Test that signup page is displayed
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)

class LoggedOutUserViewTestCase(TestCase):
    """Test views for user when logged out."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url="imageurl")

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url="imageurl")

        self.testmessage2 = Message.add_message(text="Hello", user_id = self.testuser2.id)      

        db.session.commit()  

    def test_show_following(self):
        """Test that page cannot be viewed when logged out"""

        with self.client as c:

            user = self.testuser2

            # Display following
            resp = c.get(f"/users/{user.id}/following")
            html = resp.get_data(as_text=True)

            # Test status code is 302
            self.assertEqual(resp.status_code, 302)

    def test_show_following_redirect(self):
        """Test that logged out user is properly redirected"""

        with self.client as c:

            user = self.testuser2

            # Display following
            resp = c.get(f"/users/{user.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test redirected to signup page
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)

    def test_show_followers(self):
        """Test that page cannot be viewed when logged out"""

        with self.client as c:

            user = self.testuser2

            # Display followers
            resp = c.get(f"/users/{user.id}/followers")
            html = resp.get_data(as_text=True)

            # Test status code is 302
            self.assertEqual(resp.status_code, 302)

    def test_show_followers_redirect(self):
        """Test that logged out user is properly redirected"""
        with self.client as c:

            user = self.testuser2

            # Display followers
            resp = c.get(f"/users/{user.id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test redirected to signup page
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


    def test_add_follow(self):
        """Test that user cannot follow when logged out"""

        with self.client as c:

            following = self.testuser2

            db.session.add(following)

            # Follow
            resp = c.post(f"/users/follow/{following.id}")

            # Test status code is 302
            self.assertEqual(resp.status_code, 302)


    def test_add_follow_redirect(self):
        """Test that logged out user is properly redirected"""
        with self.client as c:

            following = self.testuser2

            db.session.add(following)

            # Follow
            resp = c.post(f"/users/follow/{following.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test redirected to signup page
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)

    def test_stop_following(self):
        """Test that user cannot stop following when logged out"""

        with self.client as c:
 
            following = self.testuser2

            db.session.add(following)

            # Unfollow
            resp = c.post(f"/users/stop-following/{following.id}")

            # Test status code is 302
            self.assertEqual(resp.status_code, 302)


    def test_stop_following_redirect(self):
        """Test that logged out user is properly redirected"""
        with self.client as c:

            following = self.testuser2

            db.session.add(following)

            # Unfollow
            resp = c.post(f"/users/stop-following/{following.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test redirected to signup page
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)

    def test_update_profile(self):
        """Test that page cannot be viewed when logged out"""

        with self.client as c:

            # Get resp
            resp = c.get(f"/users/profile")
            html = resp.get_data(as_text=True)

            # Test that status code is 302
            self.assertEqual(resp.status_code, 302)

             
    def test_update_profile_redirect(self):
        """Test that logged out user is properly redirected"""
        with self.client as c:

            # Get resp
            resp = c.get(f"/users/profile", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test that status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test redirected to signup page
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
        
    def test_update_profile_post(self):
        """Test that profile cannot be updated when logged out"""

        with self.client as c:

            # Get resp
            resp = c.post(f"/users/profile", data={"username": "testtest", "email": "testuser@test.com", "bio":"this is a test", "password":"testuser"})
            html = resp.get_data(as_text=True)

            # Test that status code is 302
            self.assertEqual(resp.status_code, 302)

    def test_update_profile_post_redirect(self):
        """Test that logged out user is properly redirected"""
        with self.client as c:

            # Get resp
            resp = c.post(f"/users/profile", data={"username": "testtest", "email": "testuser@test.com", "bio":"this is a test", "password":"testuser"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test that status code is 200
            self.assertEqual(resp.status_code, 200)

            # Test redirected to signup page
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


    def test_delete_user(self):
        """Test that user cannot be deleted when logged out"""

        with self.client as c:

            # Delete user
            resp = c.post(f"/users/delete")

            # Test status code 302
            self.assertEqual(resp.status_code, 302)


    def test_delete_user_redirect(self):
        """Test that logged out user is properly redirected"""

        with self.client as c:

            # Delete user
            resp = c.post(f"/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Test status code 200
            self.assertEqual(resp.status_code, 200)

        # Test redirected to signup page
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)

            
