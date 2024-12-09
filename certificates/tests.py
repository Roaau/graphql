from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from certificates.schema import schema
from certificates.models import Certificate

# Create your tests here.

CERTIFICATE_QUERY = '''
query GetCertificates($search: String) {
  certificates(search: $search) {
    id
    title
  }
}
'''

CERTIFICATE_BY_ID_QUERY = '''
            query GetCertificateById($id_certificate: Int!) {
                certificateById(idCertificate: $id_certificate) {
                    id
                    title
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


CREATE_CERTIFICATE_MUTATION = '''
 mutation createCertificateMutation($id_certificate: Int!, $title: String, $date: Date!,
    $description: String!) {
     createCertificate(idCertificate: $id_certificate, title: $title, date: $date,
        description: $description) {
         idCertificate
         title
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

DELETE_CERTIFICATE_MUTATION = '''
mutation DeleteCertificate($id_certificate: Int!) {
    deleteCertificate(idCertificate: $id_certificate) {
        idCertificate
    }
}
'''

class CertificateTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.certificate1 = mixer.blend(Certificate)
        self.certificate2 = mixer.blend(Certificate)
   
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


    def test_certificate_query(self):
        response = self.query(
            CERTIFICATE_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query certificate results ")
        print (response)
        assert len(content['data']['certificates']) == 0


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


    def test_createCertificate_mutation(self):
        response = self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                'id_certificate': 0,
                'title': 'AI Certificate',
                'date': '2023-11-15',  
                'description': 'This is a test certificate.'},
            headers=self.headers
        )
        content = json.loads(response.content)
        created_certificate_id = content['data']['createCertificate']['idCertificate']
        print("Response content:", content)
        print(content['data'])
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createCertificate": {"idCertificate": created_certificate_id, "title": "AI Certificate"}}, content['data']) 
        
    def test_certificate_by_id_query(self):
        response_create = self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                'id_certificate': 0,
                'title': 'AI Certificate',
                'date': '2023-11-15', 
                'description': 'This is a test certificate.'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        print("Create Certificate Response:", content_create)
        created_certificate_id = content_create['data']['createCertificate']['idCertificate']

        response = self.query(
          CERTIFICATE_BY_ID_QUERY,
          variables={'id_certificate': created_certificate_id},
          headers=self.headers
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['certificateById']['title'], "AI Certificate")
        
    def test_update_existing_certificate(self):
        response_create = self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                'id_certificate': 0,
                'title': 'AI Certificate', 
                'date': '2023-11-15',  
                'description': 'This is a test certificate.'},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        created_certificate_id = content_create['data']['createCertificate']['idCertificate']

        
        self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                'id_certificate': created_certificate_id,
                'title': 'Deep Learning Certificate', 
                'date': '2023-11-15', 
                'description': 'This is a test certificate.'},
            headers=self.headers
        )

        response_query = self.query(
        CERTIFICATE_BY_ID_QUERY,
        variables={'id_certificate': created_certificate_id},
        headers=self.headers
        )
        
        content_query = json.loads(response_query.content)
                
        
        response_query_all = self.query(
            CERTIFICATE_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        
        content = json.loads(response_query_all.content)

        assert len(content['data']['certificates']) == 1
        self.assertEqual(content_query['data']['certificateById']['title'], "Deep Learning Certificate")
        
    def test_not_logged_in(self):
        response = self.query(
            CERTIFICATE_BY_ID_QUERY,
            variables={"id_certificate": 1}
        )
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in", content['errors'][0]['message'])

        response = self.query(
            CERTIFICATE_QUERY,
            variables={"search": "*"}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])
        
    def test_filter_search(self):
        self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                'id_certificate': 1,
                'title': 'Certificate A', 
                'date': '2023-11-15', 
                'description': 'This is a test certificate.'},
            headers=self.headers
        )
        
        self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                'id_certificate': 2,
                'title': 'Certificate B', 
                'date': '2023-11-15', 
                'description': 'This is a test certificate.'},
            headers=self.headers
        )
        
        
        response = self.query(
            CERTIFICATE_QUERY,
            variables={"search": "Certificate A"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['certificates']), 1)
        self.assertEqual(content['data']['certificates'][0]['title'], "Certificate A")

        response = self.query(
            CERTIFICATE_QUERY,
            variables={"search": "*"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['certificates']), 2)
        
    def test_create_certificate_not_logged_in(self):
        response = self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                "id_certificate": 0,
                "title": "Certificate of Excellence",
                "date": "2023-11-20",
                "description": "Awarded for outstanding performance."
            }
        )
        
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in !", content['errors'][0]['message'])
        
    def test_delete_not_logged_in(self):
        self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                "id_certificate": 1,
                "title": "Certificate of Excellence",
                "date": "2023-11-20",
                "description": "Awarded for outstanding performance."
            })
        
        response = self.query(
            DELETE_CERTIFICATE_MUTATION,
            variables={"id_certificate": 1}
        )
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])
        
    def test_invalid_certificate_id(self):
        response = self.query(
            DELETE_CERTIFICATE_MUTATION,
            variables={"id_certificate": 9999},
            headers=self.headers
        )
        
        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Invalid Certificate id!", content['errors'][0]['message'])
        
    def test_delete_certificate_successfully(self):
        response_create = self.query(
            CREATE_CERTIFICATE_MUTATION,
            variables={
                "id_certificate": 0,
                "title": "Certificate of Excellence",
                "date": "2023-11-20",
                "description": "Awarded for outstanding performance."
            },
            headers=self.headers
            )
        
        content_create = json.loads(response_create.content)
        created_certificate_id = content_create['data']['createCertificate']['idCertificate']
        
        response = self.query(
            DELETE_CERTIFICATE_MUTATION,
            variables={"id_certificate": created_certificate_id},
            headers=self.headers
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['deleteCertificate']['idCertificate'], created_certificate_id)

        certificate_exists = Certificate.objects.filter(id=created_certificate_id).exists()
        self.assertFalse(certificate_exists)
