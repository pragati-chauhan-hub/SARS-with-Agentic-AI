import os
import tempfile
import json
from typing import Dict, Any
from groq import Groq
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TranscriptionService:
    """
    Service for transcribing emergency call audio files and extracting patient information
    using Groq's Whisper for transcription and Llama for information extraction
    """

    def __init__(self):
        # Set Groq API key from environment variable
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)

    async def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file to text using OpenAI Whisper API

        Args:
            audio_file_path: Path to the audio file (MP3, WAV, etc.)

        Returns:
            Dictionary containing transcription and extracted information
        """
        try:
            # Read audio file
            with open(audio_file_path, "rb") as audio_file:
                # Use Groq Whisper API for transcription
                transcript_response = self.client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    language="en",  # Can be made dynamic based on requirement
                    response_format="json"
                )

            transcribed_text = transcript_response.text if hasattr(
                transcript_response, 'text') else ""

            if not transcribed_text:
                return {
                    "success": False,
                    "error": "No transcription generated",
                    "transcription": "",
                    "extracted_data": {}
                }

            # Extract patient information from transcribed text
            extracted_data = await self.extract_patient_info(transcribed_text)

            return {
                "success": True,
                "transcription": transcribed_text,
                "extracted_data": extracted_data,
                "audio_duration": getattr(transcript_response, 'duration', 0)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "transcription": "",
                "extracted_data": {}
            }

    async def extract_patient_info(self, transcribed_text: str) -> Dict[str, Any]:
        """
        Extract structured patient information from transcribed emergency call
        using GPT-4 or GPT-3.5-turbo

        Args:
            transcribed_text: The transcribed emergency call text

        Returns:
            Dictionary with extracted patient information
        """
        try:
            # Prompt for Groq Llama to extract structured information
            extraction_prompt = f"""
You are an AI assistant helping emergency services extract and intelligently fill critical information from emergency call transcriptions.

Analyze the following emergency call transcription and extract information. If specific details are NOT mentioned in the call, use your medical knowledge to make reasonable assumptions based on the emergency type and symptoms described.

INSTRUCTIONS:
1. Extract information that IS mentioned in the call
2. For missing non-critical information (like exact age, specific names), make reasonable assumptions:
   - If age not mentioned but context suggests elderly/young, estimate appropriately (e.g., 65, 8, 45)
   - If patient name not mentioned, use generic placeholder like "Patient" or infer from context
   - If caller name not mentioned, use "Caller" or relationship (e.g., "Family Member", "Witness")
3. Emergency type MUST be specific (e.g., "Heart Attack", "Car Accident", "Stroke", "Breathing Difficulty")
4. Symptoms should be comprehensive list based on what's described
5. Severity MUST be assessed based on symptoms described (critical/high/medium/low)
6. Special requirements should be inferred from emergency type and symptoms
7. IMPORTANT - Phone/Contact Number Extraction:
   - Look for ANY mention of numbers: "phone", "contact", "mobile", "cell", "telephone", "number", "reach at", "call back"
   - If ONLY ONE number is mentioned, put it in BOTH patient_phone AND caller_phone
   - If multiple numbers mentioned, try to determine which belongs to patient vs caller
   - Extract the full phone number including area code if mentioned
   - Common formats: "555-1234", "555 1234", "(555) 1234", "5551234"

Extract and fill the following in JSON format:

1. patient_name: Patient's name if mentioned, otherwise use "Patient" or infer from context
2. patient_age: Age if mentioned, otherwise estimate based on context (number, e.g., 55)
3. patient_gender: Gender if mentioned or inferred from voice/context, otherwise "unknown"
4. patient_phone: Patient's phone/contact/mobile number if mentioned (ANY phone number mentioned should be captured here), otherwise empty string
5. emergency_type: SPECIFIC type (e.g., "Heart Attack", "Severe Car Accident", "Respiratory Failure", "Stroke")
6. symptoms: Comprehensive list of all symptoms mentioned or implied (array of strings)
7. location: Full address if mentioned, otherwise describe location from context
8. severity: Based on symptoms - "critical" (life-threatening), "high" (serious), "medium" (urgent), "low" (non-urgent)
9. caller_name: Caller's name if mentioned, otherwise use relationship (e.g., "Spouse", "Neighbor", "Witness")
10. caller_phone: Caller's phone/contact/mobile number if mentioned (ANY phone number mentioned should be captured here), otherwise empty string
11. special_requirements: Medical equipment/support needed based on emergency type (array, e.g., ["Cardiac Care", "Oxygen Support"])
12. consciousness: Patient conscious state (yes/no/unknown) - infer from description if not explicit
13. breathing: Breathing status (yes/no/difficulty/unknown) - infer from description if not explicit

Transcription:
"{transcribed_text}"

Think step by step:
1. What type of emergency is this?
2. How severe are the symptoms?
3. What medical support is needed?
4. What details can be reasonably inferred?
5. Are there ANY phone/contact numbers mentioned? Extract ALL numbers found.

CRITICAL: If you find ANY phone number or contact number in the transcription, you MUST extract it to patient_phone and caller_phone fields. Do not leave these fields empty if a number is mentioned.

