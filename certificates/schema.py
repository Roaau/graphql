import graphene
from graphene_django import DjangoObjectType
from .models import Certificate
from users.schema import UserType
from django.db.models import Q

class CertificateType(DjangoObjectType):
    class Meta:
        model = Certificate

class Query(graphene.ObjectType):
    certificates = graphene.List(CertificateType, search=graphene.String())
    certificateById = graphene.Field(CertificateType, id_certificate=graphene.Int())
    
    def resolve_certificateById(self, info, id_certificate, **kwargs):
        user = info.context.user 
        
        if user.is_anonymous:
            raise Exception ('Not logged in')
        
        print (user)
        
        filter = (
            Q(posted_by=user) & Q(id = id_certificate)
        )
        
        return Certificate.objects.filter(filter).first();

    def resolve_certificates(self, info, search=None, **kwargs):
        user = info.context.user
        
        if user.is_anonymous:
            raise Exception('Not logged in!')
        
        print (user)
        
        if (search=="*"):
            filter = (
                Q(posted_by=user)
            )
            
            return Certificate.objects.filter(filter)[:10]
        else:
            filter = (
                Q(posted_by=user) & Q(title__icontains=search)
            )
            
            return Certificate.objects.filter(filter)

class CreateCertificate(graphene.Mutation):
    id_certificate = graphene.Int()
    title          = graphene.String()
    date           = graphene.Date()
    description    = graphene.String()
    posted_by      = graphene.Field(UserType)

    #2
    class Arguments:
        id_certificate  = graphene.Int()
        title           = graphene.String()
        date            = graphene.Date()
        description     = graphene.String()

    #3
    def mutate(self, info, id_certificate, title, date, description):
        user = info.context.user or None
        
        if user.is_anonymous:
            raise Exception('Not logged in !');
        
        print(user)

        currentCertificate = Certificate.objects.filter(id=id_certificate).first()
        print (currentCertificate)

        certificate = Certificate(
            title       = title,
            date        = date,
            description = description,
            posted_by   = user
            )

        if currentCertificate:
            certificate.id = currentCertificate.id

        certificate.save()

        return CreateCertificate(
            id_certificate  = certificate.id,
            title           = certificate.title,
            date            = certificate.date,
            description     = certificate.description,
            posted_by       = certificate.posted_by
        )

class DeleteCertificate(graphene.Mutation): 
    id_certificate = graphene.Int() 
    
    #2 
    class Arguments: 
        id_certificate = graphene.Int()
    
    #3
    def mutate(self, info, id_certificate): 
        user = info.context.user or None 
        
        if user.is_anonymous: 
            raise Exception('Not logged in!')
        
        print (user) 
        
        currentCertificate = Certificate.objects.filter(id=id_certificate).first()
        print(currentCertificate)
        
        if not currentCertificate:
            raise Exception('Invalid Certificate id!')
        
        currentCertificate.delete()
        
        return DeleteCertificate(
            id_certificate = id_certificate,
        )

#4
class Mutation(graphene.ObjectType):
    create_certificate = CreateCertificate.Field()
    delete_certificate = DeleteCertificate.Field()
    
schema = graphene.Schema(query=Query, mutation=Mutation)