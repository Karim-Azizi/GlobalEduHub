from django.shortcuts import render
from django.http import JsonResponse

# Custom 404 Error View
def custom_404_view(request, exception=None):
    if request.META.get('HTTP_ACCEPT', '').find('application/json') >= 0:
        return JsonResponse({'error': 'The resource was not found.'}, status=404)
    return render(request, 'errors/404.html', status=404)

# Custom 500 Error View
def custom_500_view(request):
    if request.META.get('HTTP_ACCEPT', '').find('application/json') >= 0:
        return JsonResponse({'error': 'An internal server error occurred.'}, status=500)
    return render(request, 'errors/500.html', status=500)