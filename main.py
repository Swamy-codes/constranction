import os

# Load .env only in local development (Render sets RENDER=true)
if os.getenv("RENDER") is None:
    from dotenv import load_dotenv
    load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from cloudinary_utils import upload_image

# ---- Supabase configuration ----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- FastAPI app ----
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Health check (important for Render) ----
@app.get("/")
def health():
    return {"status": "ok"}

# ---- Create project ----
@app.post("/projects")
async def create_project(
    description: str = Form(...),
    images: List[UploadFile] = File(...)
):
    image_urls = []

    for image in images:
        contents = await image.read()
        url = upload_image(contents)
        image_urls.append(url)

    response = supabase.table("projects").insert({
        "description": description,
        "image_urls": image_urls
    }).execute()

    return {
        "message": "Project created successfully",
        "data": response.data
    }