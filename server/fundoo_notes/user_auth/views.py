from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.reverse import reverse
from .models import User
import jwt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .tasks import send_verification_email
from django.utils.html import format_html
from drf_yasg.utils import swagger_auto_schema


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
    @swagger_auto_schema(operation_description="register user", request_body=UserRegistrationSerializer, responses={200: UserRegistrationSerializer})
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
                # generate a token
                token = RefreshToken.for_user(user)
                access_token = str(token.access_token)
                verification_link = request.build_absolute_uri(reverse('verify', args=[access_token]))
                # send verification link asynchronously
                send_verification_email.delay(user.email,verification_link)

                return Response({
                    'message': 'User registered successfully',
                    'status': 'success',
                    'data':serializer.data
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
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    @swagger_auto_schema(operation_description="user login", request_body=UserLoginSerializer, responses={201: UserLoginSerializer, 400: "Bad Request: Invalid input data.",
                                                                                                         500: "Internal Server Error: An error occurred during Login."})
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
        
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_registered_user(request, token):
    """
    Verify the registered user using the token.

    This view takes a JWT token as a path parameter, decodes it using the secret key, 
    and returns the decoded token in the response.

    Args:
        request (Request): The HTTP request object.
        token (str): The JWT token passed as a path parameter.

    Returns:
        Response: A DRF Response object with the decoded token or an error message.
    """
    try:
        # Decode the token
        payload=jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"])
        user = User.objects.get(id=payload['user_id'])
        user.is_verified = True
        user.save()

        
        return Response({
            'message':'valid token',
            'status': 'success'
        }, status=status.HTTP_200_OK)
    except jwt.ExpiredSignatureError:
        return Response({
            'message': 'Token has expired',
            'status': 'error'
        }, status=status.HTTP_400_BAD_REQUEST)
    except jwt.InvalidTokenError:
        return Response({
            'message': 'Invalid token',
            'status': 'error'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'message': 'An unexpected error occurred',
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

