from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CardBack
import json

# View to create a new CardBack
@csrf_exempt  # Disable CSRF protection for simplicity (use it only for non-production)
def create_card_back(request):
    """
    Create a new CardBack with a specified name and file path.
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

            # Create the new CardBack object
            card_back = CardBack.objects.create(name=name, file_path=file_path)

            # Return success response
            return JsonResponse({
                "message": "Card back created successfully",
                "card_back": {
                    "id": card_back.id,
                    "name": card_back.name,
                    "file_path": card_back.file_path
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)


# View to get all created CardBacks
@csrf_exempt  # Disable CSRF protection for simplicity (use it only for non-production)
def get_all_card_backs(request):
    """
    Returns a list of all created card backs.
    """
    try:
        # Get all card backs from the database
        card_backs = CardBack.objects.all()

        # Prepare the list of card backs in the response format
        card_backs_list = [
            {"id": card_back.id, "name": card_back.name, "file_path": card_back.file_path}
            for card_back in card_backs
        ]

        # Return the list of card backs as JSON
        return JsonResponse({"card_backs": card_backs_list}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
# Get CardBack ID from Name
def get_card_back_id_from_name(request):
    """
    Retrieves the ID of a CardBack based on its name.
    Expects a query parameter 'name' (the name of the CardBack).
    """
    name = request.GET.get('name')
    
    if not name:
        return JsonResponse({"error": "Name parameter is required"}, status=400)

    try:
        # Fetch the CardBack by name
        card_back = CardBack.objects.get(name=name)
        return JsonResponse({"id": card_back.id, "name": card_back.name}, status=200)
    
    except CardBack.DoesNotExist:
        return JsonResponse({"error": "CardBack not found"}, status=404)
