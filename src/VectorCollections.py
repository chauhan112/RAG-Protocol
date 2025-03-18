from typing import List, Dict, Optional
import shutil, os
from pathlib import Path
from .vectorStores import LocalVectorStore
from .tools import SerializationDB
from langchain_community.vectorstores import FAISS

class VectorCollections:
    def __init__(self, base_storage_path: str):
        self.base_storage_path = Path(base_storage_path)
        self.collections = {}
        self.base_storage_path.mkdir(exist_ok=True)
        self.local_file_path = self.base_storage_path / "collections.pkl"
        if self.local_file_path.exists():
            self.collections = SerializationDB.readPickle(self.local_file_path)
    def read_collections(self) -> List[str]:
        return list(self.collections.keys())
    def create_collection(self, collection_name: str):
        collection_path = self.base_storage_path / collection_name
        collection_path.mkdir(exist_ok=True)
        self.collections[collection_name] = {
            "path": collection_path,
            "pdfs": {},
        }
        self.sync()
    def delete_collection(self, collection_name: str):
        collection_path = self.base_storage_path / collection_name
        shutil.rmtree(collection_path)
        del self.collections[collection_name]
        self.sync()
    def update_collection_name(self, old_name: str, new_name: str):
        newPath = self.base_storage_path / new_name
        if newPath.exists():
            raise ValueError(f"Collection {new_name} already exists")
        infos = self.collections[old_name].copy()
        os.rename(infos["path"], newPath )
        self.collections[new_name] = infos
        self.collections[new_name]["path"] = newPath
        del self.collections[old_name]
    def sync(self):
        SerializationDB.pickleOut(self.collections, self.local_file_path)

    def read_pdfs(self, collection_name: str):
        return list(self.collections[collection_name]["pdfs"].keys())
    def add_pdf(self, collection_name: str, pdf_path: str, pdf_name: str):
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")

        target_path = self.collections[collection_name]["path"] / pdf_name
        if target_path.exists():
            raise ValueError("Pdf name already exists")
        shutil.copy(pdf_path, target_path)
        
        lvs = LocalVectorStore()
        vector_store_path = self.base_storage_path / collection_name / "vector_store"
        if vector_store_path.exists():
            lvs.load(vector_store_path)
        lvs.add_pdf(str(target_path))
        lvs.save(vector_store_path)

        self.collections[collection_name]["pdfs"][pdf_name] = str(target_path)
        self.sync()
    def remove_pdf(self, collection_name: str, pdf_name: str):
        pdf_path = self.collections[collection_name]["pdfs"][pdf_name]
        os.remove(pdf_path)
        del self.collections[collection_name]["pdfs"][pdf_name]
        self.sync()

        vector_store_path = self.base_storage_path / collection_name / "vector_store"
        pdfs = list(self.collections[collection_name]["pdfs"].values())
        if len(pdfs) == 0:
            shutil.rmtree(vector_store_path)
            return
        lvs = LocalVectorStore()
        for pdf in pdfs:
            lvs.add_pdf(pdf)
        lvs.save(vector_store_path)