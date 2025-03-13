from typing import List, Dict, Optional
import shutil
from pathlib import Path
from .vectorStores import LocalVectorStore

class VectorStoreWithCollections(LocalVectorStore):
    def __init__(self, base_storage_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_storage_path = Path(base_storage_path)
        self.collections: Dict[str, Dict] = {}  
        self.base_storage_path.mkdir(exist_ok=True)
    
    def create_collection(self, collection_name: str):
        collection_path = self.base_storage_path / collection_name
        collection_path.mkdir(exist_ok=True)
        self.collections[collection_name] = {
            "path": collection_path,
            "pdfs": {},
            "vector_store": None
        }
        return collection_name
    
    def load_collection(self, collection_name: str):
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        collection_path = self.collections[collection_name]["path"]
        vector_store_path = collection_path / "vector_store"
        if vector_store_path.exists():
            self._db = FAISS.load_local(
                str(vector_store_path), 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
        self.collections[collection_name]["vector_store"] = self._db
    
    def add_pdf_to_collection(self, collection_name: str, pdf_path: str, pdf_name: str):
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        # Copy PDF to collection directory
        target_path = self.collections[collection_name]["path"] / f"{pdf_name}.pdf"
        shutil.copy(pdf_path, target_path)
        
        # Add to vector store
        self.load_collection(collection_name)
        self.add_pdf(str(target_path))
        self.collections[collection_name]["pdfs"][pdf_name] = str(target_path)
        
        # Save updated vector store
        self.save(str(self.collections[collection_name]["path"] / "vector_store"))

