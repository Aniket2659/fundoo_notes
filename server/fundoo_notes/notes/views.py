from .models import Note
from .serializers import SerializerNote
from rest_framework import viewsets,status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
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
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


