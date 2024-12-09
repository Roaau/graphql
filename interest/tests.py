from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from interest.schema import schema
from interest.models import Interest

# Create your tests here.

INTEREST_QUERY = '''
query GetInterests($search: String) {
  interests(search: $search) {
    id
    name
  }
}
'''

INTEREST_BY_ID_QUERY = '''
            query GetInterestById($id_interest: Int!) {
                interestById(idInterest: $id_interest) {
                    id
                    name
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


CREATE_INTEREST_MUTATION = '''
 mutation createInterestMutation($id_interest: Int!, $name: String) {
     createInterest(idInterest: $id_interest, name: $name) {
         idInterest
         name
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

DELETE_INTEREST_MUTATION = '''
mutation DeleteInterest($id_interest: Int!) {
    deleteInterest(idInterest: $id_interest) {
        idInterest
    }
}
'''

class InterestTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.interest1 = mixer.blend(Interest)
        self.interest2 = mixer.blend(Interest)
   
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


    def test_interest_query(self):
        response = self.query(
            INTEREST_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query interest results ")
        print (response)
        assert len(content['data']['interests']) == 0


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


    def test_createInterest_mutation(self):
        response = self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                'id_interest': 0,
                'name': 'Boxing'},
            headers=self.headers
        )
        content = json.loads(response.content)
        created_interest_id = content['data']['createInterest']['idInterest']
        print("Response content:", content)
        print(content['data'])
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createInterest": {"idInterest": created_interest_id, "name": "Boxing"}}, content['data']) 
        
    def test_interest_by_id_query(self):
        response_create = self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                'id_interest': 0,
                'name': 'Boxing'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        created_interest_id = content_create['data']['createInterest']['idInterest']

        response = self.query(
          INTEREST_BY_ID_QUERY,
          variables={'id_interest': created_interest_id},
          headers=self.headers
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['interestById']['name'], "Boxing")
        
    def test_update_existing_interest(self):
        response_create = self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                'id_interest': 0,
                'name': 'Boxing'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        created_interest_id = content_create['data']['createInterest']['idInterest']

        
        self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                'id_interest': created_interest_id,
                'name': 'MMA'},
            headers=self.headers
        )

        response_query = self.query(
        INTEREST_BY_ID_QUERY,
        variables={'id_interest': created_interest_id},
        headers=self.headers
        )
        
        content_query = json.loads(response_query.content)
                
        
        response_query_all = self.query(
            INTEREST_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        
        content = json.loads(response_query_all.content)

        assert len(content['data']['interests']) == 1
        self.assertEqual(content_query['data']['interestById']['name'], "MMA")
        
    def test_not_logged_in(self):
        response = self.query(
            INTEREST_BY_ID_QUERY,
            variables={"id_interest": 1}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in", content['errors'][0]['message'])

        response = self.query(
            INTEREST_QUERY,
            variables={"search": "*"}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_filter_search(self):
        self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                'id_interest': 1,
                'name': 'Interest A'
            },
            headers=self.headers
        )
        self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                'id_interest': 2,
                'name': 'Interest B'
            },
            headers=self.headers
        )

        response = self.query(
            INTEREST_QUERY,
            variables={"search": "Interest A"},
            headers=self.headers
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['interests']), 1)
        self.assertEqual(content['data']['interests'][0]['name'], "Interest A")

        response = self.query(
            INTEREST_QUERY,
            variables={"search": "*"},
            headers=self.headers
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['interests']), 2)

    def test_create_interest_not_logged_in(self):
        response = self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                "id_interest": 0,
                "name": "New Interest"
            }
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in !", content['errors'][0]['message'])

    def test_delete_not_logged_in(self):
        self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                "id_interest": 1,
                "name": "Interest to Delete"
            },
            headers=self.headers
        )

        response = self.query(
            DELETE_INTEREST_MUTATION,
            variables={"id_interest": 1}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_invalid_interest_id(self):
        response = self.query(
            DELETE_INTEREST_MUTATION,
            variables={"id_interest": 9999}, 
            headers=self.headers
        )
       
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Invalid Interest id!", content['errors'][0]['message'])

    def test_delete_interest_successfully(self):
        response_create = self.query(
            CREATE_INTEREST_MUTATION,
            variables={
                "id_interest": 0,
                "name": "Interest to Delete"
            },
            headers=self.headers
        )
        content_create = json.loads(response_create.content)
        created_interest_id = content_create['data']['createInterest']['idInterest']

        response = self.query(
            DELETE_INTEREST_MUTATION,
            variables={"id_interest": created_interest_id},
            headers=self.headers
        )
        
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['deleteInterest']['idInterest'], created_interest_id)

        interest_exists = Interest.objects.filter(id=created_interest_id).exists()
        self.assertFalse(interest_exists)
