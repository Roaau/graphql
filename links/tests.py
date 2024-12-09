from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from links.schema import schema
from links.models import Link
from links.models import Vote

# Create your tests here.

LINKS_QUERY = '''
 {
   links {
     id
     url
     description
   }
 }
'''

USERS_QUERY = '''
 {
   users {
     id
     username
     password
   }
 }
'''


CREATE_LINK_MUTATION = '''
 mutation createLinkMutation($url: String, $description: String) {
     createLink(url: $url, description: $description) {
         description
     }
 }
'''

CREATE_USER_MUTATION = '''
 mutation createUserMutation($email: String!, $password: String!, $username: String!) {
     createUser(email: $email, password: $password, username: $username) {
         user {
            username
            password
         }
     }
 }
'''

LOGIN_USER_MUTATION = '''
 mutation TokenAuthMutation($username: String!, $password: String!) {
     tokenAuth(username: $username, password: $password) {
        token
     }
 }
'''

CREATE_VOTE_MUTATION = '''
mutation CreateVote($linkId: Int!) {
    createVote(linkId: $linkId) {
        user {
            id
            username
        }
        link {
            id
            url
        }
    }
}
'''

VOTE_QUERY = '''
query GetVotes {
    votes {
        user {
            id
            username
        }
        link {
            id
            url
        }
    }
}
'''

class LinkTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.link1 = mixer.blend(Link)
        self.link2 = mixer.blend(Link)
   
        response_user = self.query(
            CREATE_USER_MUTATION,
            variables={'email': 'adsoft@live.com.mx', 'username': 'adsoft', 'password': 'adsoft'}
        )
        print('user mutation ')
        content_user = json.loads(response_user.content)
        print(content_user['data'])

        response_token = self.query(
            LOGIN_USER_MUTATION,
            variables={'username': 'adsoft', 'password': 'adsoft'}
        )

        content_token = json.loads(response_token.content)
        token = content_token['data']['tokenAuth']['token']
        print(token)
        self.headers = {"AUTHORIZATION": f"JWT {token}"}


    def test_links_query(self):
        response = self.query(
            LINKS_QUERY,
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query link results ")
        print (response)
        assert len(content['data']['links']) == 2


    def test_users_query(self):
        response = self.query(
            USERS_QUERY,
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query users results ")
        print (response)
        assert len(content['data']['users']) == 3


    def test_createLink_mutation(self):
        response = self.query(
            CREATE_LINK_MUTATION,
            variables={'url': 'https://google.com', 'description': 'google'},
            headers=self.headers
        )
        content = json.loads(response.content)
        print(content['data'])
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createLink": {"description": "google"}}, content['data']) 

    def test_votes_query(self):
        response = self.query(VOTE_QUERY, headers=self.headers)
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['votes']), 0)

    def test_create_link_mutation(self):
        response = self.query(
            CREATE_LINK_MUTATION,
            variables={'url': 'https://google.com', 'description': 'Google'},
            headers=self.headers
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['createLink']['description'], "Google")

        created_link = Link.objects.get(url="https://google.com")
        self.assertEqual(created_link.description, "Google")

    def test_create_vote_not_logged_in(self):
        self.query(
            CREATE_LINK_MUTATION,
            variables={'url': 'https://example.com', 'description': 'Example Link'},
            headers=self.headers
        )
        self.client.logout()
        response = self.query(
            CREATE_VOTE_MUTATION,
            variables={"linkId": Link.objects.first().id},
        )
        content = json.loads(response.content)

        self.assertIn("errors", content)
        self.assertIn("GraphQLError: You must be logged to vote!", content["errors"][0]["message"])

    def test_create_vote_invalid_link(self):
        response = self.query(
            CREATE_VOTE_MUTATION,
            variables={"linkId": 9999},
            headers=self.headers,
        )
        content = json.loads(response.content)

        self.assertIn("errors", content)
        self.assertIn("Invalid Link!", content["errors"][0]["message"])

    def test_create_vote_successfully(self):
        response_create_link = self.query(
            CREATE_LINK_MUTATION,
            variables={'url': 'https://example.com', 'description': 'Example Link'},
            headers=self.headers
        )
        content_create_link = json.loads(response_create_link.content)
        self.assertResponseNoErrors(response_create_link)

        link_id = Link.objects.get(url="https://example.com").id

        response_create_vote = self.query(
            CREATE_VOTE_MUTATION,
            variables={"linkId": link_id},
            headers=self.headers
        )
        content_create_vote = json.loads(response_create_vote.content)
        self.assertResponseNoErrors(response_create_vote)

        self.assertEqual(content_create_vote["data"]["createVote"]["link"]["url"], "https://example.com")
        self.assertEqual(content_create_vote["data"]["createVote"]["user"]["username"], "adsoft")

        vote_exists = Vote.objects.filter(user__username="adsoft", link_id=link_id).exists()
        self.assertTrue(vote_exists)