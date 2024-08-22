from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from .models import User
from rest_framework.exceptions import ValidationError


class RegisterUserView(APIView):
    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({'message': 'User registered successfully',
                                'status': 'success', 
                                'data': serializer.data}, 
                                status=status.HTTP_201_CREATED)
            return Response({'message': 'Invalid data',
                             'status': 'error',
                             'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'message': 'Validation error',
                             'status': 'error',
                             'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': 'An unexpected error occurred',
                             'status': 'error',
                             'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginUserView(APIView):
    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'User login successful',
                                'status': 'success'}, status=status.HTTP_200_OK)
            
            return Response({'message': 'Invalid data',
                             'status': 'error',
                             'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:

            return Response({'message': 'Validation error',
                             'status': 'error',
                             'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'message': 'An unexpected error occurred',
                             'status': 'error',
                             'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
