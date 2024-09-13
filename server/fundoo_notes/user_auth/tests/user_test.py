import pytest
from user_auth.models import User
from rest_framework.reverse import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient

@pytest.mark.only
@pytest.mark.django_db
def test_user_registration(client):
    data = {
    "username":"aniket2659",
    "email":"aniket2659@gmail.com",
    "password":"aniket2659@A"}
    
    url = reverse('sign_in')
    response = client.post(url,
                           data,
                           content_type='application/json')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['message'] == 'User registered successfully'


@pytest.mark.django_db
def test_user_registration_missing_fields(client):
    data = {
    "username":"",
    "email":"aniket1234@gmail.com",
    "password":"aniket1234@A"}
    
    url = reverse('sign_in')
    response = client.post(url,
                           data,
                           content_type='application/json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_registration_invalid_email(client):
    data = {
    "username":"aniket1234",
    "email":"aniket1234.com",
    "password":"aniket1234@A"}
    
    url = reverse('sign_in')
    response = client.post(url,
                           data,
                           content_type='application/json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.data['errors']

@pytest.mark.django_db
def test_user_registration_invalid_password(client):
    data = {
    "username":"aniket1234",
    "email":"aniket1234@gmail.com",
    "password":"anike"}
    
    url = reverse('sign_in')
    response = client.post(url,
                           data,
                           content_type='application/json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'password' in response.data['errors']

@pytest.mark.django_db
def test_user_registration_missing_all_fields(client):
    # Missing all required fields
    data = {}  # No data provided

    url = reverse('sign_in')
    response = client.post(url,
                            data,
                            content_type='application/json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'username' in response.data['errors']
    assert 'email' in response.data['errors']
    assert 'password' in response.data['errors']

# Login pytest

@pytest.mark.django_db
def test_user_login(client):
    user = User.objects.create_user(email='aniket2659@gmail.com'
                                    , password='Aniket2659@',
                                    username='aniket2659')
    data = {"email":"aniket2659@gmail.com",
                "password":"Aniket2659@"}
    url = reverse('login')
    response = client.post(url,
                           data,
                           content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'User login successful'

@pytest.mark.django_db
def test_user_login_invalid_password(client):
    user = User.objects.create_user(email='aniket2659@gmail.com'
                                    , password='Aniket2659@',
                                    username='aniket2659')
    data = {"email":"aniket2659@gmail.com",
                "password":"Aniket265@"}
    url = reverse('login')
    response = client.post(url,
                           data,
                           content_type='application/json')
    print(response.data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == 'Validation error'

@pytest.mark.django_db
def test_user_login_invalid_email(client):
    user = User.objects.create_user(email='aniket2659@gmail.com'
                                    , password='Aniket2659@',
                                    username='aniket2659')
    data = {"email":"aniket265@gmail.com",
                "password":"Aniket2659@"}
    url = reverse('login')
    response = client.post(url,
                           data,
                           content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == 'Validation error'



@pytest.mark.django_db
def test_user_login_empty_fields(client):
    user = User.objects.create_user(email='aniket2659@gmail.com'
                                    , password='Aniket2659@',
                                    username='aniket2659')
    data = {"email":"aniket1234@gmail.com",
                "password":"Aniket1234@"}
    url = reverse('login')
    response = client.post(url,
                           data,
                           content_type='application/json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_login_dont_exist(client):
    data = {}
    url = reverse('login')
    response = client.post(url,
                           data,
                           content_type='application/json')
    print(response.data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.data['errors']
    assert 'password' in response.data['errors']

# verification 
@pytest.mark.django_db
def test_verify_registered_user_valid_token(client):
    # Create a test user
    user = User.objects.create_user(
        email='aniket2659@gmail.com',
        password='Aniket2659@',
        username='aniket2659'
    )
    token = RefreshToken.for_user(user).access_token
    encoded_token = str(token)
    url = reverse('verify', args=[encoded_token])
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'valid token'

@pytest.mark.django_db
def test_verify_registered_user_invalid_token(client):
    invalid_token = "invalid.token.value"
    url = reverse('verify', args=[invalid_token])
    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == 'Invalid token'
