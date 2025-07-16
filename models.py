# models.py

class RideParticipation:
    def __init__(self, participant, destination, occupiedSpaces):
        self.participant = participant  # objeto User
        self.destination = destination
        self.occupiedSpaces = occupiedSpaces
        self.status = "waiting"         # waiting, rejected, confirmed, missing, notmarked, inprogress, done
        self.confirmation = None        # fecha/hora o True/False o None

class Ride:
    def __init__(self, id, rideDateAndTime, finalAddress, allowedSpaces, rideDriver):
        self.id = id
        self.rideDateAndTime = rideDateAndTime
        self.finalAddress = finalAddress
        self.allowedSpaces = allowedSpaces
        self.rideDriver = rideDriver    # objeto User
        self.status = "ready"           # ready, inprogress, done
        self.participants = []          # lista de RideParticipation

    def remainingSpaces(self):
        return self.allowedSpaces - sum(
            p.occupiedSpaces for p in self.participants if p.status in ["waiting", "confirmed", "inprogress"]
        )

class User:
    def __init__(self, alias, name, carPlate=None):
        self.alias = alias
        self.name = name
        self.carPlate = carPlate
        self.rides = []  # lista de RideParticipation

        # estadísticas
        self.previousRidesTotal = 0
        self.previousRidesCompleted = 0
        self.previousRidesMissing = 0
        self.previousRidesNotMarked = 0
        self.previousRidesRejected = 0
