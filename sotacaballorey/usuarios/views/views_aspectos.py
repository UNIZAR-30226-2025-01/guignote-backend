from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from usuarios.models import Usuario
from aspecto_carta.models import CardSkin
from dorso_carta.models import CardBack
import json

# Unlock a skin for a player
@csrf_exempt
def unlock_skin(request, user_id):
    """
    Unlock a skin for the player.
    Expects a JSON body with 'skin_id' (ID of the CardSkin).
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            skin_id = data.get("skin_id")
            
            # Get the user and the skin
            user = Usuario.objects.get(id=user_id)
            skin = CardSkin.objects.get(id=skin_id)
            
            # Unlock the skin for the user
            user.unlocked_skins.add(skin)
            user.save()

            return JsonResponse({"message": "Skin unlocked successfully"}, status=200)

        except Usuario.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except CardSkin.DoesNotExist:
            return JsonResponse({"error": "Skin not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Unlock a back for a player
@csrf_exempt
def unlock_back(request, user_id):
    """
    Unlock a back for the player.
    Expects a JSON body with 'back_id' (ID of the CardBack).
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            back_id = data.get("back_id")
            
            # Get the user and the back
            user = Usuario.objects.get(id=user_id)
            back = CardBack.objects.get(id=back_id)
            
            # Unlock the back for the user
            user.unlocked_backs.add(back)
            user.save()

            return JsonResponse({"message": "Back unlocked successfully"}, status=200)

        except Usuario.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except CardBack.DoesNotExist:
            return JsonResponse({"error": "Back not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Retrieve the unlocked skins and backs for a player
def get_unlocked_items(request, user_id):
    """
    Retrieve all unlocked skins and backs for a player.
    """
    try:
        user = Usuario.objects.get(id=user_id)
        
        unlocked_skins = [{"id": skin.id, "name": skin.name, "file_path": skin.file_path} for skin in user.unlocked_skins.all()]
        unlocked_backs = [{"id": back.id, "name": back.name, "file_path": back.file_path} for back in user.unlocked_backs.all()]

        return JsonResponse({
            "unlocked_skins": unlocked_skins,
            "unlocked_backs": unlocked_backs
        }, status=200)

    except Usuario.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
