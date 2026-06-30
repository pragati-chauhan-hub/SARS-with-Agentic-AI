from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

# Mock ambulance data
mock_ambulances = [
    {
        "id": "AMB-105",
        "vehicle_number": "KA-05-MN-9876",
        "type": "Advanced Life Support",
        "status": "available",
        "current_location": {
            "latitude": 28.5672,
            "longitude": 77.2100,
            "address": "AIIMS Hospital, New Delhi"
        },
        "driver": {
            "name": "Amit Sharma",
            "phone": "+917483588380"  # Keep same for demo
        },
        "equipment": ["Defibrillator", "Oxygen", "Stretcher"]
    },
    {
        "id": "AMB-208",
        "vehicle_number": "MH-12-XY-4321",
        "type": "Basic Life Support",
        "status": "available",
        "current_location": {
            "latitude": 28.6129,
            "longitude": 77.2295,
            "address": "India Gate Area"
        },
        "driver": {
            "name": "Priya Verma",
            "phone": "+918618243016"  # Keep same for demo
        },
        "equipment": ["Oxygen", "Stretcher"]
    },
    {
        "id": "AMB-312",
        "vehicle_number": "DL-08-PQ-7890",
        "type": "Advanced Life Support",
        "status": "available",
        "current_location": {
            "latitude": 28.6400,
            "longitude": 77.2300,
            "address": "Karol Bagh Area"
        },
        "driver": {
            "name": "Rahul Singh",
            "phone": "+917483588380"  # Keep same for demo
        },
        "equipment": ["Defibrillator", "Oxygen", "Ventilator", "Stretcher"]
    },
    {
        "id": "AMB-456",
        "vehicle_number": "UP-16-RS-2468",
        "type": "Basic Life Support",
        "status": "available",
        "current_location": {
            "latitude": 28.6050,
            "longitude": 77.2150,
            "address": "Nehru Place Area"
        },
        "driver": {
            "name": "Neha Gupta",
            "phone": "+918618243016"  # Keep same for demo
        },
        "equipment": ["Oxygen", "First Aid Kit", "Stretcher"]
    },
    {
        "id": "AMB-589",
        "vehicle_number": "HR-26-TU-1357",
        "type": "Advanced Life Support",
        "status": "available",
        "current_location": {
            "latitude": 28.6280,
            "longitude": 77.2180,
            "address": "Connaught Place Area"
        },
        "driver": {
            "name": "Vikram Patel",
            "phone": "+917483588380"  # Keep same for demo
        },
        "equipment": ["Defibrillator", "Oxygen", "ECG Monitor", "Stretcher"]
    }
]


@router.get("/")
async def get_all_ambulances() -> List[Dict[str, Any]]:
    """Get all ambulances with their current status and location"""
    return mock_ambulances


@router.get("/{ambulance_id}")
async def get_ambulance(ambulance_id: str) -> Dict[str, Any]:
    """Get specific ambulance details"""
    ambulance = next(
        (amb for amb in mock_ambulances if amb["id"] == ambulance_id), None)
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    return ambulance


@router.put("/{ambulance_id}/status")
async def update_ambulance_status(ambulance_id: str, status: Dict[str, str]) -> Dict[str, Any]:
    """Update ambulance status"""
    return {
        "success": True,
        "message": f"Ambulance {ambulance_id} status updated",
        "ambulance_id": ambulance_id,
        "new_status": status.get("status")
    }
