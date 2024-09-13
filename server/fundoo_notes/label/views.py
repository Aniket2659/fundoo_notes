from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import DatabaseError
from loguru import logger
from django.http import Http404
from rest_framework.exceptions import ValidationError


from .models import Label
from .serializers import LabelSerializer
from drf_yasg.utils import swagger_auto_schema

class LabelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    A viewset for viewing, creating, updating, and deleting labels.

    Attributes:
        authentication_classes (list): List of authentication classes.
        permission_classes (list): List of permission classes.
        queryset (QuerySet): Default queryset for the viewset.
        serializer_class (class): Serializer class for the viewset.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Label.objects.all()
    serializer_class = LabelSerializer

    def get_queryset(self):
        """
        Limits queryset to the authenticated user's labels.

        Returns:
            QuerySet: Filtered queryset of labels.
        """
        return self.queryset.filter(user=self.request.user)
    
    @swagger_auto_schema(operation_description="Creation of label", request_body=LabelSerializer, responses={201: LabelSerializer, 400: "Bad Request: Invalid input data.",
                                                                                                             500: "Internal Server Error: An error occurred during creating label."})
    def create(self, request, *args, **kwargs):
        """
        Creates a new label for the authenticated user.

        Parameters:
            request (Request): The HTTP request object with label data.

        Returns:
            Response: Serialized label data or error message.
        """
        try:
            data = request.data.copy()
            data['user'] = request.user.id
            logger.info(f"Request Data: {data}")                                                              
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({                                                                                                                
                'message': 'Label created successfully',
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return Response({
                'message': 'Validation error',
                'status': 'error',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return Response({
                'message': 'Database error',
                'status': 'error',
                'errors': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                'message': 'An unexpected error occurred',
                'status': 'error',
                'errors': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a specific label for the authenticated user.

        Parameters:
            request (Request): The HTTP request object.
            pk (int): Primary key of the label.

        Returns:
            Response: Serialized label data or error message.
        """
        try:
            instance = self.get_object()
            if instance.user != request.user:
                return Response({
                'message': 'Permission denied',
                'status': 'error',
                'errors': 'You do not have permission to view this label'
            }, status=status.HTTP_403_FORBIDDEN)
            serializer = self.get_serializer(instance)
            return Response({
                'message': 'Label retrieved successfully',
                'status': 'success',
                'data': serializer.data
            })
        except Http404 as e:
            logger.warning(f"Label not found: {e}")
            return Response({
            'message': 'Label not found',
            'status': 'error',
            'errors': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                'message': 'An unexpected error occurred',
                'status': 'error',
                'errors': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @swagger_auto_schema(operation_description="Updation of label", request_body=LabelSerializer, responses={201: LabelSerializer, 400: "Bad Request: Invalid input data.",
                                                                                                             500: "Internal Server Error: An error occurred during updating label."})
    def update(self, request, *args, **kwargs):
        """
        Updates a specific label for the authenticated user.

        Parameters:
            request (Request): The HTTP request object with label data.
            pk (int): Primary key of the label.

        Returns:
            Response: Serialized label data or error message.
        """
        try:
            label_instance = self.get_object()
            if label_instance.user != request.user:
                return Response({
                    'message': 'Permission denied',
                    'status': 'error',
                    'errors': 'You do not have permission to update this label'
                }, status=status.HTTP_403_FORBIDDEN)

            data = request.data.copy()
            data['user'] = request.user.id
            serializer = self.get_serializer(label_instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                'message': 'Label updated successfully',
                'status': 'success',
                'data': serializer.data
            })
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return Response({
                'message': 'Validation error',
                'status': 'error',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            logger.warning(f"Label not found: {e}")
            return Response({
            'message': 'Label not found',
            'status': 'error',
            'errors': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                'message': 'An unexpected error occurred',
                'status': 'error',
                'errors': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @swagger_auto_schema(operation_description="Deletion of label", request_body=LabelSerializer, responses={201: LabelSerializer, 400: "Bad Request: Invalid input data.",
                                                                                                             500: "Internal Server Error: An error occurred during deleting label."})
    def destroy(self, request, *args, **kwargs):
        """
        Deletes a specific label for the authenticated user.

        Parameters:
            request (Request): The HTTP request object.
            pk (int): Primary key of the label.

        Returns:
            Response: Empty response or error message.
        """
        try:
            self.perform_destroy(self.get_object())
            return Response({
                'message': 'Label deleted successfully',
                'status': 'success'
            }, status=status.HTTP_204_NO_CONTENT)
        except Http404 as e:
            logger.warning(f"Label not found: {e}")
            return Response({
            'message': 'Label not found',
            'status': 'error',
            'errors': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                'message': 'An unexpected error occurred',
                'status': 'error',
                'errors': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        """
        Fetches all labels for the authenticated user.

        Parameters:
            request (Request): The HTTP request object.

        Returns:
            Response: Serialized list of labels or error message.
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'message': 'Labels retrieved successfully',
                'status': 'success',
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                'message': 'An unexpected error occurred',
                'status': 'error',
                'errors': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.db import connection, DatabaseError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from loguru import logger
from drf_yasg.utils import swagger_auto_schema
from .serializers import LabelSerializer
from .utils import dictfetchall  


class LabelListCreateAPIView(APIView):
    """
    API view for listing all labels and creating a new label.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='list_labels',
        tags=['Labels'],
        operation_description="List all labels for the authenticated user.",
        responses={
            200: LabelSerializer(many=True),
            500: "Internal Server Error: Error while fetching labels."
        }
    )
    def get(self, request):
        """
        Retrieve all labels for the authenticated user.
        """
        user_id = request.user.id
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM label WHERE user_id = %s", [user_id])
                labels = dictfetchall(cursor)
                return Response(labels, status=status.HTTP_200_OK)

        except DatabaseError as e:
            logger.error(f"Database error while fetching labels: {e}")
            return Response({"message": "Database error", "status": "error", "errors": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_id='create_label',
        tags=['Labels'],
        operation_description="Create a new label for the authenticated user.",
        request_body=LabelSerializer,
        responses={
            201: LabelSerializer,
            400: "Bad Request: Invalid input data.",
            500: "Internal Server Error: Error while creating label."
        }
    )
    def post(self, request):
        """
        Create a new label for the authenticated user.
        """
        user_id = request.user.id
        data = request.data
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO label (name, color, user_id) VALUES (%s, %s, %s) RETURNING id",
                               [data.get('name'), data.get('color'), user_id])
                new_id = cursor.fetchone()[0]
                label = {"id": new_id, "name": data.get('name'), "color": data.get('color'), "user_id": user_id}
                return Response(label, status=status.HTTP_201_CREATED)

        except DatabaseError as e:
            logger.error(f"Database error while creating label: {e}")
            return Response({"message": "Database error", "status": "error", "errors": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LabelDetailAPIView(APIView):
    """
    API view for retrieving, updating, and deleting a specific label.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='retrieve_label',
        tags=['Labels'],
        operation_description="Retrieve a specific label for the authenticated user.",
        responses={
            200: LabelSerializer,
            404: "Label not found.",
            500: "Internal Server Error: Error while fetching label."
        }
    )
    def get(self, request, label_id):
        """
        Retrieve a specific label for the authenticated user.
        """
        user_id = request.user.id
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM label WHERE id = %s AND user_id = %s", [label_id, user_id])
                row = cursor.fetchone()
                if row:
                    label = dict(zip([col[0] for col in cursor.description], row))
                    return Response(label, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Label not found."}, status=status.HTTP_404_NOT_FOUND)

        except DatabaseError as e:
            logger.error(f"Database error while fetching label: {e}")
            return Response({"message": "Database error", "status": "error", "errors": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_id='update_label',
        tags=['Labels'],
        operation_description="Update an existing label for the authenticated user.",
        request_body=LabelSerializer,
        responses={
            200: LabelSerializer,
            404: "Label not found or no permission to update.",
            500: "Internal Server Error: Error while updating label."
        }
    )
    def put(self, request, label_id):
        """
        Update an existing label for the authenticated user.
        """
        user_id = request.user.id
        data = request.data
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE label SET name = %s, color = %s WHERE id = %s AND user_id = %s",
                               [data.get('name'), data.get('color'), label_id, user_id])
                if cursor.rowcount == 0:
                    return Response({"error": "Label not found or no permission to update."}, status=status.HTTP_404_NOT_FOUND)
                return Response({"id": label_id, "name": data.get('name'), "color": data.get('color'), "user_id": user_id},
                                status=status.HTTP_200_OK)
        except DatabaseError as e:
            logger.error(f"Database error while updating label: {e}")
            return Response({"message": "Database error", "status": "error", "errors": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_id='delete_label',
        tags=['Labels'],
        operation_description="Delete a label for the authenticated user.",
        responses={
            204: "Label deleted successfully.",
            404: "Label not found or no permission to delete.",
            500: "Internal Server Error: Error while deleting label."
        }
    )
    def delete(self, request, label_id):
        """
        Delete a specific label for the authenticated user.
        """
        user_id = request.user.id
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM label WHERE id = %s AND user_id = %s", [label_id, user_id])
                if cursor.rowcount == 0:
                    return Response({"error": "Label not found or no permission to delete."}, status=status.HTTP_404_NOT_FOUND)
                return Response({"message": "Label deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except DatabaseError as e:
            logger.error(f"Database error while deleting label: {e}")
            return Response({"message": "Database error", "status": "error", "errors": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
