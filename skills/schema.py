import graphene
from graphene_django import DjangoObjectType
from .models import Skill
from users.schema import UserType
from django.db.models import Q

class SkillType(DjangoObjectType):
    class Meta:
        model = Skill

class Query(graphene.ObjectType):
    skills = graphene.List(SkillType, search=graphene.String())
    skillById = graphene.Field(SkillType, id_skill=graphene.Int())
    
    def resolve_skillById(self, info, id_skill, **kwargs):
        user = info.context.user 
        
        if user.is_anonymous:
            raise Exception ('Not logged in')
        
        print (user)
        
        filter = (
            Q(posted_by=user) & Q(id = id_skill)
        )
        
        return Skill.objects.filter(filter).first();

    def resolve_skills(self, info, search=None, **kwargs):
        user = info.context.user
        
        if user.is_anonymous:
            raise Exception('Not logged in!')
        
        print (user)
        
        if (search=="*"):
            filter = (
                Q(posted_by=user)
            )
            
            return Skill.objects.filter(filter)[:10]
        else:
            filter = (
                Q(posted_by=user) & Q(skill__icontains=search)
            )
            
            return Skill.objects.filter(filter)

class CreateSkill(graphene.Mutation):
    id_skill  = graphene.Int()
    skill     = graphene.String()
    level     = graphene.Int()
    posted_by = graphene.Field(UserType)

    #2
    class Arguments:
        id_skill  = graphene.Int()
        skill     = graphene.String()
        level     = graphene.Int()

    #3
    def mutate(self, info, id_skill, skill, level):
        user = info.context.user or None
        
        if user.is_anonymous:
            raise Exception('Not logged in !');
        
        print(user)

        currentSkill = Skill.objects.filter(id=id_skill).first()
        print (currentSkill)

        skill = Skill(
            skill     = skill,
            level     = level,
            posted_by = user
            )

        if currentSkill:
            skill.id = currentSkill.id

        skill.save()

        return CreateSkill(
            id_skill  = skill.id,
            skill     = skill.skill,
            level     = skill.level,
            posted_by = skill.posted_by
        )

class DeleteSkill(graphene.Mutation): 
    id_skill = graphene.Int() 
    
    #2 
    class Arguments: 
        id_skill = graphene.Int()
    
    #3
    def mutate(self, info, id_skill): 
        user = info.context.user or None 
        
        if user.is_anonymous: 
            raise Exception('Not logged in!')
        
        print (user) 
        
        currentSkill = Skill.objects.filter(id=id_skill).first()
        print(currentSkill)
        
        if not currentSkill:
            raise Exception('Invalid Skill id!')
        
        currentSkill.delete()
        
        return DeleteSkill(
            id_skill = id_skill,
        )

#4
class Mutation(graphene.ObjectType):
    create_skill = CreateSkill.Field()
    delete_skill = DeleteSkill.Field()
    
schema = graphene.Schema(query=Query, mutation=Mutation)