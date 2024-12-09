import graphene
from graphene_django import DjangoObjectType
from .models import Header
from users.schema import UserType
from django.db.models import Q


# Define el tipo de objeto GraphQL para Header
class HeaderType(DjangoObjectType):
    class Meta:
        model = Header


# Definición de la clase Query para las consultas
class Query(graphene.ObjectType):
    headers = graphene.List(HeaderType, search=graphene.String())
    headerById = graphene.Field(HeaderType, id_header=graphene.Int())

    def resolve_headerById(self, info, id_header, **kwargs):
        user = info.context.user

        if user.is_anonymous:
            raise Exception('Not logged in')

        print(user)

        # Filtra por usuario y id_header
        filter = (
            Q(posted_by=user) & Q(id=id_header)
        )

        return Header.objects.filter(filter).first()

    def resolve_headers(self, info, search=None, **kwargs):
        user = info.context.user

        if user.is_anonymous:
            raise Exception('Not logged in!')

        print(user)

        # Si no hay búsqueda, se devuelve todo lo que el usuario ha creado
        if search == "*":
            filter = (
                Q(posted_by=user)
            )
            return Header.objects.filter(filter)[:10]
        else:
            # Filtro por el nombre si search no es "*"
            filter = (
                Q(posted_by=user) & Q(name__icontains=search)
            )
            return Header.objects.filter(filter)


# Definición de la mutación para crear un nuevo Header
class CreateHeader(graphene.Mutation):
    id_header = graphene.Int()
    name = graphene.String()
    description = graphene.String()
    image_url = graphene.String()
    email = graphene.String()
    phone_number = graphene.String()
    location = graphene.String()
    github = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        name = graphene.String()
        description = graphene.String()
        image_url = graphene.String()
        email = graphene.String()
        phone_number = graphene.String()
        location = graphene.String()
        github = graphene.String()
        id_header = graphene.Int()  # ID opcional para editar el header existente

    def mutate(self, info, name, description, image_url, email, phone_number, location, github, id_header=None):
        user = info.context.user

        if user.is_anonymous:
            raise Exception('Not logged in!')

        print(user)

        if id_header:
            # Si se proporciona un ID, intentamos encontrar el Header existente
            currentHeader = Header.objects.filter(id=id_header, posted_by=user).first()

            if currentHeader:
                # Si el Header existe, lo actualizamos
                currentHeader.name = name
                currentHeader.description = description
                currentHeader.image_url = image_url
                currentHeader.email = email
                currentHeader.phone_number = phone_number
                currentHeader.location = location
                currentHeader.github = github
                currentHeader.save()

                return CreateHeader(
                    id_header=currentHeader.id,
                    name=currentHeader.name,
                    description=currentHeader.description,
                    image_url=currentHeader.image_url,
                    email=currentHeader.email,
                    phone_number=currentHeader.phone_number,
                    location=currentHeader.location,
                    github=currentHeader.github,
                    posted_by=currentHeader.posted_by
                )
            else:
                raise Exception('Header not found or not owned by the user')

        # Si no se proporciona un ID, creamos un nuevo Header
        header = Header(
            name=name,
            description=description,
            image_url=image_url,
            email=email,
            phone_number=phone_number,
            location=location,
            github=github,
            posted_by=user
        )
        header.save()

        return CreateHeader(
            id_header=header.id,
            name=header.name,
            description=header.description,
            image_url=header.image_url,
            email=header.email,
            phone_number=header.phone_number,
            location=header.location,
            github=header.github,
            posted_by=header.posted_by
        )


# Definición de la mutación para eliminar un Header
class DeleteHeader(graphene.Mutation):
    id_header = graphene.Int()

    class Arguments:
        id_header = graphene.Int()

    def mutate(self, info, id_header):
        user = info.context.user

        if user.is_anonymous:
            raise Exception('Not logged in!')

        print(user)

        # Busca el Header a eliminar
        currentHeader = Header.objects.filter(id=id_header).first()
        print(currentHeader)

        if not currentHeader:
            raise Exception('Invalid Header id!')

        # Elimina el Header
        currentHeader.delete()

        return DeleteHeader(
            id_header=id_header,
        )


# Clase que agrupa las mutaciones disponibles
class Mutation(graphene.ObjectType):
    create_header = CreateHeader.Field()
    delete_header = DeleteHeader.Field()


# Definición del esquema con la Query y Mutation
schema = graphene.Schema(query=Query, mutation=Mutation)
