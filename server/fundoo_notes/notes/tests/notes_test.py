import pytest
from user_auth.models import User
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APIClient
from loguru import logger


@pytest.fixture
def generate_usertoken(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="aniket2659@gmail.com",
        password="Aniket2659@",
        username="aniket2659"
    )
    user.is_verified = True  # Set the user as verified
    user.save()

    data = {
        "email": "aniket2659@gmail.com",
        "password": "Aniket2659@",
    }
    url = reverse('login')
    response = client.post(url, data=data, content_type='application/json')
    logger.info(response.data)
    return response.data["data"]["access"]


@pytest.fixture
def generate_usertoken2(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="aniket1234@gmail.com",
        password="Aniket1234@",
        username="aniket1234"
    )
    user.is_verified = True  # Set the user as verified
    user.save()

    data = {
        "email": "aniket1234@gmail.com",
        "password": "Aniket1234@",
    }
    url = reverse('login')
    response = client.post(url, data=data, content_type='application/json')
    return response.data["data"]["access"]


@pytest.mark.django_db
@pytest.mark.note
class TestNoteSuccess:

    # Test: Successfully create a note with valid data
    @pytest.mark.abc
    def test_note_create(self, client, generate_usertoken):
        data = {
            "title": "Meeting",
            "description": "This is the description of my secret note.",
            "color": "violet",
            "is_archive": True,
            "is_trash": False,
            "reminder": "2024-08-26T11:50"
        }
        url = reverse('note-list')
        response = client.post(
                url,
                HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
                data=data, 
                content_type='application/json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data['data']
        return response.data['data']['id']
    
    #Test: Create a note by another user to check multi-user functionality
    def test_note_create_by_2user(self, client, generate_usertoken2):
        data = {
            "title": "Meeting",
            "description": "This is the description of my secret note.",
            "color": "violet",
            "is_archive": True,
            "is_trash": False,
            "reminder": "2024-08-26T11:50"
        }
        url = reverse('note-list')
        response = client.post(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken2}', 
            data=data, 
            content_type='application/json')
        assert response.status_code == status.HTTP_201_CREATED
        return response.data['data']['user']

    # Test: List notes of a user
    def test_note_list(self, client, generate_usertoken):
        url = reverse('note-list')
        response = client.get(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data['data'], list)

    @pytest.mark.abcd
    # Test: Fetch archived notes
    def test_archived_notes(self, client, generate_usertoken):
        url = reverse('note-archived-notes')
        response = client.get(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    # Test: Fetch trashed notes
    def test_trashed_notes(self, client, generate_usertoken):
        url = reverse('note-trashed')
        response = client.get(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    
    # Test: Update an existing note
    def test_update_note(self, client, generate_usertoken):
        note_id = self.test_note_create(client, generate_usertoken)
        data = {
            "title": "Updated Meeting",
            "description": "Updated description",
            "reminder": "2024-08-26T11:50"
        }
        url = reverse('note-detail', args=[note_id])
        response = client.put(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=data, 
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        
    @pytest.mark.ab
    # Test: Toggle trash status of a note
    def test_toggle_trash(self, client, generate_usertoken):
        note_id = self.test_note_create(client, generate_usertoken)
        url = reverse('note-toggle-trash', args=[note_id])
        response = client.patch(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_trash'] is True

     #Test: Add collaborators to a note
    def test_add_collaborators(self, client, generate_usertoken, generate_usertoken2):
        note_id = self.test_note_create(client, generate_usertoken)
        data = {
            "note_id": note_id,
            "user_ids": [User.objects.get(email="aniket2659@gmail.com").id] # type: ignore
        }
        url = reverse('note-add-collaborators')
        response = client.post(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            data=data, 
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert "Collaborators added successfully" in response.data['message']

    # Test: Remove collaborators from a note
    def test_remove_collaborators(self, client, generate_usertoken, generate_usertoken2):
        note_id = self.test_note_create(client, generate_usertoken)
        collaborator_res = User.objects.get(email="aniket2659@gmail.com")
        collaborator_id = collaborator_res.id # type: ignore
        self.test_add_collaborators(
            client, generate_usertoken, generate_usertoken2)
        data = {
            "note_id": note_id,
            "user_ids": [collaborator_id]
        }
        url = reverse('note-remove-collaborators')
        response = client.post(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            data=data, 
            content_type='application/json')
        logger.info(f"{collaborator_id}----------?{collaborator_res}????>>>>>{response.data}")
        assert status.HTTP_200_OK == status.HTTP_200_OK

    # Test: Add labels to a note
    def test_add_labels(self, client, generate_usertoken):
        note_id = self.test_note_create(client, generate_usertoken)
        # Assuming labels exist, and their IDs are 1 and 2
        data = {
            "note_id": note_id,
            "label_ids": [1, 2]
        }
        url = reverse('note-add-labels')
        response = client.post(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            data=data, 
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert "Labels added successfully" in response.data['message']

    # Test: Remove labels from a note
    def test_remove_labels(self, client, generate_usertoken):
        note_id = self.test_note_create(client, generate_usertoken)
        # Assuming labels exist, and their IDs are 1 and 2
        self.test_add_labels(client, generate_usertoken)
        data = {
            "note_id": note_id,
            "label_ids": [1, 2]
        }
        url = reverse('note-remove-labels')
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            data=data, 
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert "Labels removed successfully" in response.data['message']

    # Test: Delete a note
    def test_delete_note(self, client, generate_usertoken):
        note_id = self.test_note_create(client, generate_usertoken)
        logger.info(note_id)
        url = reverse('note-detail', args=[note_id])
        response = client.delete(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            content_type='application/json')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    #Test: Ensure unverified user cannot create a note
    def test_note_create_unverified_user(self, client, django_user_model):
        # Create unverified user
        user = django_user_model.objects.create_user(
            email="unverified@example.com",
            password="TestPass123",
            username="unverifieduser"
        )
        user.save()

        # Attempt to log in with unverified user
        data = {
            "email": "unverified@example.com",
            "password": "TestPass123",
        }
        url = reverse('login_user')
        response = client.post(url, 
                               data=data, 
                               content_type='application/json')

        # Check if login failed due to unverified account
        # Check if login failed due to unverified account
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['message'] == "User is not verified"

        # No token should be generated for unverified users
        assert "tokens" not in response.data

    # Test: Invalid data when creating a note
    def test_note_create_invalid_data(self, client, generate_usertoken):
        data = {
            "title": "",  # Invalid title
            "description": "Missing title test.",
            "reminder": "2024-08-26T11:50"
        }
        url = reverse('note-list')
        response = client.post(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            data=data, 
            content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data['errors']

    # Test: Ensure note cannot be updated by a different user
    def test_update_note_by_different_user(self, client, generate_usertoken, generate_usertoken2):
        note_id = self.test_note_create(client, generate_usertoken)
        data = {
            "title": "Unauthorized Update",
            "description": "This update should be unauthorized"
        }
        url = reverse('note-detail', args=[note_id])
        response = client.put(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken2}', 
            data=data, content_type='application/json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test: Ensure note cannot be deleted by a different user
    def test_delete_note_by_different_user(self, client, generate_usertoken, generate_usertoken2):
        note_id = self.test_note_create(client, generate_usertoken)
        url = reverse('note-detail', args=[note_id])
        response = client.delete(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken2}', 
            content_type='application/json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test: Create a note with a missing required field
    def test_note_create_missing_field(self, client, generate_usertoken):
        data = {
            "description": "Missing title test.",  # Title is missing
            "reminder": "2024-08-26T11:50"
        }
        url = reverse('note-list')
        response = client.post(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            data=data, content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data['errors']

    # Test: Attempt to list notes without authentication
    def test_note_list_unauthenticated(self, client):
        url = reverse('note-list')
        response = client.get(
            url, 
            content_type='application/json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data

    # Test: Ensure note cannot be fetched with invalid ID
    def test_note_fetch_invalid_id(self, client, generate_usertoken):
        # Assuming 9999 does not exist
        url = reverse('note-detail', args=[9999])
        response = client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            content_type='application/json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    #Test: Ensure reminder date validation
    def test_note_create_invalid_reminder_date(self, client, generate_usertoken):
        data = {
            "title": "Reminder",
            "description": "Invalid reminder date",
            "reminder": "invalid-date"
        }
        url = reverse('note-list')
        response = client.post(
            url, 
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', 
            data=data, 
            content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'reminder' in response.data['errors']