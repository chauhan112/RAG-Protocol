from fastapi import FastAPI, HTTPException, UploadFile, File
from typing import List, Dict, Optional
from pydantic import BaseModel
import os
import shutil
from .collections import VectorStoreWithCollections

class CollectionCreate(BaseModel):
    name: str

class PDFCreate(BaseModel):
    collection_name: str
    pdf_name: str


app = FastAPI()
vector_store = VectorStoreWithCollections(base_storage_path="./vector_storage")

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
    print("liszinh")
    return list(vector_store.collections.keys())

@app.get("/collections/{collection_name}", response_model=dict)
async def get_collection(collection_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {
        "name": collection_name,
        "pdfs": list(vector_store.collections[collection_name]["pdfs"].keys())
    }

@app.delete("/collections/{collection_name}", response_model=dict)
async def delete_collection(collection_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Delete collection directory and its contents
    shutil.rmtree(vector_store.collections[collection_name]["path"])
    del vector_store.collections[collection_name]
    return {"status": "deleted"}

# PDF CRUD Operations
@app.post("/collections/{collection_name}/pdfs/", response_model=dict)
async def upload_pdf(collection_name: str, pdf_name: str, file: UploadFile = File(...)):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file temporarily
    temp_path = f"temp_{pdf_name}.pdf"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        vector_store.add_pdf_to_collection(collection_name, temp_path, pdf_name)
        return {"pdf_name": pdf_name, "collection_name": collection_name, "status": "uploaded"}
    finally:
        os.remove(temp_path)

@app.get("/collections/{collection_name}/pdfs/", response_model=List[str])
async def list_pdfs(collection_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    return list(vector_store.collections[collection_name]["pdfs"].keys())

@app.delete("/collections/{collection_name}/pdfs/{pdf_name}", response_model=dict)
async def delete_pdf(collection_name: str, pdf_name: str):
    if collection_name not in vector_store.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    if pdf_name not in vector_store.collections[collection_name]["pdfs"]:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    # Remove PDF file
    pdf_path = vector_store.collections[collection_name]["pdfs"][pdf_name]
    os.remove(pdf_path)
    
    # Recreate vector store without the deleted PDF
    vector_store.collections[collection_name]["vector_store"] = None
    remaining_pdfs = vector_store.collections[collection_name]["pdfs"]
    del remaining_pdfs[pdf_name]
    
    vector_store._db = None
    for pdf_path in remaining_pdfs.values():
        vector_store.add_pdf(pdf_path)
    vector_store.save(str(vector_store.collections[collection_name]["path"] / "vector_store"))
    
    return {"status": "deleted"}

