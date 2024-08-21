from django.shortcuts import render
import re
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST # restricts the view to accept only POST requests
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.forms import model_to_dict
from django.contrib.auth import authenticate

# Create your views here.

User = get_user_model()

@csrf_exempt # disables CSRF protection for the view.
@require_POST # only POST requests are allowed to access this view
def register_user(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        phone_number = data.get('phone_number')

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        pass_regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

        if not re.match(email_regex, email):
            return JsonResponse({"message": "Invalid email format","status":"error"}, status=400)
        if not re.match(pass_regex, password):
            return JsonResponse({"message": "Password must be at least 8 characters long,,ust contain 1 uppercase,1 digit and one special character","status":"error"}, status=400)
        user = User.objects.create_user(email=email,
                                         username=username, 
                                         password=password, 
                                         phone_number=phone_number)
        credentials=model_to_dict(user,exclude=['password'])
        return JsonResponse({"message": "User registered successfully","status":'succees',"data":credentials,}, status=201)


    except KeyError:
        return JsonResponse({"message": "Missing required fields","status":"error"}, status=400)


@csrf_exempt
@require_POST
def login_user(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        # Authenticate user
        user = authenticate(request, email=email, password=password)

        if user is not None:
            return JsonResponse({"message": "Login successful",'status':"success"}, status=200)
        
        return JsonResponse({"message": "Unexpected error occured","status": "error"}, status=400)

    except KeyError:
        return JsonResponse({"message": "Missing email or password","status":"error"}, status=400)
    


