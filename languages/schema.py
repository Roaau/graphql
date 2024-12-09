import graphene
from graphene_django import DjangoObjectType
from .models import Language
from users.schema import UserType
from django.db.models import Q

class LanguageType(DjangoObjectType):
    class Meta:
        model = Language

class Query(graphene.ObjectType):
    languages = graphene.List(LanguageType, search=graphene.String())
    languageById = graphene.Field(LanguageType, id_language=graphene.Int())
    
    def resolve_languageById(self, info, id_language, **kwargs):
        user = info.context.user 
        
        if user.is_anonymous:
            raise Exception ('Not logged in')
        
        print (user)
        
        filter = (
            Q(posted_by=user) & Q(id = id_language)
        )
        
        return Language.objects.filter(filter).first();

    def resolve_languages(self, info, search=None, **kwargs):
        user = info.context.user
        
        if user.is_anonymous:
            raise Exception('Not logged in!')
        
        print (user)
        
        if (search=="*"):
            filter = (
                Q(posted_by=user)
            )
            
            return Language.objects.filter(filter)[:10]
        else:
            filter = (
                Q(posted_by=user) & Q(name__icontains=search)
            )
            
            return Language.objects.filter(filter)

class CreateLanguage(graphene.Mutation):
    id_language = graphene.Int()
    name        = graphene.String()
    posted_by   = graphene.Field(UserType)

    #2
    class Arguments:
        id_language  = graphene.Int()
        name         = graphene.String()

    #3
    def mutate(self, info, id_language, name):
        user = info.context.user or None
        
        if user.is_anonymous:
            raise Exception('Not logged in !');
        
        print(user)

        currentLanguage = Language.objects.filter(id=id_language).first()
        print (currentLanguage)

        language = Language(
            name      = name,
            posted_by = user
            )

        if currentLanguage:
            language.id = currentLanguage.id

        language.save()

        return CreateLanguage(
            id_language = language.id,
            name        = language.name,
            posted_by   = language.posted_by
        )

class DeleteLanguage(graphene.Mutation): 
    id_language = graphene.Int() 
    
    #2 
    class Arguments: 
        id_language = graphene.Int()
    
    #3
    def mutate(self, info, id_language): 
        user = info.context.user or None 
        
        if user.is_anonymous: 
            raise Exception('Not logged in!')
        
        print (user) 
        
        currentLanguage = Language.objects.filter(id=id_language).first()
        print(currentLanguage)
        
        if not currentLanguage:
            raise Exception('Invalid Language id!')
        
        currentLanguage.delete()
        
        return DeleteLanguage(
            id_language = id_language,
        )

#4
class Mutation(graphene.ObjectType):
    create_language = CreateLanguage.Field()
    delete_language = DeleteLanguage.Field()
    
schema = graphene.Schema(query=Query, mutation=Mutation)