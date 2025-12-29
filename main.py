import os
from typing import List

# Load .env only in local development (Render sets RENDER=true)
if os.getenv("RENDER") != "true":
    from dotenv import load_dotenv
    load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from cloudinary_utils import upload_image  # Make sure this exists and returns URL

# ---- Supabase configuration ----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- FastAPI app ----
app = FastAPI(title="Project Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Health check (important for Render) ----
@app.get("/")
def health():
    return {"status": "ok"}

# ---- Create project endpoint ----
@app.post("/projects")
async def create_project(
    description: str = Form(...),
    images: List[UploadFile] = File(...)
):
    image_urls = []

    for image in images:
        try:
            contents = await image.read()
            url = upload_image(contents)
            if not url:
                raise ValueError("Empty URL returned from upload_image")
            image_urls.append(url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

    try:
        response = supabase.table("projects").insert({
            "description": description,
            "image_urls": image_urls
        }).execute()

        # Supabase response can be tuple or object
        data = getattr(response, "data", None) or (response[0] if isinstance(response, tuple) else None)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase insert failed: {str(e)}")

    return {
        "message": "Project created successfully",
        "data": data
    }
