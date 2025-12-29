import os
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from cloudinary_utils import upload_image

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
# Health check (CRITICAL for Replit)
# --------------------
@app.get("/")
def health():
    return {"status": "ok"}

# --------------------
# Supabase (SAFE INIT)
# --------------------
supabase: Optional[Client] = None

@app.on_event("startup")
def init_supabase():
    global supabase

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("⚠️ Supabase not configured")
        return

    try:
        supabase = create_client(url, key)
        print("✅ Supabase connected")
    except Exception as e:
        print("❌ Supabase init failed:", e)
        supabase = None

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
        try:
            contents = await image.read()
            url = upload_image(contents)
            if not url:
                raise ValueError("Empty URL returned from upload_image")
            image_urls.append(url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")

    try:
        response = supabase.table("projects").insert({
            "description": description,
            "image_urls": image_urls
        }).execute()

        data = getattr(response, "data", None)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase insert failed: {e}")

    return {
        "message": "Project created successfully",
        "data": data
    }
