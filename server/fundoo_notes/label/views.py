from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import DatabaseError
from loguru import logger

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
                'errors': e.message_dict
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
            serializer = self.get_serializer(instance)
            return Response({
                'message': 'Label retrieved successfully',
                'status': 'success',
                'data': serializer.data
            })
        except ObjectDoesNotExist as e:
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
                'errors': e.message_dict
            }, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
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
        except ObjectDoesNotExist as e:
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
