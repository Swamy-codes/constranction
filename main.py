import os
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader

# --------------------------------------------------
# Load .env ONLY for local (Render sets RENDER=true)
# --------------------------------------------------
if os.getenv("RENDER") != "true":
    from dotenv import load_dotenv
    load_dotenv()

# --------------------------------------------------
# Environment Variables
# --------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if not all([
    SUPABASE_URL,
    SUPABASE_KEY,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET
]):
    raise RuntimeError("Missing environment variables")

# --------------------------------------------------
# Supabase Client
# --------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------------------------------
# Cloudinary Config
# --------------------------------------------------
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# --------------------------------------------------
# FastAPI App
# --------------------------------------------------
app = FastAPI(title="Projects API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Health Check
# --------------------------------------------------
@app.get("/")
def health():
    return {"status": "ok"}

# --------------------------------------------------
# Create Project API
# --------------------------------------------------
@app.post("/projects")
async def create_project(
    description: str = Form(...),
    images: List[UploadFile] = File(...)
):
    try:
        image_urls = []

        for image in images:
            result = cloudinary.uploader.upload(
                image.file,
                folder="projects"
            )
            image_urls.append(result["secure_url"])

        data = {
            "description": description,
            "image_urls": image_urls
        }

        response = supabase.table("projects").insert(data).execute()

        return {
            "message": "Project created successfully",
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
