from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from usuarios.models import Usuario
from aspecto_carta.models import CardSkin
from dorso_carta.models import CardBack
from tapete.models import Tapete
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


# Unlock a tapete for a player
@csrf_exempt
def unlock_tapete(request, user_id):
    """
    Unlock a tapete for the player.
    Expects a JSON body with 'tapete_id' (ID of the Tapete).
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            tapete_id = data.get("tapete_id")
            
            # Get the user and the tapete
            user = Usuario.objects.get(id=user_id)
            tapete = Tapete.objects.get(id=tapete_id)
            
            # Unlock the tapete for the user
            user.unlocked_tapetes.add(tapete)
            user.save()

            return JsonResponse({"message": "Card mat unlocked successfully"}, status=200)

        except Usuario.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Tapete.DoesNotExist:
            return JsonResponse({"error": "Card mat not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Equip a skin for a player
@csrf_exempt
def equip_skin(request, user_id):
    """
    Equip a skin for the player.
    Expects a JSON body with 'skin_id' (ID of the CardSkin).
    Checks if the user owns the skin before equipping.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            skin_id = data.get("skin_id")
            
            # Get the user and the skin
            user = Usuario.objects.get(id=user_id)
            skin = CardSkin.objects.get(id=skin_id)
            
            # Check if user owns the skin
            if skin not in user.unlocked_skins.all():
                return JsonResponse({"error": "User does not own this skin"}, status=403)
            
            # Equip the skin
            user.equipped_skin = skin
            user.save()

            return JsonResponse({
                "message": "Skin equipped successfully",
                "equipped_skin": {
                    "id": skin.id,
                    "name": skin.name,
                    "file_path": skin.file_path
                }
            }, status=200)

        except Usuario.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except CardSkin.DoesNotExist:
            return JsonResponse({"error": "Skin not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Equip a back for a player
@csrf_exempt
def equip_back(request, user_id):
    """
    Equip a back for the player.
    Expects a JSON body with 'back_id' (ID of the CardBack).
    Checks if the user owns the back before equipping.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            back_id = data.get("back_id")
            
            # Get the user and the back
            user = Usuario.objects.get(id=user_id)
            back = CardBack.objects.get(id=back_id)
            
            # Check if user owns the back
            if back not in user.unlocked_backs.all():
                return JsonResponse({"error": "User does not own this back"}, status=403)
            
            # Equip the back
            user.equipped_back = back
            user.save()

            return JsonResponse({
                "message": "Back equipped successfully",
                "equipped_back": {
                    "id": back.id,
                    "name": back.name,
                    "file_path": back.file_path
                }
            }, status=200)

        except Usuario.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except CardBack.DoesNotExist:
            return JsonResponse({"error": "Back not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Equip a tapete for a player
@csrf_exempt
def equip_tapete(request, user_id):
    """
    Equip a tapete for the player.
    Expects a JSON body with 'tapete_id' (ID of the Tapete).
    Checks if the user owns the tapete before equipping.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            tapete_id = data.get("tapete_id")
            
            # Get the user and the tapete
            user = Usuario.objects.get(id=user_id)
            tapete = Tapete.objects.get(id=tapete_id)
            
            # Check if user owns the tapete
            if tapete not in user.unlocked_tapetes.all():
                return JsonResponse({"error": "User does not own this card mat"}, status=403)
            
            # Equip the tapete
            user.equipped_tapete = tapete
            user.save()

            return JsonResponse({
                "message": "Card mat equipped successfully",
                "equipped_tapete": {
                    "id": tapete.id,
                    "name": tapete.name,
                    "file_path": tapete.file_path
                }
            }, status=200)

        except Usuario.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Tapete.DoesNotExist:
            return JsonResponse({"error": "Card mat not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Retrieve the unlocked skins, backs and tapetes for a player
def get_unlocked_items(request, user_id):
    """
    Retrieve all unlocked skins, backs and tapetes for a player.
    """
    try:
        user = Usuario.objects.get(id=user_id)
        
        unlocked_skins = [{"id": skin.id, "name": skin.name, "file_path": skin.file_path} for skin in user.unlocked_skins.all()]
        unlocked_backs = [{"id": back.id, "name": back.name, "file_path": back.file_path} for back in user.unlocked_backs.all()]
        unlocked_tapetes = [{"id": tapete.id, "name": tapete.name, "file_path": tapete.file_path} for tapete in user.unlocked_tapetes.all()]

        return JsonResponse({
            "unlocked_skins": unlocked_skins,
            "unlocked_backs": unlocked_backs,
            "unlocked_tapetes": unlocked_tapetes
        }, status=200)

    except Usuario.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
# Retrieve the unlocked skins, backs and tapetes for a player
def get_equipped_items(request, user_id):
    """
    Retrieve all unlocked skins, backs and tapetes for a player.
    """
    try:
        user = Usuario.objects.get(id=user_id)

        # Get equipped items
        equipped_skin = None
        if user.equipped_skin:
            equipped_skin = {
                "id": user.equipped_skin.id,
                "name": user.equipped_skin.name,
                "file_path": user.equipped_skin.file_path
            }
        
        equipped_back = None
        if user.equipped_back:
            equipped_back = {
                "id": user.equipped_back.id,
                "name": user.equipped_back.name,
                "file_path": user.equipped_back.file_path
            }
        
        equipped_tapete = None
        if user.equipped_tapete:
            equipped_tapete = {
                "id": user.equipped_tapete.id,
                "name": user.equipped_tapete.name,
                "file_path": user.equipped_tapete.file_path
            }

        return JsonResponse({
            "equipped_skin": equipped_skin,
            "equipped_back": equipped_back,
            "equipped_tapete": equipped_tapete
        }, status=200)

    except Usuario.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)