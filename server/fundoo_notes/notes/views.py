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
from .utils import schedule_reminder
from .models import Note

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
                queryset = Note.objects.filter(user=request.user)
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
                notes_data = json.loads(notes_data) # type: ignore
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

            note = Note.objects.get(pk=pk, user=request.user)
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
    def update(self, request, pk=None):
        """
        Update an existing note for the user.
        Parameters: request (Request) - HTTP request, pk (int) - Note ID.
        Returns: Serialized updated note data or error message.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = SerializerNote(note, data=request.data)
            serializer.is_valid(raise_exception=True)
            note=serializer.save()

            if note.reminder:
                schedule_reminder(note)


            cache_key = f"user_{request.user.id}"
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data) 
                for idx, existing_note in enumerate(notes_data):
                    if existing_note['id'] == int(pk):  
                        notes_data[idx] = serializer.data
                        break

                self.redis.save(cache_key, json.dumps(notes_data))

            return Response({
                    'message': 'successfully updated',
                    'status': 'success',
                    'data':serializer.data})
        except Exception as e:
            logger.error(f"Unexpected error while updating note: {e}")

            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        """
        Delete a note by ID for the user.
        Parameters: request (Request) - HTTP request, pk (int) - Note ID.
        Returns: Status 204 if successful, error message otherwise.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
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
    