from .models import Note
from .serializers import SerializerNote
from rest_framework.decorators import action
from rest_framework import viewsets,status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from loguru import logger

# Create your views here.

class NotesViewSet(viewsets.ViewSet):
    """
    A ViewSet for managing notes for an authenticated user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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
            serializer.save(user=request.user)
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
            queryset = Note.objects.filter(user=request.user)
            serializer = SerializerNote(queryset, many=True)
            return Response({
                    'message': 'successfully showin list of note id',
                    'status': 'success',
                    'data':serializer.data})
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
        Retrieve a note by ID for the user.
        Parameters: request (Request) - HTTP request, pk (int) - Note ID.
        Returns: Serialized note data or error message.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = SerializerNote(note)
            return Response({
                    'message': 'successfully retrieve by note id',
                    'status': 'success',
                    'data':serializer.data})
        except Exception as e:
            logger.error(f"Unexpected error while retrieve note: {e}")

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
            serializer.save()
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
    def is_archive(self, request, pk=None):
        """
        desc: Toggles the archive status of a specific note.
        params:
            request (Request): The HTTP request object.
            pk (int): Primary key of the note.
        return: Response: Updated note data or error message.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.is_archive = not note.is_archive
            note.save()
            serializer = SerializerNote(note)
            return Response({
                    'message': 'successfully toggele ',
                    'status': 'success',
                    'data':serializer.data})
        except ObjectDoesNotExist:
            return Response(
                {
                    'message': 'Note not found',
                    'status': 'error',
                    'errors': 'The requested note does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError as e:
            logger.error(f"Database error while toggling archive status: {e}")
            return Response(
                {
                    'message': 'Failed to toggle archive status',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error while toggling archive status: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def archived(self, request):
        """
        desc: Fetches all archived notes for the authenticated user.
        params: request (Request): The HTTP request object.
        return: Response: Serialized list of archived notes or error message.
        """
        try:
            queryset = Note.objects.filter(user=request.user, is_archive=True)
            serializer = SerializerNote(queryset, many=True)
            return Response({
                    'message': 'successfully retrieve',
                    'status': 'success',
                    'data':serializer.data})
        except DatabaseError as e:
            logger.error(f"Database error while fetching archived notes: {e}")
            return Response(
                {
                    'message': 'Failed to fetch archived notes',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error while toggling archive status: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'])
    def is_trash(self, request, pk=None):
        """
        desc: Toggles the trash status of a specific note.
        params:
            request (Request): The HTTP request object.
            pk (int): Primary key of the note.
        return: Response: Updated note data or error message.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.is_trash = not note.is_trash
            note.save()
            serializer = SerializerNote(note)
            return Response({
                    'message': 'successfully updated',
                    'status': 'success',
                    'data':serializer.data})
        except ObjectDoesNotExist:
            return Response(
                {
                    'message': 'Note not found',
                    'status': 'error',
                    'errors': 'The requested note does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError as e:
            logger.error(f"Database error while fetching trashed notes: {e}")

            return Response(
                {
                    'message': 'Failed to toggle trash status',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error while toggling trashed status: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def trashed(self, request):
        """
        desc: Fetches all trashed notes for the authenticated user.
        params: request (Request): The HTTP request object.
        return: Response: Serialized list of trashed notes or error message.
        """
        try:
            queryset = Note.objects.filter(user=request.user, is_trash=True)
            serializer = SerializerNote(queryset, many=True)
            return Response({
                    'message': 'successfully showing',
                    'status': 'success',
                    'data':serializer.data})
        except DatabaseError as e:
            logger.error(f"Database error while fetching trashed notes: {e}")
            return Response(
                {
                    'message': 'Failed to fetch trashed notes',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error while toggling trashed status: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )