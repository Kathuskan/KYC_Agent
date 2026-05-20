import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- 1. Schema Definition ---
class KYCData(BaseModel):
    name: str = Field(description="The full name of the person exactly as it appears on the ID.")
    dob: str = Field(description="The date of birth in YYYY-MM-DD format.")
    id_number: str = Field(description="The unique government identification number.")
    is_valid: bool = Field(description="True if the image appears to be a clear, valid government ID. False if blurred, cropped, or suspicious.")

client = genai.Client()

# --- 2. The AI Extraction Function (Phase 1) ---
def extract_id_data(image_path: str) -> KYCData:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    prompt = "Analyze this government ID card. Extract the exact Name, Date of Birth, and ID Number. If the document is unreadable or fake, set is_valid to false."
    
    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        prompt
    ]

    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=KYCData,
            temperature=0.1 
        ),
    )
    return response.parsed

# --- 3. The Verification Function (Phase 2) ---
def verify_against_registry(extracted_data: KYCData, registry_file: str = 'registry.json') -> dict:
    """Cross-references the AI-extracted data against our mock database."""
    
    # Fail immediately if the AI flagged the image as blurry or fake
    if not extracted_data.is_valid:
        return {"status": "FAILED", "reason": "Image is not a valid or readable ID card."}
    
    # Open our mock database
    try:
        with open(registry_file, 'r') as file:
            registry = json.load(file)
    except FileNotFoundError:
        return {"status": "ERROR", "reason": "Database file not found."}

    # Search for the ID number in the database
    for record in registry:
        if record['id_number'] == extracted_data.id_number:
            # If ID exists, strictly check if the Name and DOB match perfectly
            name_match = record['name'].upper() == extracted_data.name.upper()
            dob_match = record['dob'] == extracted_data.dob
            
            if name_match and dob_match:
                return {"status": "VERIFIED", "reason": "All data matches government records perfectly."}
            else:
                return {"status": "FAILED", "reason": "Name or Date of Birth does not match official records."}
            
    return {"status": "FAILED", "reason": "ID Number not found in government registry."}

# --- 4. The Main Execution Flow ---
if __name__ == "__main__":
    try:
        print("Step 1: AI is reading the ID Document...")
        # Make sure sample_id.jpg exists in your folder!
        extracted_data = extract_id_data("image.png") 
        
        print("\n--- AI Extracted Data ---")
        print(f"Name: {extracted_data.name}")
        print(f"DOB: {extracted_data.dob}")
        print(f"ID Number: {extracted_data.id_number}")
        print(f"Valid Image: {extracted_data.is_valid}")
        
        print("\nStep 2: Cross-referencing with database...")
        final_result = verify_against_registry(extracted_data)
        
        print("\n===============================")
        print(f"FINAL KYC STATUS: {final_result['status']}")
        print(f"DETAILS: {final_result['reason']}")
        print("===============================\n")
        
    except Exception as e:
        print(f"\nCritical Error: {e}")