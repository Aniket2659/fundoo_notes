from .models import Log
from loguru import logger
from rest_framework.response import Response
from rest_framework  import status


class RequestLoggerMiddleware(object):
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self,request):
        
        method = request.method
        url = request.path
            
        log_entry = Log.objects.filter(method=method,url=url)
     
        if not log_entry.exists() :
            create = Log.objects.create(method=method,url=url)
        else: 
            log_entry=log_entry.first()   
            log_entry.count += 1
            log_entry.save()
        
        response = self.get_response(request)
        
        return response