Return ONLY valid JSON. No markdown, no explanations, just the JSON object.
"""

            # Call Groq API for information extraction using Llama
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert medical AI for emergency services. Extract information from calls and intelligently fill missing details using medical knowledge. When extracting phone numbers, recognize alternative phrases like 'contact number', 'mobile number', 'cell number', 'telephone', 'number to reach', etc. Always provide specific, actionable information. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ],
                temperature=0.3,  # Balanced for extraction and inference
                max_tokens=1200
            )

            # Parse the response
            extracted_json = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if extracted_json.startswith("```json"):
                extracted_json = extracted_json[7:]
            if extracted_json.startswith("```"):
                extracted_json = extracted_json[3:]
            if extracted_json.endswith("```"):
                extracted_json = extracted_json[:-3]

            extracted_json = extracted_json.strip()

            # Parse JSON
            extracted_data = json.loads(extracted_json)

            # Post-process and ensure all fields are filled intelligently
            extracted_data = self._ensure_complete_data(extracted_data)

            # Add priority based on severity
            severity = extracted_data.get("severity", "medium").lower()
            priority_map = {
                "critical": 1,
                "high": 2,
                "medium": 3,
                "low": 4
            }
            extracted_data["priority"] = priority_map.get(severity, 3)

            return extracted_data

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return self._get_default_patient_info()
        except Exception as e:
            print(f"Extraction error: {e}")
            return self._get_default_patient_info()

    def _get_default_patient_info(self) -> Dict[str, Any]:
        """Return default patient information structure when extraction fails"""
        return {
            "patient_name": "Patient",
            "patient_age": 45,
            "patient_gender": "unknown",
            "patient_phone": "",
            "emergency_type": "Medical Emergency",
            "symptoms": ["Emergency reported"],
            "location": "Location to be determined",
            "severity": "high",
            "priority": 2,
            "caller_name": "Caller",
            "caller_phone": "",
            "special_requirements": ["Basic Life Support"],
            "consciousness": "unknown",
            "breathing": "unknown"
        }

    def _ensure_complete_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure extracted data is complete and usable
        Fill in missing critical fields with intelligent defaults
        """
        # Ensure patient name
        if not data.get("patient_name") or data.get("patient_name").strip() == "":
            data["patient_name"] = "Patient"

        # Ensure patient age is a number
        if not data.get("patient_age") or data.get("patient_age") == "":
            data["patient_age"] = 45  # Default adult age
        elif isinstance(data.get("patient_age"), str):
            try:
                data["patient_age"] = int(data["patient_age"])
            except:
                data["patient_age"] = 45

        # Ensure gender
        if not data.get("patient_gender"):
            data["patient_gender"] = "unknown"

        # Ensure patient phone
        if not data.get("patient_phone"):
            data["patient_phone"] = ""

        # Ensure emergency type is specific
        if not data.get("emergency_type") or data.get("emergency_type") == "unknown":
            data["emergency_type"] = "Medical Emergency"

        # Ensure symptoms is a list
        if not data.get("symptoms"):
            data["symptoms"] = ["Emergency reported - details to be confirmed"]
        elif isinstance(data.get("symptoms"), str):
            data["symptoms"] = [data["symptoms"]]

        # Ensure location
        if not data.get("location") or data.get("location").strip() == "":
            data["location"] = "Location to be confirmed by dispatcher"

        # Ensure severity
        if not data.get("severity") or data.get("severity") not in ["critical", "high", "medium", "low"]:
            data["severity"] = "high"  # Default to high for safety

        # Ensure caller name
        if not data.get("caller_name") or data.get("caller_name").strip() == "":
            data["caller_name"] = "Caller"

        # Ensure caller phone
        if not data.get("caller_phone"):
            data["caller_phone"] = ""

        # Ensure special requirements is a list
        if not data.get("special_requirements"):
            # Infer special requirements from emergency type
            emergency_type = data.get("emergency_type", "").lower()
            if "heart" in emergency_type or "cardiac" in emergency_type:
                data["special_requirements"] = [
                    "Cardiac Care", "Defibrillator"]
            elif "breath" in emergency_type or "respiratory" in emergency_type:
                data["special_requirements"] = [
                    "Oxygen Support", "Respiratory Care"]
            elif "accident" in emergency_type or "trauma" in emergency_type:
                data["special_requirements"] = [
                    "Trauma Care", "Multiple Units"]
            elif "stroke" in emergency_type:
                data["special_requirements"] = [
                    "Stroke Protocol", "Critical Care"]
            else:
                data["special_requirements"] = ["Basic Life Support"]
        elif isinstance(data.get("special_requirements"), str):
            data["special_requirements"] = [data["special_requirements"]]

        # Ensure consciousness
        if not data.get("consciousness"):
            data["consciousness"] = "unknown"

        # Ensure breathing
        if not data.get("breathing"):
            data["breathing"] = "unknown"

        return data

    async def process_audio_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Process uploaded audio file

        Args:
            file_bytes: Audio file bytes
            filename: Original filename

        Returns:
            Processing result with transcription and extracted data
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name

            # Process transcription
            result = await self.transcribe_audio(temp_file_path)

            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"File processing error: {str(e)}",
                "transcription": "",
                "extracted_data": {}
            }
