import graphene
from graphene_django import DjangoObjectType
from .models import WorkExperience
from users.schema import UserType
from django.db.models import Q

class WorkExperienceType(DjangoObjectType):
    class Meta:
        model = WorkExperience

class Query(graphene.ObjectType):
    experiences = graphene.List(WorkExperienceType, search=graphene.String())
    experienceById = graphene.Field(WorkExperienceType, id_work_experience=graphene.Int())
    
    def resolve_experienceById(self, info, id_work_experience, **kwargs):
        user = info.context.user 
        
        if user.is_anonymous:
            raise Exception ('Not logged in')
        
        print (user)
        
        filter = (
            Q(posted_by=user) & Q(id = id_work_experience)
        )
        
        return WorkExperience.objects.filter(filter).first();

    def resolve_experiences(self, info, search=None, **kwargs):
        user = info.context.user
        
        if user.is_anonymous:
            raise Exception('Not logged in!')
        
        print (user)
        
        if (search=="*"):
            filter = (
                Q(posted_by=user)
            )
            
            return WorkExperience.objects.filter(filter)[:10]
        else:
            filter = (
                Q(posted_by=user) & Q(role__icontains=search)
            )
            
            return WorkExperience.objects.filter(filter)

class CreateWorkExperience(graphene.Mutation):
    id_work_experience = graphene.Int()
    role               = graphene.String()
    company            = graphene.String()
    accomplishments    = graphene.List(graphene.String)
    start_date         = graphene.Date()
    end_date           = graphene.Date()
    location           = graphene.String()
    posted_by          = graphene.Field(UserType)

    #2
    class Arguments:
        id_work_experience = graphene.Int()
        role               = graphene.String()
        company            = graphene.String()
        accomplishments    = graphene.List(graphene.String)
        start_date         = graphene.Date()
        end_date           = graphene.Date()
        location           = graphene.String()

    #3
    def mutate(self, info, id_work_experience, role, company, accomplishments, start_date, end_date, location):
        user = info.context.user or None
        
        if user.is_anonymous:
            raise Exception('Not logged in !');
        
        print(user)

        currentWorkExperience = WorkExperience.objects.filter(id=id_work_experience).first()
        print (currentWorkExperience)

        work_experience = WorkExperience(
            role            = role,
            company         = company,
            accomplishments = accomplishments,
            start_date      = start_date,
            end_date        = end_date,
            location        = location,
            posted_by       = user
            )

        if currentWorkExperience:
            work_experience.id = currentWorkExperience.id

        work_experience.save()

        return CreateWorkExperience(
            id_work_experience  = work_experience.id,
            role                = work_experience.role,
            company             = work_experience.company,
            accomplishments     = work_experience.accomplishments,
            start_date          = work_experience.start_date,
            end_date            = work_experience.end_date,
            location            = work_experience.location,
            posted_by           = work_experience.posted_by
        )

class DeleteWorkExperience(graphene.Mutation): 
    id_work_experience = graphene.Int() 
    
    #2 
    class Arguments: 
        id_work_experience = graphene.Int()
    
    #3
    def mutate(self, info, id_work_experience): 
        user = info.context.user or None 
        
        if user.is_anonymous: 
            raise Exception('Not logged in!')
        
        print (user) 
        
        currentWorkExperience = WorkExperience.objects.filter(id=id_work_experience).first()
        print(currentWorkExperience)
        
        if not currentWorkExperience:
            raise Exception('Invalid Work Experience id!')
        
        currentWorkExperience.delete()
        
        return DeleteWorkExperience(
            id_work_experience = id_work_experience,
        )

#4
class Mutation(graphene.ObjectType):
    create_work_experience = CreateWorkExperience.Field()
    delete_work_experience = DeleteWorkExperience.Field()
    
schema = graphene.Schema(query=Query, mutation=Mutation)