import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Define the Strict Data Structure (The Schema)
# This forces the LLM to output exactly these fields and nothing else.
class KYCData(BaseModel):
    name: str = Field(description="The full name of the person exactly as it appears on the ID.")
    dob: str = Field(description="The date of birth in YYYY-MM-DD format.")
    id_number: str = Field(description="The unique government identification number.")
    is_valid: bool = Field(description="True if the image appears to be a clear, valid government ID. False if blurred, cropped, or highly suspicious.")

# 2. Initialize the AI Client
# It will automatically pick up the GEMINI_API_KEY from your environment variables
client = genai.Client()

def extract_id_data(image_path: str) -> KYCData:
    """Reads a local image file and extracts structured KYC data."""
    
    # 3. Read the image file into memory
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    # 4. Construct the prompt and attach the image bytes
    prompt = "Analyze this government ID card. Extract the exact Name, Date of Birth, and ID Number. If the document is unreadable or fake, set is_valid to false."
    
    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        prompt
    ]

    # 5. Call Gemini 2.5 Flash with the Structured Output configuration
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=KYCData,
            temperature=0.1 # Keep temperature low to prevent hallucinating data
        ),
    )
    
    # 6. Return the perfectly formatted Python object
    return response.parsed

# --- Testing the Script ---
if __name__ == "__main__":
    try:
        print("Processing ID Document...")
        # Point this to your test image
        extracted_data = extract_id_data("IMG_8747.jpeg") 
        
        print("\n--- Extraction Successful ---")
        print(f"Name: {extracted_data.name}")
        print(f"DOB: {extracted_data.dob}")
        print(f"ID Number: {extracted_data.id_number}")
        print(f"Valid Document: {extracted_data.is_valid}")
        
    except Exception as e:
        print(f"Error processing document: {e}")