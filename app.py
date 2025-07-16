# app.py
from flask import Flask, jsonify, request, abort
from datetime import datetime
from models import User, Ride, RideParticipation


app = Flask(__name__)


class RideParticipation:
    def __init__(self, participant, destination, occupiedSpaces):
        self.participant = participant  
        self.destination = destination
        self.occupiedSpaces = occupiedSpaces
        self.status = "waiting" 
        self.confirmation = None

class Ride:
    def __init__(self, id, rideDateAndTime, finalAddress, allowedSpaces, rideDriver):
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

# ------------------------
# DATA HANDLER
# ------------------------
users = []
rides = []
ride_counter = 1

def find_user(alias):
    return next((u for u in users if u.alias == alias), None)

def find_ride(driver_alias, ride_id):
    ride = next((r for r in rides if r.rideDriver.alias == driver_alias and r.id == ride_id), None)
    if not ride:
        abort(404, description=f"Ride {ride_id} no encontrado para {driver_alias}")
    return ride

# ------------------------
# ENDPOINTS
# ------------------------

# USUARIOS
@app.route("/usuarios", methods=["GET"])
def list_users():
    return jsonify([{
        "alias": u.alias, "name": u.name, "carPlate": u.carPlate
    } for u in users])

@app.route("/usuarios", methods=["POST"])
def create_user():
    data = request.get_json()
    alias = data.get("alias")
    name = data.get("name")
    carPlate = data.get("carPlate")
    if not alias or not name:
        abort(422, description="Faltan alias o name.")
    if any(u.alias == alias for u in users):
        abort(422, description="Alias ya existe.")
    user = User(alias, name, carPlate)
    users.append(user)
    return jsonify({"message": f"Usuario {alias} creado."}), 201

@app.route("/usuarios/<alias>", methods=["GET"])
def get_user(alias):
    user = find_user(alias)
    if not user:
        abort(404, description="Usuario no encontrado.")
    return jsonify({
        "alias": user.alias,
        "name": user.name,
        "carPlate": user.carPlate,
        "previousRidesTotal": user.previousRidesTotal,
        "previousRidesCompleted": user.previousRidesCompleted,
        "previousRidesMissing": user.previousRidesMissing,
        "previousRidesNotMarked": user.previousRidesNotMarked,
        "previousRidesRejected": user.previousRidesRejected
    })

# RIDES
@app.route("/usuarios/<alias>/rides", methods=["POST"])
def create_ride(alias):
    global ride_counter
    driver = find_user(alias)
    if not driver:
        abort(404, description="Conductor no encontrado.")
    data = request.get_json()
    finalAddress = data.get("finalAddress")
    rideDateAndTime = data.get("rideDateAndTime")
    allowedSpaces = data.get("allowedSpaces")
    if not all([finalAddress, rideDateAndTime, allowedSpaces]):
        abort(422, description="Faltan datos para ride.")
    ride = Ride(ride_counter, rideDateAndTime, finalAddress, allowedSpaces, driver)
    rides.append(ride)
    ride_counter += 1
    return jsonify({"message": f"Ride creado con id {ride.id}"}), 201

@app.route("/usuarios/<alias>/rides", methods=["GET"])
def get_user_rides(alias):
    user = find_user(alias)
    if not user:
        abort(404, description="Usuario no encontrado.")
    user_rides = [r for r in rides if r.rideDriver.alias == alias]
    return jsonify([{
        "id": r.id, "rideDateAndTime": r.rideDateAndTime,
        "finalAddress": r.finalAddress, "status": r.status
    } for r in user_rides])

@app.route("/usuarios/<alias>/rides/<int:ride_id>", methods=["GET"])
def get_ride_details(alias, ride_id):
    ride = find_ride(alias, ride_id)
    return jsonify({
        "ride": {
            "id": ride.id,
            "rideDateAndTime": ride.rideDateAndTime,
            "finalAddress": ride.finalAddress,
            "driver": ride.rideDriver.alias,
            "status": ride.status,
            "participants": [{
                "confirmation": p.confirmation,
                "participant": {
                    "alias": p.participant.alias,
                    "previousRidesTotal": p.participant.previousRidesTotal,
                    "previousRidesCompleted": p.participant.previousRidesCompleted,
                    "previousRidesMissing": p.participant.previousRidesMissing,
                    "previousRidesNotMarked": p.participant.previousRidesNotMarked,
                    "previousRidesRejected": p.participant.previousRidesRejected
                },
                "destination": p.destination,
                "occupiedSpaces": p.occupiedSpaces,
                "status": p.status
            } for p in ride.participants]
        }
    })

