import unittest
import json
from app import app, users, rides, ride_counter, User, Ride, RideParticipation

class TestRideSystem(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Limpiar datos entre pruebas
        global users, rides, ride_counter
        users.clear()
        rides.clear()
        ride_counter = 1
    
    def test_crear_usuario_exitoso(self):
        """
        Caso de prueba: Creación exitosa de usuario con auto
        Verifica que un usuario conductor se cree correctamente con todos sus atributos
        """
        # Arrange
        user_data = {
            "alias": "jperez",
            "name": "Juan Perez",
            "carPlate": "ABC-123"
        }
        
        # Act
        response = self.app.post('/usuarios', 
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        # Assert
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn("creado", response_data["message"])
        
        # Verificar que el usuario fue creado en la lista
        self.assertEqual(len(users), 1)
        usuario = users[0]
        self.assertEqual(usuario.alias, "jperez")
        self.assertEqual(usuario.name, "Juan Perez")
        self.assertEqual(usuario.carPlate, "ABC-123")
        self.assertEqual(usuario.previousRidesTotal, 0)
        self.assertEqual(usuario.previousRidesCompleted, 0)
    
    def test_crear_ride_usuario_inexistente_error(self):
        """
        Caso de prueba: Error al crear ride con usuario inexistente
        Verifica que se retorne error 404 cuando el conductor no existe
        """
        # Arrange
        ride_data = {
            "rideDateAndTime": "2025/07/15 22:00",
            "finalAddress": "Av Javier Prado 456, San Borja",
            "allowedSpaces": 3
        }
        
        # Act
        response = self.app.post('/usuarios/usuarioInexistente/rides',
                               data=json.dumps(ride_data),
                               content_type='application/json')
        
        # Assert
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertIn("Conductor no encontrado", response_data["message"])
    
    def test_unirse_ride_ya_solicitado_error(self):
        """
        Caso de prueba: Error al intentar unirse dos veces al mismo ride
        Verifica validación de duplicidad de solicitudes del mismo participante
        """
        # Arrange - Crear conductor y ride
        driver_data = {
            "alias": "jperez",
            "name": "Juan Perez",
            "carPlate": "ABC-123"
        }
        self.app.post('/usuarios', 
                     data=json.dumps(driver_data),
                     content_type='application/json')
        
        ride_data = {
            "rideDateAndTime": "2025/07/15 22:00",
            "finalAddress": "Av Javier Prado 456, San Borja",
            "allowedSpaces": 3
        }
        response = self.app.post('/usuarios/jperez/rides',
                               data=json.dumps(ride_data),
                               content_type='application/json')
        
        # Crear participante
        participant_data = {
            "alias": "lgomez",
            "name": "Luis Gomez"
        }
        self.app.post('/usuarios', 
                     data=json.dumps(participant_data),
                     content_type='application/json')
        
        # Primera solicitud exitosa
        join_data = {
            "destination": "Av Aramburú 245, Surquillo",
            "occupiedSpaces": 1
        }
        self.app.post('/usuarios/jperez/rides/1/requestToJoin/lgomez',
                     data=json.dumps(join_data),
                     content_type='application/json')
        
        # Act - Segunda solicitud (duplicada)
        response = self.app.post('/usuarios/jperez/rides/1/requestToJoin/lgomez',
                               data=json.dumps(join_data),
                               content_type='application/json')
        
        # Assert
        self.assertEqual(response.status_code, 422)
        response_data = json.loads(response.data)
        self.assertIn("Ya solicitaste unirte", response_data["message"])
    
    def test_aceptar_participante_sin_espacios_error(self):
        """
        Caso de prueba: Error al aceptar participante cuando no hay espacios disponibles
        Verifica validación de espacios disponibles al aceptar participantes
        """
        # Arrange - Crear conductor y ride con solo 1 espacio
        driver_data = {
            "alias": "jperez",
            "name": "Juan Perez",
            "carPlate": "ABC-123"
        }
        self.app.post('/usuarios', 
                     data=json.dumps(driver_data),
                     content_type='application/json')
        
        ride_data = {
            "rideDateAndTime": "2025/07/15 22:00",
            "finalAddress": "Av Javier Prado 456, San Borja",
            "allowedSpaces": 1
        }
        self.app.post('/usuarios/jperez/rides',
                     data=json.dumps(ride_data),
                     content_type='application/json')
        
        # Crear dos participantes
        for i, alias in enumerate(["lgomez", "mrodriguez"]):
            user_data = {
                "alias": alias,
                "name": f"Usuario {i+1}"
            }
            self.app.post('/usuarios', 
                         data=json.dumps(user_data),
                         content_type='application/json')
            
            # Ambos solicitan unirse
            join_data = {
                "destination": f"Destino {i+1}",
                "occupiedSpaces": 1
            }
            self.app.post(f'/usuarios/jperez/rides/1/requestToJoin/{alias}',
                         data=json.dumps(join_data),
                         content_type='application/json')
        
        # Aceptar primer participante (ocupa el único espacio)
        self.app.post('/usuarios/jperez/rides/1/accept/lgomez')
        
        # Act - Intentar aceptar segundo participante (no hay espacios)
        response = self.app.post('/usuarios/jperez/rides/1/accept/mrodriguez')
        
        # Assert
        self.assertEqual(response.status_code, 422)
        response_data = json.loads(response.data)
        self.assertIn("No hay espacios suficientes", response_data["message"])

if __name__ == '__main__':
    unittest.main()