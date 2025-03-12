from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from chat_global.models import ChatGlobal
from utils.jwt_auth import generar_token  # Import JWT generation function


class ChatGlobalTestCase(TestCase):
    
    def setUp(self):
        """Setup before each test - Create users and generate tokens."""
        self.usuario1 = Usuario.objects.create(nombre="Carlos", correo="carlos@example.com", contrasegna="1234")
        self.usuario2 = Usuario.objects.create(nombre="Elena", correo="elena@example.com", contrasegna="1234")
        self.usuario3 = Usuario.objects.create(nombre="David", correo="david@example.com", contrasegna="1234")
        self.usuario4 = Usuario.objects.create(nombre="Lucia", correo="lucia@example.com", contrasegna="1234")  # Third user for isolation test

        # Generate authentication tokens
        self.token_usuario1 = generar_token(self.usuario1)
        self.token_usuario2 = generar_token(self.usuario2)
        self.token_usuario3 = generar_token(self.usuario3)
        self.token_usuario4 = generar_token(self.usuario4)

    def test_chat_mensajes_en_orden(self):
        """Test that global chat messages are stored and retrieved in chronological order."""

        # 🔹 Send messages between Usuario1 and Usuario2
        mensajes_chat1 = [
            ("Hola, cómo estás?", self.token_usuario1, self.usuario2.id),
            ("Bien, gracias! Y tú?", self.token_usuario2, self.usuario1.id),
            ("Todo bien, listo para jugar?", self.token_usuario1, self.usuario2.id)
        ]

        for mensaje, headers, recipient_id in mensajes_chat1:
            response = self.client.post(
                reverse('chat_global:enviar_mensaje_global', args=[recipient_id, mensaje]),
                HTTP_AUTH=headers
            )
            self.assertEqual(response.status_code, 201)  # Ensure messages are sent successfully

        # 🔹 Send messages between Usuario2 and Usuario3
        mensajes_chat2 = [
            ("Hola David!", self.token_usuario2, self.usuario3.id),
            ("Qué tal, Elena?", self.token_usuario3, self.usuario2.id),
            ("Vamos a jugar después?", self.token_usuario2, self.usuario3.id)
        ]

        for mensaje, headers, recipient_id in mensajes_chat2:
            response = self.client.post(
                reverse('chat_global:enviar_mensaje_global', args=[recipient_id, mensaje]),
                HTTP_AUTH=headers
            )
            self.assertEqual(response.status_code, 201)

        # 🔹 Retrieve messages for Usuario1
        response_chat1 = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario2.id]),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response_chat1.status_code, 200)

        mensajes_recibidos_1 = response_chat1.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_1), 3)  # Ensure all 3 messages are retrieved

        # 🔹 Check chronological order for chat 1
        for i in range(len(mensajes_recibidos_1) - 1):
            self.assertLessEqual(mensajes_recibidos_1[i]["timestamp"], mensajes_recibidos_1[i + 1]["timestamp"])
            
                # 🔹 Retrieve messages exchanged between Usuario2 and Usuario3
        response_chat2_3 = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario3.id]),
            HTTP_AUTH=self.token_usuario2
        )

        self.assertEqual(response_chat2_3.status_code, 200)

        mensajes_recibidos_2_3 = response_chat2_3.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_2_3), 3)  # Should receive 3 messages exchanged between Usuario2 and Usuario3

        # 🔹 Check chronological order for messages between Usuario2 and Usuario3
        for i in range(len(mensajes_recibidos_2_3) - 1):
            self.assertLessEqual(mensajes_recibidos_2_3[i]["timestamp"], mensajes_recibidos_2_3[i + 1]["timestamp"])

        # 🔹 Ensure messages between Usuario1 and Usuario2 are NOT the same as those between Usuario2 and Usuario3
        self.assertNotEqual(mensajes_recibidos_1, mensajes_recibidos_2_3)

            
        

      

    def test_mensajes_recibidos_por_usuario1(self):
        """Test that messages sent to Usuario1 by Usuarios 2, 3, and 4 are retrieved correctly from separate requests."""

        # 🔹 Send messages from Usuario2 to Usuario1
        mensajes_chat_2_1 = [
            ("Hola Carlos!", self.token_usuario2, self.usuario1.id),
            ("Cómo va todo?", self.token_usuario2, self.usuario1.id),
            ("Nos vemos en el juego!", self.token_usuario2, self.usuario1.id)
        ]

        for mensaje, token, recipient_id in mensajes_chat_2_1:
            response = self.client.post(
                reverse('chat_global:enviar_mensaje_global', args=[recipient_id, mensaje]),
                HTTP_AUTH=token
            )
            self.assertEqual(response.status_code, 201)

        # 🔹 Send messages from Usuario3 to Usuario1
        mensajes_chat_3_1 = [
            ("Hola Carlos, listo para jugar?", self.token_usuario3, self.usuario1.id),
            ("Recuerda nuestra estrategia!", self.token_usuario3, self.usuario1.id),
            ("Nos vemos en el torneo!", self.token_usuario3, self.usuario1.id)
        ]

        for mensaje, token, recipient_id in mensajes_chat_3_1:
            response = self.client.post(
                reverse('chat_global:enviar_mensaje_global', args=[recipient_id, mensaje]),
                HTTP_AUTH=token
            )
            self.assertEqual(response.status_code, 201)

        # 🔹 Send messages from Usuario4 to Usuario1
        mensajes_chat_4_1 = [
            ("Carlos, tienes un minuto?", self.token_usuario4, self.usuario1.id),
            ("Necesito hablar sobre el equipo.", self.token_usuario4, self.usuario1.id),
            ("Llámame cuando puedas.", self.token_usuario4, self.usuario1.id)
        ]

        for mensaje, token, recipient_id in mensajes_chat_4_1:
            response = self.client.post(
                reverse('chat_global:enviar_mensaje_global', args=[recipient_id, mensaje]),
                HTTP_AUTH=token
            )
            self.assertEqual(response.status_code, 201)

        # 🔹 Retrieve messages **from Usuario2 to Usuario1**
        response_chat2_1 = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario2.id]),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response_chat2_1.status_code, 200)

        mensajes_recibidos_2_1 = response_chat2_1.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_2_1), 3, "Usuario2's messages to Usuario1 are missing or mixed.")

        # 🔹 Retrieve messages **from Usuario3 to Usuario1**
        response_chat3_1 = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario3.id]),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response_chat3_1.status_code, 200)

        mensajes_recibidos_3_1 = response_chat3_1.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_3_1), 3, "Usuario3's messages to Usuario1 are missing or mixed.")

        # 🔹 Retrieve messages **from Usuario4 to Usuario1**
        response_chat4_1 = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario4.id]),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response_chat4_1.status_code, 200)

        mensajes_recibidos_4_1 = response_chat4_1.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_4_1), 3, "Usuario4's messages to Usuario1 are missing or mixed.")

        # 🔹 Ensure messages total 9 (3 from each sender)
        total_mensajes = len(mensajes_recibidos_2_1) + len(mensajes_recibidos_3_1) + len(mensajes_recibidos_4_1)
        self.assertEqual(total_mensajes, 9, "Total messages count mismatch.")

        # 🔹 Ensure correct sender and recipient labels
        for msg in mensajes_recibidos_2_1:
            self.assertEqual(msg["emisor"], "Elena", "Incorrect sender for messages from Usuario2.")
            self.assertEqual(msg["receptor"], "Carlos", "Incorrect recipient for messages from Usuario2.")

        for msg in mensajes_recibidos_3_1:
            self.assertEqual(msg["emisor"], "David", "Incorrect sender for messages from Usuario3.")
            self.assertEqual(msg["receptor"], "Carlos", "Incorrect recipient for messages from Usuario3.")

        for msg in mensajes_recibidos_4_1:
            self.assertEqual(msg["emisor"], "Lucia", "Incorrect sender for messages from Usuario4.")
            self.assertEqual(msg["receptor"], "Carlos", "Incorrect recipient for messages from Usuario4.")

        # 🔹 Check chronological order for each sender
        for messages in [mensajes_recibidos_2_1, mensajes_recibidos_3_1, mensajes_recibidos_4_1]:
            for i in range(len(messages) - 1):
                self.assertLessEqual(messages[i]["timestamp"], messages[i + 1]["timestamp"])




    def test_mensaje_a_uno_mismo(self):

        mensaje_falso = "Mensaje reflexivo"

        response = self.client.post(
            reverse('chat_global:enviar_mensaje_global', args=[self.usuario3.id, mensaje_falso]),
            HTTP_AUTH=self.token_usuario3
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Cannot send a message to yourself")
        
