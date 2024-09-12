from .models import Note
from .serializers import SerializerNote
from rest_framework.decorators import action
from rest_framework import viewsets,status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError,NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from loguru import logger
from utils.redis_utils import RedisUtils
import json
from user_auth.models import User
from .utils import schedule_reminder
from .models import Note,Collaborator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from label.models import Label

# Create your views here.

class NotesViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing notes for an authenticated user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    redis=RedisUtils()


    queryset=Note.objects.all()
    serializer_class=SerializerNote
    @swagger_auto_schema(operation_description="Creation of note", request_body=SerializerNote, 
                         responses={201: SerializerNote, 400: "Bad Request: Invalid input data.", 500: "Internal Server Error: An error occurred during Creating note."})
    def create(self, request):
        """
        Create a new note for the user.
        Parameters: request (Request) - HTTP request with note data.
        Returns: Serialized note data or error message.
        """
        try:
            serializer = SerializerNote(data=request.data)
            serializer.is_valid(raise_exception=True)
            note=serializer.save(user=request.user)
            # Schedule the task if reminder is set
            if note.reminder: 
                schedule_reminder(note) 
            
            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data)
            else:
                notes_data = []

            notes_data.append(serializer.data)
            self.redis.save(cache_key, json.dumps(notes_data))
            return Response({
                    'message': 'successfully create',
                    'status': 'success',
                    'data':serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Unexpected error while creating note: {e}")

            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
  
    def list(self, request):
        """
        List all notes for the user.
        Parameters: request (Request) - HTTP request.
        Returns: Serialized list of notes or error message.
        """
        try:
            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)

            if notes_data:
                logger.info("Returning notes from cache.")
                notes_data = json.loads(notes_data) 

            else:
                queryset = Note.objects.filter(
                    Q(user=request.user) | Q(collaborator__user=request.user),
                    is_archive=False,
                    is_trash=False
                ).distinct() 
                serializer = SerializerNote(queryset, many=True)
                notes_data = serializer.data
                logger.info(f"info {notes_data}")

                notes_data_str = json.dumps(notes_data)
                self.redis.save(cache_key, notes_data_str)

            return Response({
                    'message': 'successfully showin list of note id',
                    'status': 'success',
                    'data':notes_data})
        except Exception as e:
            logger.error(f"Unexpected error while fetching notes: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def retrieve(self, request, pk=None):
        """
        desc: Retrieves a specific note for the authenticated user.
        params:
            request (Request): The HTTP request object.
            pk (int): Primary key of the note.
        return: Response: Serialized note data or error message.
        """
        try:
            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)

            if notes_data:
                notes_data = json.loads(notes_data)
                note_data = next(
                    (note for note in notes_data if note['id'] == int(pk)), None)  # type: ignore
                if note_data:
                    logger.info(f"Returning note {pk} from cache.")
                    return Response({
                        "message": "Note retrieved successfully",
                        "status": "success",
                        "data": note_data
                    })
                else:
                    raise ObjectDoesNotExist

            note = Note.objects.get(
                Q(pk=pk) & (Q(user=request.user) | Q(collaborator__user=request.user))
            )
            serializer = SerializerNote(note)
            note_data = serializer.data

            self.redis.save(cache_key, json.dumps(note_data))
            return Response({
                "message": "Note retrieved successfully",
                "status": "success",
                "data": note_data
            })
        except Exception as e:
            logger.error(f"Unexpected error while retrieving note: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @swagger_auto_schema(operation_description="Updation of note", request_body=SerializerNote, responses={201: SerializerNote, 400: "Bad Request: Invalid input data.",
                                                                                                           500: "Internal Server Error: An error occurred during updating note."})
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update a specific note by its ID.
        """
        try:
            instance = Note.objects.get(id=pk)
            if instance.user.id == request.user.id:
                data = request.data.copy()
                data['user'] = request.user.id
                
            else:
                collabrator = instance.collaborators_set.filter(user_id=request.user.id).first()
                
                if collabrator is None:
                    return Response({"Message":"You are not collaborator of this note",
                                     "satus":"Error"},status=status.HTTP_403_FORBIDDEN)
                
                if collabrator.access_type == "read_only":
                    return Response({"Message":"You only have read_only permission on this note",
                                     "satus":"Error"},status=status.HTTP_403_FORBIDDEN)
                    
                data = request.data.copy()
                data.pop('user',None)    
                        
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            # self.sechdule_reminder(pk)
            if serializer.instance.reminder:
                self.sechdule_reminder(serializer.instance,request.data['reminder'])
            note_cache_key = f"user_{request.user.id}_note_{pk}"
            self.redis.save(note_cache_key,serializer.data,ex=300)
            cache_key = f"user_{request.user.id}"
            queryset = self.get_queryset()
            self.redis.save(cache_key,self.get_serializer(queryset,many=True).data,ex=300)
            return Response({"Message":"The note is updated",
                             "satus":"Sucess",
                             "data":serializer.data},status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating note with ID {pk}: {str(e)}")
            return Response({
                'error': 'An error occurred while updating the note.',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Deletion of note", request_body=SerializerNote, responses={201: SerializerNote, 400: "Bad Request: Invalid input data.",
                                                                                                           500: "Internal Server Error: An error occurred during deleting note."})

    def destroy(self, request, pk=None):
        """
        Delete a note by ID for the user.
        Parameters: request (Request) - HTTP request, pk (int) - Note ID.
        Returns: Status 204 if successful, error message otherwise.
        """
        try:
            note = Note.objects.get(
                Q(pk=pk) & (Q(user=request.user) | Q(collaborator__user=request.user))
            )
            note.delete()
            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data) 
                notes_data = [
                    note for note in notes_data if note['id'] != int(pk)]

                self.redis.save(cache_key, json.dumps(notes_data))

            return Response({
                    'message': 'successfully deleted',
                    'status': 'success',
                },status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Unexpected error while deleting note: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @swagger_auto_schema(operation_description=" toggle Archive ", request_body=SerializerNote, responses={201: SerializerNote, 400: "Bad Request: Invalid input data.",
                                                                                                       500: "Internal Server Error: An error occurred during archive note."})

    @action(detail=True, methods=['patch'])
    def toggle_archive(self, request, pk=None):
        try:
            note = self.get_object()

            note.is_archive = not note.is_archive
            note.save()

            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)
            print(f"cashed toggle:{notes_data}")

            if notes_data:
                for cached_note in notes_data:
                    if cached_note['id'] == note.id:
                        cached_note['is_archive'] = note.is_archive
                        print("cache updated toggle archive")
                        break
                self.redis.save(cache_key, notes_data, expiry=3600)

            return Response({
                'user': request.user.email,
                'message': 'Note archive status toggled successfully.',
                'data': SerializerNote(note).data
            }, status=status.HTTP_200_OK)
        except NotFound:
            logger.error(f"Note with ID {pk} not found for user {request.user.email}.")
            return Response({
                'user': request.user.email,
                'error': 'Note not found.',
                'detail': 'The note with the provided ID does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred while toggling archive status for note with ID {pk} for user {request.user.email}: {str(e)}")
            return Response({
                'user': request.user.email,
                'error': 'An error occurred while toggling the archive status.',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def archived_notes(self, request):
        try:
            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)
            print(f"Archived Notes:{notes_data}")

            if notes_data:
                archived_notes = [note for note in notes_data if note.get('is_archive', False)]
                print(f"aechived notes:{archived_notes}")
                return Response({
                    'user': request.user.email,
                    'message': 'Archived notes retrieved successfully from cache.',
                    'data': archived_notes
                }, status=status.HTTP_200_OK)
            
            queryset = Note.objects.filter(user=request.user, is_archive=True)
            serializer = self.get_serializer(queryset, many=True)
            self.redis.save(cache_key, serializer.data, expiry=3600)
            
            return Response({
                'user': request.user.email,
                'message': 'Archived notes retrieved successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"An error occurred while retrieving archived notes for user {request.user.email}: {str(e)}")
            return Response({
                'user': request.user.email,
                'error': 'An error occurred while retrieving archived notes.',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

    @swagger_auto_schema(operation_description=" toggle trash ", request_body=SerializerNote, responses={201: SerializerNote, 400: "Bad Request: Invalid input data.",
                                                                                                       500: "Internal Server Error: An error occurred during trashed note."})

    @action(detail=True, methods=['patch'])
    def toggle_trash(self, request, pk=None):
        try:
            note = self.get_object()
            note.is_trash = not note.is_trash
            note.save()

            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)

            if notes_data:
                updated_note_data = SerializerNote(note).data
                updated_notes = [
                    updated_note_data if n['id'] == note.id else n
                    for n in notes_data
                ]
                self.redis.save(cache_key, updated_notes, expiry=3600)
                print("Toggle trash")
            else:
                queryset = self.get_queryset().filter(is_archive=False, is_trash=False)
                self.redis.save(cache_key, self.get_serializer(queryset, many=True).data, expiry=300)

            return Response({
                'user': request.user.email,
                'message': 'Note trash status toggled successfully.',
                'data': SerializerNote(note).data
            }, status=status.HTTP_200_OK)
        except NotFound:
            logger.error(f"Note with ID {pk} not found for user {request.user.email}.")
            return Response({
                'user': request.user.email,
                'error': 'Note not found.',
                'detail': 'The note with the provided ID does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred while toggling trash status for note with ID {pk} for user {request.user.email}: {str(e)}")
            return Response({
                'user': request.user.email,
                'error': 'An error occurred while toggling the trash status.',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def trashed_notes(self, request):
        try:
            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)

            if notes_data:
                
                trashed_notes = [note for note in notes_data if note.get('is_trash', False)]
                return Response({
                    'user': request.user.email,
                    'message': 'Trashed notes retrieved successfully from cache.',
                    'data': trashed_notes
                }, status=status.HTTP_200_OK)
            
            queryset = self.get_queryset().filter(is_trash=True)
            serializer = self.get_serializer(queryset, many=True)

            self.redis.save(cache_key, serializer.data, expiry=3600)
            return Response({
                'user': request.user.email,
                'message': 'Trashed notes retrieved successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"An error occurred while retrieving trashed notes for user {request.user.email}: {str(e)}")
            return Response({
                'user': request.user.email,
                'error': 'An error occurred while retrieving trashed notes.',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Add collaborators to a note",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'user_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER))
            }
        ),
        responses={
            200: "Collaborators added successfully",
            400: "Bad Request: Invalid input data.",
            404: "Not Found: Note not found.",
            500: "Internal Server Error: An error occurred during adding collaborators."
        }
    )
    @action(detail=False, methods=['post'])
    def add_collaborators(self, request):
        try:
            self.redis.delete(f"user_{request.user.id}")
            note_id = request.data.get('note_id')
            user_ids = request.data.get('user_ids', [])

            if not isinstance(user_ids, list):
                return Response(
                    {'message': 'Invalid data format for user_ids', 'status': 'error'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            note = Note.objects.get(pk=note_id, user=request.user)
            if request.user.id in user_ids:
                return Response(
                    {'message': 'Owner cannot be added as a collaborator', 'status': 'error'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            users = User.objects.filter(pk__in=user_ids)
            valid_user_ids = {user.id for user in users}

            # Create a list of Collaborator objects to be created
            collaborators = [
                Collaborator(note=note, user=user, access_type=Collaborator.READ_WRITE)
                for user in users
            ]

            Collaborator.objects.bulk_create(collaborators, ignore_conflicts=True)

            invalid_user_ids = set(user_ids) - valid_user_ids
            if invalid_user_ids:
                return Response(
                    {'message': f"Collaborators added successfully, but the following user_ids were not found: {list(invalid_user_ids)}", 
                     'status': 'partial_success'},
                    status=status.HTTP_200_OK
                )

            return Response(
                {'message': 'Collaborators added successfully', 
                'status': 'success'},
                status=status.HTTP_200_OK
            )

        except Note.DoesNotExist:
            return Response(
                {'message': 'Note not found', 
                'status': 'error',
                'errors': 'The requested note does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error while adding collaborators: {e}")
            return Response(
                {'message': 'An unexpected error occurred', 
                'status': 'error',
                'errors': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @swagger_auto_schema(
    operation_description="remove collaborator of the note API endpoint",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['note_id', 'user_id'],
        properties={
            'note_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the note'),
            'user_id': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER), description='List of user IDs to add'),
        }
    ),
    responses={
        200: 'Collaborator Remove successfully',
        403: 'You are not the owner of this note',
        404: 'One or more labels not found',
        400: 'Invalid input',
    }
)       
    @action(detail=False, methods=['post'])  
    def remove_collaborator(self,request):
        note_id = request.data.get('note_id')
        user_ids = request.data.get('user_id',[])
        
        note = Note.objects.filter(id=note_id).first()
        if not note:
            return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        
        Collaborator.objects.filter(note_id=note_id,user_id__in=user_ids).delete()
        
        return Response({"message":"Collaborator removed Successsfully",
                         "status":"success"}, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method='post',
        operation_description="Add labels to a note",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'label_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER))
            }
        ),
        responses={
            200: "Labels added successfully",
            400: "Bad Request: Invalid input data.",
            404: "Not Found: Note or labels not found.",
            500: "Internal Server Error: An error occurred during adding labels."
        }
    )
    @action(detail=False, methods=['post'])
    def add_labels(self, request):

        self.redis.delete(f"user_{request.user.id}")
        note_id = request.data.get('note_id')
        label_ids = request.data.get('label_ids', [])

        if not note_id or not isinstance(label_ids, list):
            return Response(
                {'message': 'Invalid input data', 'status': 'error'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            note = Note.objects.get(pk=note_id, user=request.user)
            labels = Label.objects.filter(id__in=label_ids)
            note.labels.add(*labels)
            return Response(
                {'message': 'Labels added successfully',
                'status': 'success'},
                status=status.HTTP_200_OK
            )

        except Note.DoesNotExist:
            return Response(
                {'message': 'Note not found',
                'status': 'error', 
                'errors': 'The requested note does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error while adding labels: {e}")
            return Response(
                {'message': 'An unexpected error occurred',
                 'status': 'error', 
                 'errors': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        method='post',
        operation_description="Remove labels from a note",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'label_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER))
            }
        ),
        responses={
            200: "Labels removed successfully",
            400: "Bad Request: Invalid input data.",
            404: "Not Found: Note or labels not found.",
            500: "Internal Server Error: An error occurred during removing labels."
        }
    )
    @action(detail=False, methods=['post'])
    def remove_labels(self, request):
        note_id = request.data.get('note_id')
        label_ids = request.data.get('label_ids', [])

        if not note_id or not isinstance(label_ids, list):
            return Response(
                {'message': 'Invalid input data', 'status': 'error'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            note = Note.objects.get(pk=note_id, user=request.user)
            labels = Label.objects.filter(id__in=label_ids)
            note.labels.remove(*labels)
            return Response(
                {'message': 'Labels removed successfully', 
                 'status': 'success'},
                status=status.HTTP_200_OK
            )

        except Note.DoesNotExist:
            return Response(
                {'message': 'Note not found', 
                 'status': 'error', 
                 'errors': 'The requested note does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error while removing labels: {e}")
            return Response(
                {'message': 'An unexpected error occurred', 
                 'status': 'error', 
                 'errors': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )