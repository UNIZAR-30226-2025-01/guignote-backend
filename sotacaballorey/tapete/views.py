from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Tapete
import json

@csrf_exempt  # Disable CSRF protection for simplicity (use it only for non-production)
def create_tapete(request):
    """
    Create a new Tapete with a specified name and file path.
    Expects a JSON body with 'name' and 'file_path'.
    """
    if request.method == "POST":
        try:
            # Parse the request body
            data = json.loads(request.body)
            name = data.get("name")
            file_path = data.get("file_path")

            # Validate the inputs
            if not name or not file_path:
                return JsonResponse({"error": "Name and file path are required."}, status=400)

            # Create the new Tapete object
            tapete = Tapete.objects.create(name=name, file_path=file_path)

            # Return success response
            return JsonResponse({
                "message": "Card mat created successfully",
                "tapete": {
                    "id": tapete.id,
                    "name": tapete.name,
                    "file_path": tapete.file_path
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt  # Disable CSRF protection for simplicity (use it only for non-production)
def get_all_tapetes(request):
    """
    Returns a list of all created card mats.
    """
    try:
        # Get all tapetes from the database
        tapetes = Tapete.objects.all()

        # Prepare the list of tapetes in the response format
        tapetes_list = [
            {"id": tapete.id, "name": tapete.name, "file_path": tapete.file_path}
            for tapete in tapetes
        ]

        # Return the list of tapetes as JSON
        return JsonResponse({"tapetes": tapetes_list}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_tapete_id_from_name(request):
    """
    Retrieves the ID of a Tapete based on its name.
    Expects a query parameter 'name' (the name of the Tapete).
    """
    name = request.GET.get('name')
    
    if not name:
        return JsonResponse({"error": "Name parameter is required"}, status=400)

    try:
        # Fetch the Tapete by name
        tapete = Tapete.objects.get(name=name)
        return JsonResponse({"id": tapete.id, "name": tapete.name}, status=200)
    
    except Tapete.DoesNotExist:
        return JsonResponse({"error": "Tapete not found"}, status=404) 