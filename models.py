# models.py

class RideParticipation:
    def __init__(self, participant, destination, occupiedSpaces):
        if participant is None:
            raise ValueError("Participant no puede ser None.")
        self.participant = participant  
        self.destination = destination
        self.occupiedSpaces = occupiedSpaces
        self.status = "waiting"   
        self.confirmation = None      

class Ride:
    def __init__(self, id, rideDateAndTime, finalAddress, allowedSpaces, rideDriver):
        if allowedSpaces < 0:
            raise ValueError("allowedSpaces no puede ser negativo.")
        self.id = id
        self.rideDateAndTime = rideDateAndTime
        self.finalAddress = finalAddress
        self.allowedSpaces = allowedSpaces
        self.rideDriver = rideDriver  
        self.status = "ready"           
        self.participants = []          

    def remainingSpaces(self):
        return self.allowedSpaces - sum(
            p.occupiedSpaces for p in self.participants if p.status in ["waiting", "confirmed", "inprogress"]
        )

class User:
    def __init__(self, alias, name, carPlate=None):
        self.alias = alias
        self.name = name
        self.carPlate = carPlate
        self.rides = []  

        self.previousRidesTotal = 0
        self.previousRidesCompleted = 0
        self.previousRidesMissing = 0
        self.previousRidesNotMarked = 0
        self.previousRidesRejected = 0
