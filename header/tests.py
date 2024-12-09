from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import json
from django.contrib.auth import get_user_model

from header.schema import schema
from header.models import Header

# Query y Mutation Strings
HEADER_QUERY = '''
query GetHeaders($search: String) {
  headers(search: $search) {
    id
    name
  }
}
'''

HEADER_BY_ID_QUERY = '''
query GetHeaderById($id_header: Int!) {
    headerById(idHeader: $id_header) {
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

CREATE_HEADER_MUTATION = '''
mutation createHeaderMutation($name: String!,
    $description: String!,
    $image_url: String,
    $email: String!,
    $phone_number: String,
    $location: String!,
    $github: String!) {
     createHeader(name: $name,
        description: $description,
        imageUrl: $image_url,
        email: $email,
        phoneNumber: $phone_number,
        location: $location,
        github: $github) {
         idHeader
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

DELETE_HEADER_MUTATION = '''
mutation DeleteHeader($id_header: Int!) {
    deleteHeader(idHeader: $id_header) {
        idHeader
    }
}
'''

class HeaderTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.header1 = mixer.blend(Header)
        self.header2 = mixer.blend(Header)

        # Crear usuario
        response_user = self.query(
            CREATE_USER_MUTATION,
            variables={'email': 'adsoft@live.com.mx', 'username': 'adsoft', 'password': 'adsoft'}
        )
        content_user = json.loads(response_user.content)

        # Obtener token de autenticación
        response_token = self.query(
            LOGIN_USER_MUTATION,
            variables={'username': 'adsoft', 'password': 'adsoft'}
        )
        content_token = json.loads(response_token.content)
        token = content_token['data']['tokenAuth']['token']
        self.headers = {"AUTHORIZATION": f"JWT {token}"}

    def test_headers_query(self):
        # Crear un nuevo header
        self.query(
            CREATE_HEADER_MUTATION,
            variables={
                "name": "John Doe",
                "description": "A passionate software engineer.",
                "image_url": "https://example.com/profile.jpg",
                "email": "johndoe@example.com",
                "phone_number": "+123456789",
                "location": "New York, USA",
                "github": "https://github.com/johndoe"
            },
            headers=self.headers
        )
         
        response = self.query(
            HEADER_QUERY,
            variables={'search': '*'},
            headers=self.headers
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['headers']), 1)

    def test_users_query(self):
        response = self.query(USERS_QUERY)
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['users']), 3)

    def test_create_header_mutation(self):
        response = self.query(
            CREATE_HEADER_MUTATION,
            variables={
                "name": "John Doe",
                "description": "A passionate software engineer.",
                "image_url": "https://example.com/profile.jpg",
                "email": "johndoe@example.com",
                "phone_number": "+123456789",
                "location": "New York, USA",
                "github": "https://github.com/johndoe"
            },
            headers=self.headers
        )
        content = json.loads(response.content)
        created_headers_id = content['data']['createHeader']['idHeader']
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createHeader": {"idHeader": created_headers_id, "name": "John Doe"}}, content['data'])

    def test_query_invalid_id(self):
        response = self.query(
            HEADER_BY_ID_QUERY,
            variables={'id_header': 999},
            headers=self.headers
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertIsNone(content['data']['headerById'])

    def test_delete_not_logged_in(self):
        response = self.query(
            DELETE_HEADER_MUTATION,
            variables={"id_header": 1}
        )
        content = json.loads(response.content)
        self.assertIn('errors', content)
        self.assertIn("Not logged in", content['errors'][0]['message'])

    def test_delete_header_successfully(self):
        # Crear un header
        response_create = self.query(
            CREATE_HEADER_MUTATION,
            variables={
                'name': 'Header E',
                'description': 'This is header E.',
                'image_url': 'https://example.com/image5.jpg',
                'email': 'headere@example.com',
                'phone_number': '+222222222',
                'location': 'Seattle, USA',
                'github': 'https://github.com/headere'
            },
            headers=self.headers
        )
        content_create = json.loads(response_create.content)
        created_header_id = content_create['data']['createHeader']['idHeader']

        # Eliminar el header creado
        response = self.query(
            DELETE_HEADER_MUTATION,
            variables={"id_header": created_header_id},
            headers=self.headers
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['deleteHeader']['idHeader'], created_header_id)

        header_exists = Header.objects.filter(id=created_header_id).exists()
        self.assertFalse(header_exists)

    def test_update_existing_header(self):
        # Crear un header
        response_create = self.query(
            CREATE_HEADER_MUTATION,
            variables={
                'name': 'Header A',
                'description': 'Updated Description',
                'image_url': 'https://example.com/updated_image.jpg',
                'email': 'updated_header@example.com',
                'phone_number': '+987654321',
                'location': 'San Francisco, USA',
                'github': 'https://github.com/updatedheader'
            },
            headers=self.headers
        )
        content_create = json.loads(response_create.content)
        created_header_id = content_create['data']['createHeader']['idHeader']

        # Actualizar el header creado
        response = self.query(
            CREATE_HEADER_MUTATION,
            variables={
                'id_header': created_header_id,
                'name': 'Updated Header',
                'description': 'Updated Description',
                'image_url': 'https://example.com/updated_image.jpg',
                'email': 'updated_header@example.com',
                'phone_number': '+987654321',
                'location': 'San Francisco, USA',
                'github': 'https://github.com/updatedheader'
            },
            headers=self.headers
        )

        content_create = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content_create['data']['createHeader']['name'], "Updated Header")

        updated_header = Header.objects.get(id=created_header_id)
        self.assertEqual(updated_header.name, "Updated Header")