# PARTICIPANTES
@app.route("/usuarios/<alias>/rides/<int:ride_id>/requestToJoin/<participant_alias>", methods=["POST"])
def request_to_join(alias, ride_id, participant_alias):
    ride = find_ride(alias, ride_id)
    participant = find_user(participant_alias)
    if not participant:
        abort(404, description="Participant no encontrado.")
    if ride.status != "ready":
        abort(422, description="Ride ya iniciado.")
    if any(p.participant.alias == participant_alias for p in ride.participants):
        abort(422, description="Ya solicitaste unirte.")
    data = request.get_json()
    destination = data.get("destination")
    occupiedSpaces = data.get("occupiedSpaces")
    if ride.remainingSpaces() < occupiedSpaces:
        abort(422, description="No hay suficientes espacios.")
    rp = RideParticipation(participant, destination, occupiedSpaces)
    ride.participants.append(rp)
    participant.rides.append(rp)
    return jsonify({"message": f"{participant_alias} solicitó unirse al ride {ride_id}."})

@app.route("/usuarios/<alias>/rides/<int:ride_id>/accept/<participant_alias>", methods=["POST"])
def accept_participant(alias, ride_id, participant_alias):
    ride = find_ride(alias, ride_id)
    p = next((p for p in ride.participants if p.participant.alias == participant_alias), None)
    if not p or p.confirmation is not None:
        abort(422, description="Solicitud inválida.")
    if ride.remainingSpaces() < p.occupiedSpaces:
        abort(422, description="No hay espacios suficientes.")
    p.confirmation = True
    p.status = "confirmed"
    return jsonify({"message": f"{participant_alias} aceptado."})

@app.route("/usuarios/<alias>/rides/<int:ride_id>/reject/<participant_alias>", methods=["POST"])
def reject_participant(alias, ride_id, participant_alias):
    ride = find_ride(alias, ride_id)
    p = next((p for p in ride.participants if p.participant.alias == participant_alias), None)
    if not p or p.confirmation is not None:
        abort(422, description="Solicitud inválida.")
    p.confirmation = False
    p.status = "rejected"
    p.participant.previousRidesRejected += 1
    return jsonify({"message": f"{participant_alias} rechazado."})

@app.route("/usuarios/<alias>/rides/<int:ride_id>/start", methods=["POST"])
def start_ride(alias, ride_id):
    ride = find_ride(alias, ride_id)
    if any(p.status not in ["confirmed", "rejected"] for p in ride.participants):
        abort(422, description="Hay solicitudes sin procesar.")
    for p in ride.participants:
        if p.status == "confirmed":
            p.status = "inprogress"
        elif p.status == "waiting":
            p.status = "missing"
    ride.status = "inprogress"
    return jsonify({"message": f"Ride {ride_id} iniciado."})

@app.route("/usuarios/<alias>/rides/<int:ride_id>/end", methods=["POST"])
def end_ride(alias, ride_id):
    ride = find_ride(alias, ride_id)
    for p in ride.participants:
        if p.status == "inprogress":
            p.status = "notmarked"
            p.participant.previousRidesNotMarked += 1
        elif p.status == "confirmed":
            p.participant.previousRidesCompleted += 1
        elif p.status == "missing":
            p.participant.previousRidesMissing += 1
        p.participant.previousRidesTotal += 1
    ride.status = "done"
    return jsonify({"message": f"Ride {ride_id} terminado."})

@app.route("/usuarios/<alias>/rides/<int:ride_id>/unloadParticipant", methods=["POST"])
def unload_participant(alias, ride_id):
    ride = next((r for r in rides if r.id == ride_id), None)
    if not ride:
        abort(404, description="Ride no encontrado.")
    p = next((p for p in ride.participants if p.participant.alias == alias), None)
    if not p or p.status != "inprogress":
        abort(422, description="No puedes bajarte ahora.")
    p.status = "done"
    p.participant.previousRidesCompleted += 1
    p.participant.previousRidesTotal += 1
    return jsonify({"message": f"{alias} se bajó del ride {ride_id}."})

if __name__ == "__main__":
    app.run(debug=True)
