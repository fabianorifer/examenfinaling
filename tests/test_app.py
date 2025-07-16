# tests/test_app.py

import unittest
from models import User, Ride, RideParticipation

class TestModels(unittest.TestCase):

    # ✅ Éxito: creación correcta de usuario
    def test_create_user(self):
        user = User(alias="jperez", name="Juan Perez", carPlate="ABC123")
        self.assertEqual(user.alias, "jperez")
        self.assertEqual(user.name, "Juan Perez")
        self.assertEqual(user.carPlate, "ABC123")

    #  Error 1: creación de Ride con espacios negativos
    def test_ride_with_negative_spaces(self):
        with self.assertRaises(ValueError):
            Ride(1, "2025-07-15 22:00", "UTEC", -3, User("a", "b"))

    #  Error 2: RideParticipation sin participante válido
    def test_ride_participation_without_user(self):
        with self.assertRaises(ValueError):
            RideParticipation(None, "Av. ABC", 1)

    #  Error 3: creación de usuario sin argumentos requeridos
    def test_create_user_without_alias(self):
        with self.assertRaises(TypeError):
            User()

    #  Cubre el método remainingSpaces para lograr 100%
    def test_remaining_spaces(self):
        user = User("driver1", "Conductor Uno")
        ride = Ride(1, "2025-07-15 22:00", "Destino X", 3, user)
        self.assertEqual(ride.remainingSpaces(), 3)

        #  Cubre el método remainingSpaces con participantes activos
    def test_remaining_spaces_with_participants(self):
        driver = User("conductor", "Pedro")
        ride = Ride(1, "2025-07-17 12:00", "UTEC", 4, driver)

        p1 = User("p1", "Ana")
        p2 = User("p2", "Luis")

        rp1 = RideParticipation(p1, "Destino 1", 1)
        rp2 = RideParticipation(p2, "Destino 2", 2)

        rp1.status = "confirmed"
        rp2.status = "waiting"

        ride.participants.extend([rp1, rp2])

        self.assertEqual(ride.remainingSpaces(), 1)  # 4 - (1 + 2)


if __name__ == "__main__":
    unittest.main()
