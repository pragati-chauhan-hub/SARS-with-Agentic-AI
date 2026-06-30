from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.sms_service import sms_service

router = APIRouter()

# In-memory storage for dispatches (replace with database in production)
dispatches = {}


@router.post("/")
async def dispatch_ambulance(dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch an ambulance to an emergency location via WhatsApp

    Expected data:
    - ambulance_id: ID of the ambulance to dispatch
    - emergency_id: ID of the emergency
    - patient_info: Patient information (optional)
    - hospital_name: Name of the destination hospital
    - hospital_address: Address of the destination hospital
    - driver_phone: Driver's phone number (E.164 format, e.g., +919876543210)
    - eta: Estimated time of arrival (optional)
    """
    ambulance_id = dispatch_data.get("ambulance_id")
    hospital_name = dispatch_data.get("hospital_name")
    hospital_address = dispatch_data.get("hospital_address")
    driver_phone = dispatch_data.get("driver_phone")

    # Validate required fields
    if not all([ambulance_id, hospital_name, hospital_address, driver_phone]):
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: ambulance_id, hospital_name, hospital_address, driver_phone"
        )

    # Generate dispatch ID
    dispatch_id = f"DSP-{len(dispatches) + 1:03d}"

    # Send WhatsApp notification
    whatsapp_result = sms_service.send_hospital_assignment(
        driver_phone=driver_phone,
        ambulance_id=ambulance_id,
        hospital_name=hospital_name,
        hospital_address=hospital_address,
        patient_info=dispatch_data.get("patient_info"),
        eta=dispatch_data.get("eta", "8 minutes")
    )

    # Store dispatch information
    dispatches[dispatch_id] = {
        "dispatch_id": dispatch_id,
        "ambulance_id": ambulance_id,
        "emergency_id": dispatch_data.get("emergency_id"),
        "hospital_name": hospital_name,
        "hospital_address": hospital_address,
        "driver_phone": driver_phone,
        "patient_info": dispatch_data.get("patient_info"),
        "eta": dispatch_data.get("eta", "8 minutes"),
        "status": "dispatched",
        "whatsapp_sent": whatsapp_result.get("success", False),
        "whatsapp_sid": whatsapp_result.get("message_sid"),
        "whatsapp_error": whatsapp_result.get("error")
    }

    response = {
        "success": True,
        "message": "Ambulance dispatched successfully",
        "dispatch_id": dispatch_id,
        "ambulance_id": ambulance_id,
        "emergency_id": dispatch_data.get("emergency_id"),
        "hospital_name": hospital_name,
        "eta": dispatch_data.get("eta", "8 minutes"),
        "whatsapp_status": {
            "sent": whatsapp_result.get("success", False),
            "message_sid": whatsapp_result.get("message_sid"),
            "error": whatsapp_result.get("error") if not whatsapp_result.get("success") else None
        }
    }

    return response


@router.get("/{dispatch_id}")
async def get_dispatch_status(dispatch_id: str) -> Dict[str, Any]:
    """Get status of a dispatch"""
    dispatch = dispatches.get(dispatch_id)

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    return {
        "dispatch_id": dispatch_id,
        "status": dispatch.get("status", "en_route"),
        "ambulance_id": dispatch.get("ambulance_id"),
        "hospital_name": dispatch.get("hospital_name"),
        "hospital_address": dispatch.get("hospital_address"),
        "eta": dispatch.get("eta", "5 minutes"),
        "whatsapp_sent": dispatch.get("whatsapp_sent", False),
        "current_location": {
            "latitude": 28.6139,
            "longitude": 77.2090
        }
    }


@router.post("/{dispatch_id}/send-update")
async def send_dispatch_update(dispatch_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send an update message to the ambulance driver via WhatsApp

    Expected data:
    - update_type: Type of update (e.g., "ROUTE_CHANGE", "PRIORITY_UPDATE")
    - details: Update details message
    """
    dispatch = dispatches.get(dispatch_id)

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    update_type = update_data.get("update_type", "UPDATE")
    details = update_data.get("details", "")

    if not details:
        raise HTTPException(
            status_code=400, detail="Update details are required")

    # Send WhatsApp update
    whatsapp_result = sms_service.send_emergency_update(
        driver_phone=dispatch.get("driver_phone"),
        ambulance_id=dispatch.get("ambulance_id"),
        update_type=update_type,
        details=details
    )

    return {
        "success": True,
        "message": "Update sent to driver via WhatsApp",
        "dispatch_id": dispatch_id,
        "whatsapp_status": {
            "sent": whatsapp_result.get("success", False),
            "message_sid": whatsapp_result.get("message_sid"),
            "error": whatsapp_result.get("error") if not whatsapp_result.get("success") else None
        }
    }


@router.get("/")
async def get_all_dispatches() -> Dict[str, Any]:
    """Get all dispatches"""
    return {
        "dispatches": list(dispatches.values()),
        "total": len(dispatches)
    }
