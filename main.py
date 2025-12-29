# main.py
from dotenv import load_dotenv
import os

# MUST be called **before importing supabase_client**
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from cloudinary_utils import upload_image
from supabase import supabase
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict later
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
