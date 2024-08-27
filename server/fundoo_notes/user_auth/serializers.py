from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import re


User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    This serializer handles the validation and creation of new users.
    
    Attributes:
        Meta (class): Contains metadata options for the serializer.
        model (User): The user model.
        fields (list): The fields that will be serialized and deserialized.
    """

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'phone_number', 'is_verified']
        extra_kwargs={"password": {"write_only": True}}

    def validate(self, attrs):
        """
        Validate the email and password fields.

        This method checks if the email has a valid format and if the password meets
        the required criteria (minimum 8 characters, at least 1 uppercase letter, 
        and 1 special character).

        Args:
            attrs (dict): A dictionary of attributes to validate.

        Raises:
            serializers.ValidationError: If the email or password does not meet the required criteria.

        Returns:
            dict: The validated attributes.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        password_regex = r"^(?=.*[A-Z])(?=.*[!@#$%^&*()_+{}\[\]:;\"'<>?,./~`-])(?=.*[a-zA-Z0-9]).{8,}$"

        try:
            if not re.match(email_regex, email):
                raise serializers.ValidationError({'email': 'Invalid email format.'})

            if not re.match(password_regex, password):
                raise serializers.ValidationError({
                    'password': 'Password must be at least 8 characters long and contain both letters and numbers, at least 1 uppercase letter, and 1 special character.'
                })

        except serializers.ValidationError as e:
            raise e
        except Exception as e:
            raise serializers.ValidationError({'error': f'An unexpected error occurred: {str(e)}'})

        return super().validate(attrs)

    def create(self, validated_data):
        """
        Create a new user.

        This method creates a new user using the validated data.

        Args:
            validated_data (dict): A dictionary of validated attributes.

        Returns:
            User: The created user instance.
        """
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number')
        )
        
        return user



class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    This serializer handles user authentication and token generation.
    
    Attributes:
        email (EmailField): The email field for user login.
        password (CharField): The password field for user login.
        access (CharField): The access token, generated upon successful login.
        refresh (CharField): The refresh token, generated upon successful login.
        data (DictField): The user data, returned upon successful login.
    """

    email = serializers.EmailField(required=True, write_only=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    data = serializers.DictField(read_only=True)

    def create(self, validated_data):
        """
        Authenticate the user and generate JWT tokens.

        This method authenticates the user with the provided email and password. If the 
        authentication is successful, it returns the user's data along with access and 
        refresh tokens.

        Args:
            validated_data (dict): A dictionary of validated attributes.

        Raises:
            serializers.ValidationError: If authentication fails.

        Returns:
            dict: A dictionary containing user data and JWT tokens.
        """
        email = validated_data.get('email')
        password = validated_data.get('password')

        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError('Invalid email or password')
        
        token = RefreshToken.for_user(user)
        return {
            'data': {
                'id': user.id,  
                'username': user.username,
                'email': user.email,
            },
            'access': str(token.access_token),
            'refresh': str(token)
        }
