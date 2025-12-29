import os
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from cloudinary import config, uploader
from io import BytesIO

# --------------------
# Load .env locally only
# --------------------
if os.getenv("RENDER") != "true":
    from dotenv import load_dotenv
    load_dotenv()

# --------------------
# Configure Cloudinary
# --------------------
config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(file_bytes: BytesIO) -> str:
    try:
        result = uploader.upload(file_bytes)
        return result.get("secure_url", "")
    except Exception as e:
        print("Cloudinary upload error:", e)
        return ""

# --------------------
# Initialize FastAPI
# --------------------
app = FastAPI(title="Project Management API")

# --------------------
# CORS
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# Health check
# --------------------
@app.get("/")
def health():
    return {"status": "ok"}

# --------------------
# Supabase client
# --------------------
supabase: Optional[Client] = None

@app.on_event("startup")
def init_supabase():
    global supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("⚠️ Supabase not configured")
        supabase = None
        return

    try:
        supabase = create_client(url, key)
        print("✅ Supabase connected")
    except Exception as e:
        supabase = None
        print("❌ Supabase init failed:", e)

# --------------------
# Create project endpoint
# --------------------
@app.post("/projects")
async def create_project(
    description: str = Form(...),
    images: List[UploadFile] = File(...)
):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not available")

    image_urls = []

    for image in images:
        contents = await image.read()
        url = upload_image(BytesIO(contents))
        if not url:
            raise HTTPException(status_code=500, detail="Image upload failed")
        image_urls.append(url)

    try:
        response = supabase.table("projects").insert({
            "description": description,
            "image_urls": image_urls
        }).execute()
        data = getattr(response, "data", None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase insert failed: {e}")

    return {"message": "Project created successfully", "data": data}

# --------------------
# Uvicorn entrypoint for local run
# --------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
