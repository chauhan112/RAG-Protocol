from fastapi import FastAPI, HTTPException, UploadFile, File
from typing import List, Dict, Optional
from pydantic import BaseModel
import os
import shutil
from .VectorCollections import VectorCollections
from fastapi.middleware.cors import CORSMiddleware


class CollectionCreate(BaseModel):
    name: str

class PDFCreate(BaseModel):
    collection_name: str
    pdf_name: str

class CollectionUpdate(BaseModel):
    oldName: str
    newName: str


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
vector_store = VectorCollections(base_storage_path="./.vector_storage")

# Collection CRUD Operations
@app.post("/collections/", response_model=dict)
async def create_collection(collection: CollectionCreate):
    try:
        collection_name = vector_store.create_collection(collection.name)
        return {"collection_name": collection_name, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/collections/", response_model=List[str])
async def list_collections():
    return vector_store.read_collections()

@app.get("/collections/{collection_name}", response_model=dict)
async def read_pdfs(collection_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {
        "name": collection_name,
        "pdfs": vector_store.read_pdfs(collection_name)
    }

@app.delete("/collections/{collection_name}", response_model=dict)
async def delete_collection(collection_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")

    vector_store.delete_collection(collection_name)
    return {"status": "deleted"}

@app.post("/collections/update/", response_model=dict)
async def update_collection_name(collection: CollectionUpdate):
    if collection.oldName not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    try:
        vector_store.update_collection_name(collection.oldName, collection.newName)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "updated"}

# PDF CRUD Operations
@app.post("/collections/{collection_name}/pdfs/", response_model=dict)
async def upload_pdf(collection_name: str, pdf_name: str, file: UploadFile = File(...)):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    temp_path = f"temp_{pdf_name}.pdf"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        vector_store.add_pdf(collection_name, temp_path, pdf_name)
        return {"pdf_name": pdf_name, "collection_name": collection_name, "status": "uploaded"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.remove(temp_path)

@app.get("/collections/{collection_name}/pdfs/", response_model=List[str])
async def list_pdfs(collection_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    return vector_store.read_pdfs(collection_name)

@app.delete("/collections/{collection_name}/pdfs/{pdf_name}", response_model=dict)
async def delete_pdf(collection_name: str, pdf_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    if pdf_name not in vector_store.collections[collection_name]["pdfs"]:
        raise HTTPException(status_code=404, detail="PDF not found")

    vector_store.remove_pdf(collection_name, pdf_name)
    return {"status": "deleted"}

