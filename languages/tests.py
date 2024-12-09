from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from languages.schema import schema
from languages.models import Language

# Create your tests here.

LANGUAGE_QUERY = '''
query GetLanguage($search: String) {
  languages(search: $search) {
    id
    name
  }
}
'''

LANGUAGE_BY_ID_QUERY = '''
            query GetLanguageById($id_language: Int!) {
                languageById(idLanguage: $id_language) {
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


CREATE_LANGUAGE_MUTATION = '''
 mutation createLanguageMutation($id_language: Int!, $name: String) {
     createLanguage(idLanguage: $id_language, name: $name) {
         idLanguage
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

DELETE_LANGUAGE_MUTATION = '''
mutation DeleteLanguage($id_language: Int!) {
    deleteLanguage(idLanguage: $id_language) {
        idLanguage
    }
}
'''

class LanguageTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.language1 = mixer.blend(Language)
        self.language2 = mixer.blend(Language)
   
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


    def test_language_query(self):
        response = self.query(
            LANGUAGE_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query languages results ")
        print (response)
        assert len(content['data']['languages']) == 0


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


    def test_createLanguage_mutation(self):
        response = self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                'id_language': 0,
                'name': 'Japanese'},
            headers=self.headers
        )
        content = json.loads(response.content)
        created_language_id = content['data']['createLanguage']['idLanguage']
        print("Response content:", content)
        print(content['data'])
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createLanguage": {"idLanguage": created_language_id, "name": "Japanese"}}, content['data']) 
        
    def test_language_by_id_query(self):
        response_create = self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                'id_language': 0,
                'name': 'Japanese'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        created_language_id = content_create['data']['createLanguage']['idLanguage']

        response = self.query(
          LANGUAGE_BY_ID_QUERY,
          variables={'id_language': created_language_id},
          headers=self.headers
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['languageById']['name'], "Japanese")
        
    def test_update_existing_language(self):
        response_create = self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                'id_language': 0,
                'name': 'Japanese'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        created_language_id = content_create['data']['createLanguage']['idLanguage']

        
        self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                'id_language': created_language_id,
                'name': 'English'},
            headers=self.headers
        )

        response_query = self.query(
        LANGUAGE_BY_ID_QUERY,
        variables={'id_language': created_language_id},
        headers=self.headers
        )
        
        content_query = json.loads(response_query.content)
        
        response_query_all = self.query(
            LANGUAGE_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        
        content = json.loads(response_query_all.content)

        assert len(content['data']['languages']) == 1
        self.assertEqual(content_query['data']['languageById']['name'], "English")

    def test_not_logged_in(self):
        response = self.query(
            LANGUAGE_BY_ID_QUERY,
            variables={"id_language": 1}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in", content['errors'][0]['message'])

        response = self.query(
            LANGUAGE_QUERY,
            variables={"search": "*"}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_filter_search(self):
        self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                'id_language': 1,
                'name': 'Japanese'
            },
            headers=self.headers
        )

        self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                'id_language': 2,
                'name': 'English'
            },
            headers=self.headers
        )

        response = self.query(
            LANGUAGE_QUERY,
            variables={"search": "Japanese"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['languages']), 1)
        self.assertEqual(content['data']['languages'][0]['name'], "Japanese")

        response = self.query(
            LANGUAGE_QUERY,
            variables={"search": "*"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['languages']), 2)

    def test_create_language_not_logged_in(self):
        response = self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                "id_language": 0,
                "name": "German"
            }
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in !", content['errors'][0]['message'])

    def test_delete_not_logged_in(self):
        self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                "id_language": 1,
                "name": "Spanish"
            },
            headers=self.headers
        )

        response = self.query(
            DELETE_LANGUAGE_MUTATION,
            variables={"id_language": 1}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_invalid_language_id(self):
        response = self.query(
            DELETE_LANGUAGE_MUTATION,
            variables={"id_language": 9999},
            headers=self.headers
        )
        
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Invalid Language id!", content['errors'][0]['message'])

    def test_delete_language_successfully(self):
        response_create = self.query(
            CREATE_LANGUAGE_MUTATION,
            variables={
                "id_language": 0,
                "name": "Italian"
            },
            headers=self.headers
        )
        content_create = json.loads(response_create.content)
        created_language_id = content_create['data']['createLanguage']['idLanguage']

        response = self.query(
            DELETE_LANGUAGE_MUTATION,
            variables={"id_language": created_language_id},
            headers=self.headers
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['deleteLanguage']['idLanguage'], created_language_id)

        language_exists = Language.objects.filter(id=created_language_id).exists()
        self.assertFalse(language_exists)