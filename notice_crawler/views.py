
from django.http import JsonResponse
from .models import Notice

def insert_notice(request):
    if request.method == 'POST':
        data = request.POST
        notice = Notice(
            title=data.get('title'),
            content=data.get('content'),
            original_link=data.get('original_link')
        )
        notice.save()
        return JsonResponse({'status': 'success', 'message': 'Notice added successfully'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
