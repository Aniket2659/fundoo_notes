import pytest
from user_auth.models import User
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import Label

@pytest.fixture
def user_token_1(client, django_user_model):
    """
    Fixture to create a verified user and return an access token for the user.
    """
    user = django_user_model.objects.create_user(
        email="aniketbabar2002@gmail.com",
        password="Aniket@2002",
        username="aniket2002"
    )
    user.is_verified = True
    user.save()

    data = {
        "email": "aniketbabar2002@gmail.com",
        "password": "Aniket@2002",
    }
    url = reverse('login')
    response = client.post(url, data=data, content_type='application/json')
    return response.data["data"]["access"]


@pytest.fixture
def user_token_2(client, django_user_model):
    """
    Fixture to create another verified user and return an access token for this user.
    """
    user = django_user_model.objects.create_user(
        email="aniketbabar2001@gmail.com",
        password="Aniket@2001",
        username="aniket2001"
    )
    user.is_verified = True
    user.save()

    data = {
        "email": "aniketbabar2001@gmail.com",
        "password": "Aniket@2001",
    }
    url = reverse('login')
    response = client.post(url, data=data, content_type='application/json')
    return response.data["data"]["access"]


@pytest.mark.django_db
@pytest.mark.labels_success
class TestLabelAPI:
    """
    A test suite for testing the Label API endpoints.
    """

    @pytest.fixture
    def create_label_fixture(self, client, user_token_1):
        """
        Fixture to create a label for testing.
        """
        url = reverse('label-list')
        data = {
            'name': 'aniket',
            'color': 'brown'
        }
        response = client.post(
            url,
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        return response.data
    
    def test_create_label(self, client, user_token_1):
        """
        Test case to create a label successfully.
        """
        url = reverse('label-list')
        data = {
            'name': 'sky',
            'color': 'blue'
        }
        response = client.post(
            url,
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == 'sky'
        assert response.data['data']['color'] == 'blue'

    def test_create_label_with_invalid_data(self, client, user_token_1):
        """
        Test case to create a label with invalid input data.
        """
        url = reverse('label-list')
        data = {
            'name': '',  
            'color': 'yellow'
        }
        response = client.post(
            url,
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


    def test_create_label_without_auth(self, client):
        """
        Test case to create a label without authentication token.
        """
        url = reverse('label-list')
        data = {
            'name': 'sky',  
            'color': 'blue'
        }
        response = client.post(
            url,
            data=data,
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Authentication credentials were not provided.' in response.data['detail']


    def test_get_specific_label(self, client, user_token_1, create_label_fixture):
        """
        Test case to retrieve a specific label by ID.
        """
        label_id = create_label_fixture['data']['id']
        url = reverse('label-detail', args=[label_id])
        response = client.get(
            url,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['id'] == label_id

    def test_get_non_existent_label(self, client, user_token_1):
        """
        Test case to retrieve a non-existent label.
        """
        url = reverse('label-detail', args=[999])  # Assuming 999 is a non-existent ID
        response = client.get(
            url,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND  # Expecting 404 Not Found
        assert 'errors' in response.data  # Check for the presence of a detail message


    def test_list_all_labels(self, client, user_token_1):
        """
        Test case to list all labels for a user.
        """
        # Create some labels first to ensure they are available for this test
        url = reverse('label-list')
        data = [
            {'name': 'label1', 'color': 'red'},
            {'name': 'label2', 'color': 'blue'}
        ]
        for label_data in data:
            client.post(
                url,
                data=label_data,
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
            )
        
        # Test listing labels
        response = client.get(
            url,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) > 0  # Ensure at least one label is returned


    def test_list_all_labels_no_labels(self, client, user_token_1):
        """
        Test case to handle the scenario where no labels are found for a user.
        """
        url = reverse('label-list')
        
        # Ensure no labels are created for the user
        response = client.get(
            url,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert response.data['data'] == []  # Expecting an empty list


    def test_update_label(self, client, user_token_1, create_label_fixture):
        """
        Test case to update a label successfully.
        """
        label_id = create_label_fixture['data']['id']
        url = reverse('label-detail', args=[label_id])
        updated_data = {
            'name': 'parrot',
            'color': 'green'
        }
        response = client.put(
            url,
            data=updated_data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'parrot'
        assert response.data['data']['color'] == 'green'


    def test_update_label_with_invalid_data(self, client, create_label_fixture, user_token_1):
        """
        Test case to update a label with invalid input data.
        """
        label_id = create_label_fixture['data']['id']
        url = reverse('label-detail', args=[label_id])
        updated_data = {
            'name': '',  # Invalid: empty name
            'color': 'green'
        }
        response = client.put(
            url,
            data=updated_data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data['errors']  # Check for error related to the 'name' field


    def test_update_label_by_unauthorized_user(self, client, create_label_fixture, user_token_2):
        """
        Test case to attempt updating a label that belongs to another user.
        """
        label_id = create_label_fixture['data']['id']
        url = reverse('label-detail', args=[label_id])
        updated_data = {
            'name': 'parrot',
            'color': 'green'
        }
        response = client.put(
            url,
            data=updated_data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_2}'  # Using a different user's token
        )
        assert status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == 'error'


    def test_update_non_existent_label(self, client, user_token_1):
        """
        Test case to attempt updating a label that does not exist.
        """
        non_existent_label_id = 9999  # Assuming this ID does not exist
        url = reverse('label-detail', args=[non_existent_label_id])
        updated_data = {
            'name': 'parrot',
            'color': 'green'
        }
        response = client.put(
            url,
            data=updated_data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] == 'error'
        assert response.data['message'] == 'Label not found'



    def test_delete_label(self, client, user_token_1, create_label_fixture):
        """
        Test case to delete a label successfully.
        """
        label_id = create_label_fixture['data']['id']
        url = reverse('label-detail', args=[label_id])
        response = client.delete(
            url,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Label.objects.filter(id=label_id).exists()

    def test_delete_non_existent_label(self, client, user_token_1):
        """
        Test case to attempt deleting a label that does not exist.
        """
        url = reverse('label-detail', args=[99999])  # Using a non-existent label ID
        response = client.delete(
            url,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_1}'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] == 'error'
        assert response.data['message'] == 'Label not found'


    def test_access_other_user_label(self, client, user_token_2, create_label_fixture):
        """
        Test case to ensure unauthorized access to another user's label is not allowed.
        """
        label_id = create_label_fixture['data']['id']
        url = reverse('label-detail', args=[label_id])
        response = client.get(
            url,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {user_token_2}'  # Using a different user's token
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] == 'error'





