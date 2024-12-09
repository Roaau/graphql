from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from education.schema import schema
from education.models import Education

# Create your tests here.

EDUCATION_QUERY = '''
query GetDegrees($search: String) {
  degrees(search: $search) {
    id
    degree
  }
}
'''

EDUCATION_BY_ID_QUERY = '''
            query GetdegreeById($id_education: Int!) {
                degreeById(idEducation: $id_education) {
                    id
                    degree
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


CREATE_EDUCATION_MUTATION = '''
 mutation createEducationMutation($id_education: Int!, $degree: String, $university: String!,
    $start_date: Date!,
    $end_date: Date!) {
     createEducation(idEducation: $id_education, degree: $degree, university: $university,
        startDate: $start_date,
        endDate: $end_date) {
         idEducation
         degree
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

DELETE_EDUCATION_MUTATION = '''
mutation DeleteEducation($id_education: Int!) {
    deleteEducation(idEducation: $id_education) {
        idEducation
    }
}
'''

class EducationTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.education1 = mixer.blend(Education)
        self.education2 = mixer.blend(Education)
   
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


    def test_education_query(self):
        response = self.query(
            EDUCATION_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query education results ")
        print (response)
        assert len(content['data']['degrees']) == 0


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


    def test_createEducation_mutation(self):
        response = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                'id_education': 0,
                'degree': 'Software Engineer Degree',
                'university': 'Test University',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'},
            headers=self.headers
        )
        content = json.loads(response.content)
        created_education_id = content['data']['createEducation']['idEducation']
        print("Response content:", content)
        print(content['data'])
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createEducation": {"idEducation": created_education_id, "degree": "Software Engineer Degree"}}, content['data']) 
        
    def test_education_by_id_query(self):
        response_create = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                'id_education': 0,
                'degree': 'Software Engineer Degree',
                'university': 'Test University',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        print("Create Education Response:", content_create)
        created_education_id = content_create['data']['createEducation']['idEducation']

        response = self.query(
          EDUCATION_BY_ID_QUERY,
          variables={'id_education': created_education_id},
          headers=self.headers
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['degreeById']['degree'], "Software Engineer Degree")
        
    def test_update_existing_education(self):
        response_create = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                'id_education': 0,
                'degree': 'Software Engineer Degree', 
                'university': 'Test University',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        created_education_id = content_create['data']['createEducation']['idEducation']

        
        self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                'id_education': created_education_id,
                'degree': 'Management Degree', 
                'university': 'Test University',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'},
            headers=self.headers
        )

        response_query = self.query(
        EDUCATION_BY_ID_QUERY,
        variables={'id_education': created_education_id},
        headers=self.headers
        )
        
        content_query = json.loads(response_query.content)
                
        
        response_query_all = self.query(
            EDUCATION_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        
        content = json.loads(response_query_all.content)

        assert len(content['data']['degrees']) == 1
        self.assertEqual(content_query['data']['degreeById']['degree'], "Management Degree")
        
    def test_not_logged_in(self):
        response = self.query(
            EDUCATION_BY_ID_QUERY,
            variables={"id_education": 1}
        )
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in", content['errors'][0]['message'])

        response = self.query(
            EDUCATION_QUERY,
            variables={"search": "*"}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_filter_search(self):
        self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                'id_education': 1,
                'degree': 'Bachelor of Science',
                'university': 'Tech University',
                'start_date': '2020-01-01',
                'end_date': '2024-01-01'
            },
            headers=self.headers
        )

        self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                'id_education': 2,
                'degree': 'Master of Science',
                'university': 'Tech University',
                'start_date': '2020-01-01',
                'end_date': '2022-01-01'
            },
            headers=self.headers
        )

        response = self.query(
            EDUCATION_QUERY,
            variables={"search": "Bachelor"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['degrees']), 1)
        self.assertEqual(content['data']['degrees'][0]['degree'], "Bachelor of Science")

        response = self.query(
            EDUCATION_QUERY,
            variables={"search": "*"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['degrees']), 2)

    def test_create_education_not_logged_in(self):
        response = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                "id_education": 0,
                "degree": "Doctor of Philosophy",
                "university": "Research Institute",
                "start_date": "2015-09-01",
                "end_date": "2020-05-30"
            }
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_delete_not_logged_in(self):
        self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                "id_education": 1,
                "degree": "Certificate of Excellence",
                "university": "Tech University",
                "start_date": "2018-06-01",
                "end_date": "2020-12-31"
            },
            headers=self.headers
        )

        response = self.query(
            DELETE_EDUCATION_MUTATION,
            variables={"id_education": 1}
        )
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_invalid_education_id(self):
        response = self.query(
            DELETE_EDUCATION_MUTATION,
            variables={"id_education": 9999},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Invalid Education id!", content['errors'][0]['message'])

    def test_delete_education_successfully(self):
        response_create = self.query(
            CREATE_EDUCATION_MUTATION,
            variables={
                "id_education": 0,
                "degree": "Bachelor of Science",
                "university": "Tech University",
                "start_date": "2020-01-01",
                "end_date": "2024-01-01"
            },
            headers=self.headers
        )

        content_create = json.loads(response_create.content)
        created_education_id = content_create['data']['createEducation']['idEducation']

        response = self.query(
            DELETE_EDUCATION_MUTATION,
            variables={"id_education": created_education_id},
            headers=self.headers
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['deleteEducation']['idEducation'], created_education_id)

        education_exists = Education.objects.filter(id=created_education_id).exists()
        self.assertFalse(education_exists)
