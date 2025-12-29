from dotenv import load_dotenv
import os

# Must be called first
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from cloudinary_utils import upload_image
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key not found in environment variables.")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
