from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinLengthValidator
from django.contrib.auth import authenticate


User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):

    password=serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )

    username=serializers.CharField(required=True,validators=[MinLengthValidator(3)])

    class Meta:
        model = User
        fields = ['id','email', 'username', 'password', 'phone_number','is_verified']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number')
        )
        return user

    
class UserLoginSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)
    password=serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'})




    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')

        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError('Invalid email or password')
        
        return user

