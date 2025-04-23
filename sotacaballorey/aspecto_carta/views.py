from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CardSkin

@csrf_exempt  # Disable CSRF protection for simplicity (use it only for non-production)
def create_card_skin(request):
    """
    Create a new CardSkin with a specified name and file path.
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

            # Create the new CardSkin object
            card_skin = CardSkin.objects.create(name=name, file_path=file_path)

            # Return success response
            return JsonResponse({
                "message": "Card skin created successfully",
                "card_skin": {
                    "id": card_skin.id,
                    "name": card_skin.name,
                    "file_path": card_skin.file_path
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    # If the request method is not POST
    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt 
def get_all_card_skins(request):
    """
    Returns a list of all created card skins.
    """
    try:
        # Get all card skins from the database
        card_skins = CardSkin.objects.all()

        # Prepare the list of card skins in the response format
        card_skins_list = [
            {"id": card_skin.id, "name": card_skin.name, "file_path": card_skin.file_path}
            for card_skin in card_skins
        ]

        # Return the list of card skins as JSON
        return JsonResponse({"card_skins": card_skins_list}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_card_skin_id_from_name(request):
    """
    Retrieves the ID of a CardSkin based on its name.
    Expects a query parameter 'name' (the name of the CardSkin).
    """
    name = request.GET.get('name')
    
    if not name:
        return JsonResponse({"error": "Name parameter is required"}, status=400)

    try:
        # Fetch the CardSkin by name
        card_skin = CardSkin.objects.get(name=name)
        return JsonResponse({"id": card_skin.id, "name": card_skin.name}, status=200)
    
    except CardSkin.DoesNotExist:
        return JsonResponse({"error": "CardSkin not found"}, status=404)