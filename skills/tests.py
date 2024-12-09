from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from mixer.backend.django import mixer
import graphene
import json
from django.contrib.auth import get_user_model

from skills.schema import schema
from skills.models import Skill

# Create your tests here.

SKILL_QUERY = '''
query GetSkills($search: String) {
  skills(search: $search) {
    id
    skill
  }
}
'''

SKILL_BY_ID_QUERY = '''
            query GetSkillById($id_skills: Int!) {
                skillById(idSkill: $id_skills) {
                    id
                    skill
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


CREATE_SKILL_MUTATION = '''
 mutation createSkillMutation($id_skills: Int!, $skill: String, $level: Int!) {
     createSkill(idSkill: $id_skills, skill: $skill, level: $level) {
         idSkill
         skill
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

DELETE_SKILL_MUTATION = '''
mutation DeleteSkill($id_skills: Int!) {
    deleteSkill(idSkill: $id_skills) {
        idSkill
    }
}
'''

class SkillTestCase(GraphQLTestCase):
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    GRAPHQL_SCHEMA = schema
    
    def setUp(self):
        self.skills1 = mixer.blend(Skill)           
        self.skills2 = mixer.blend(Skill)
   
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


    def test_skills_query(self):
        response = self.query(
            SKILL_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        print(response)
        content = json.loads(response.content)
        print(response.content)
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        print ("query skills results ")
        print (response)
        assert len(content['data']['skills']) == 0


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


    def test_createSkill_mutation(self):
        response = self.query(
            CREATE_SKILL_MUTATION,
            variables={
                'id_skills': 0,
                'skill': 'Resilience',
                'level': 4},
            headers=self.headers
        )
        content = json.loads(response.content)
        created_skills_id = content['data']['createSkill']['idSkill']
        print("Response content:", content)
        print(content['data'])
        self.assertResponseNoErrors(response)
        self.assertDictEqual({"createSkill": {"idSkill": created_skills_id, "skill": "Resilience"}}, content['data']) 
        
    def test_skills_by_id_query(self):
        response_create = self.query(
            CREATE_SKILL_MUTATION,
            variables={
                'id_skills': 0,
                'skill': 'Resilience',
                'level': 4},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        print("bbbbbbbbbbb:", content_create)
        created_skills_id = content_create['data']['createSkill']['idSkill']

        response = self.query(
          SKILL_BY_ID_QUERY,
          variables={'id_skills': created_skills_id},
          headers=self.headers
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['skillById']['skill'], "Resilience")
        
    def test_update_existing_skills(self):
        response_create = self.query(
            CREATE_SKILL_MUTATION,
            variables={
                'id_skills': 0,
                'skill': 'Resilience',
                'level': 4},
            headers=self.headers
        )
        
        content_create = json.loads(response_create.content)
        created_skills_id = content_create['data']['createSkill']['idSkill']

        
        self.query(
            CREATE_SKILL_MUTATION,
            variables={
                'id_skills': created_skills_id,
                'skill': 'Critical Thinking',
                'level': 4},
            headers=self.headers
        )

        response_query = self.query(
        SKILL_BY_ID_QUERY,
        variables={'id_skills': created_skills_id},
        headers=self.headers
        )
        
        content_query = json.loads(response_query.content)
                
        
        response_query_all = self.query(
            SKILL_QUERY,
             variables={
                'search': '*'},
            headers=self.headers
        )
        
        content = json.loads(response_query_all.content)

        assert len(content['data']['skills']) == 1
        self.assertEqual(content_query['data']['skillById']['skill'], "Critical Thinking")
        
    def test_not_logged_in(self):
        response = self.query(
            SKILL_BY_ID_QUERY,
            variables={"id_skills": 1}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in", content['errors'][0]['message'])

        response = self.query(
            SKILL_QUERY,
            variables={"search": "*"}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_filter_search(self):
        self.query(
            CREATE_SKILL_MUTATION,
            variables={
                'id_skills': 1,
                'skill': 'Resilience',
                'level': 4
            },
            headers=self.headers
        )

        self.query(
            CREATE_SKILL_MUTATION,
            variables={
                'id_skills': 2,
                'skill': 'Critical Thinking',
                'level': 5
            },
            headers=self.headers
        )

        response = self.query(
            SKILL_QUERY,
            variables={"search": "Resilience"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['skills']), 1)
        self.assertEqual(content['data']['skills'][0]['skill'], "Resilience")

        response = self.query(
            SKILL_QUERY,
            variables={"search": "*"},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(len(content['data']['skills']), 2)

    def test_create_skill_not_logged_in(self):
        response = self.query(
            CREATE_SKILL_MUTATION,
            variables={
                "id_skills": 0,
                "skill": "Problem Solving",
                "level": 5
            }
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in !", content['errors'][0]['message'])

    def test_delete_not_logged_in(self):
        self.query(
            CREATE_SKILL_MUTATION,
            variables={
                "id_skills": 1,
                "skill": "Problem Solving",
                "level": 5
            },
            headers=self.headers
        )

        response = self.query(
            DELETE_SKILL_MUTATION,
            variables={"id_skills": 1}
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Not logged in!", content['errors'][0]['message'])

    def test_invalid_skill_id(self):
        response = self.query(
            DELETE_SKILL_MUTATION,
            variables={"id_skills": 9999},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertIn('errors', content)
        self.assertIn("Invalid Skill id!", content['errors'][0]['message'])

    def test_delete_skill_successfully(self):
        response_create = self.query(
            CREATE_SKILL_MUTATION,
            variables={
                "id_skills": 0,
                "skill": "Adaptability",
                "level": 5
            },
            headers=self.headers
        )

        content_create = json.loads(response_create.content)
        created_skills_id = content_create['data']['createSkill']['idSkill']

        response = self.query(
            DELETE_SKILL_MUTATION,
            variables={"id_skills": created_skills_id},
            headers=self.headers
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['deleteSkill']['idSkill'], created_skills_id)

        skill_exists = Skill.objects.filter(id=created_skills_id).exists()
        self.assertFalse(skill_exists)