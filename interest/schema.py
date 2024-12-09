import graphene
from graphene_django import DjangoObjectType
from .models import Interest
from users.schema import UserType
from django.db.models import Q

class InterestType(DjangoObjectType):
    class Meta:
        model = Interest

class Query(graphene.ObjectType):
    interests = graphene.List(InterestType, search=graphene.String())
    interestById = graphene.Field(InterestType, id_interest=graphene.Int())
    
    def resolve_interestById(self, info, id_interest, **kwargs):
        user = info.context.user 
        
        if user.is_anonymous:
            raise Exception ('Not logged in')
        
        print (user)
        
        filter = (
            Q(posted_by=user) & Q(id = id_interest)
        )
        
        return Interest.objects.filter(filter).first();

    def resolve_interests(self, info, search=None, **kwargs):
        user = info.context.user
        
        if user.is_anonymous:
            raise Exception('Not logged in!')
        
        print (user)
        
        if (search=="*"):
            filter = (
                Q(posted_by=user)
            )
            
            return Interest.objects.filter(filter)[:10]
        else:
            filter = (
                Q(posted_by=user) & Q(name__icontains=search)
            )
            
            return Interest.objects.filter(filter)

class CreateInterest(graphene.Mutation):
    id_interest = graphene.Int()
    name        = graphene.String()
    posted_by   = graphene.Field(UserType)

    #2
    class Arguments:
        id_interest = graphene.Int()
        name        = graphene.String()

    #3
    def mutate(self, info, id_interest, name):
        user = info.context.user or None
        
        if user.is_anonymous:
            raise Exception('Not logged in !');
        
        print(user)

        currentInterest = Interest.objects.filter(id=id_interest).first()
        print (currentInterest)

        interest = Interest(
            name      = name,
            posted_by = user
            )

        if currentInterest:
            interest.id = currentInterest.id

        interest.save()

        return CreateInterest(
            id_interest = interest.id,
            name        = interest.name,
            posted_by   = interest.posted_by
        )

class DeleteInterest(graphene.Mutation): 
    id_interest = graphene.Int() 
    
    #2 
    class Arguments: 
        id_interest = graphene.Int()
    
    #3
    def mutate(self, info, id_interest): 
        user = info.context.user or None 
        
        if user.is_anonymous: 
            raise Exception('Not logged in!')
        
        print (user) 
        
        currentInterest = Interest.objects.filter(id=id_interest).first()
        print(currentInterest)
        
        if not currentInterest:
            raise Exception('Invalid Interest id!')
        
        currentInterest.delete()
        
        return DeleteInterest(
            id_interest = id_interest,
        )

#4
class Mutation(graphene.ObjectType):
    create_interest = CreateInterest.Field()
    delete_interest = DeleteInterest.Field()
    
schema = graphene.Schema(query=Query, mutation=Mutation)