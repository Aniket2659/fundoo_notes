from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from rest_framework.exceptions import ValidationError

class RegisterUserView(APIView):
    """
    API view for registering a new user.

    This view handles the HTTP POST request for user registration, utilizing the 
    UserRegistrationSerializer to validate and create the user.

    Attributes:
        permission_classes (tuple): Empty tuple to allow unrestricted access to this view.
        authentication_classes (tuple): Empty tuple as no authentication is required for registration.
    """

    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        """
        Handle POST requests for user registration.

        This method validates the incoming request data using the UserRegistrationSerializer. 
        If valid, it saves the new user and returns a success response. If invalid, it returns
        an error response.

        Args:
            request (Request): The HTTP request object containing user registration data.

        Returns:
            Response: A DRF Response object with a success or error message and corresponding status code.
        """
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({
                    'message': 'User registered successfully',
                    'status': 'success',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                'message': 'Invalid data',
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({
                'message': 'Validation error',
                'status': 'error',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'message': 'An unexpected error occurred',
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    """
    API view for user login.

    This view handles the HTTP POST request for user login, utilizing the UserLoginSerializer 
    to authenticate the user and return JWT tokens.

    Attributes:
        permission_classes (tuple): Empty tuple to allow unrestricted access to this view.
        authentication_classes (tuple): Empty tuple as no authentication is required for login.
    """

    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        """
        Handle POST requests for user login.

        This method validates the incoming request data using the UserLoginSerializer. 
        If valid, it authenticates the user and returns a success response with JWT tokens. 
        If invalid, it returns an error response.

        Args:
            request (Request): The HTTP request object containing user login data.

        Returns:
            Response: A DRF Response object with a success or error message, user data, 
            and corresponding status code.
        """
        try:
            serializer = UserLoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'message': 'User login successful',
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                'message': 'Validation error',
                'status': 'error',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'message': 'An unexpected error occurred',
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
