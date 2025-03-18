#%%
def test_collection_crud():
    from src.VectorCollections import VectorCollections
    import shutil
    testFolderName = ".temp_folder"
    vc = VectorCollections(testFolderName)
    assert vc.read_collections() == []
    vc.create_collection("test")
    assert vc.read_collections() == ["test"]
    vc.delete_collection("test")
    assert vc.read_collections() == []
    vc.create_collection("test")
    vc.update_collection_name("test","test2")
    assert vc.read_collections() == ["test2"]
    shutil.rmtree(testFolderName)

def test_pdf_crud():
    from src.VectorCollections import VectorCollections
    import shutil
    testFolderName = ".temp_folder"
    vc = VectorCollections(testFolderName )
    vc.create_collection("test")
    pdfile = "./doc/Protokoll_der_Eigentümerversammlung_(WEMoG).pdf"
    vc.add_pdf("test",pdfile, "test.pdf")
    assert (vc.base_storage_path / "test" / "vector_store").exists()
    assert vc.read_pdfs("test") == ["test.pdf"]
    vc.remove_pdf("test","test.pdf")
    assert vc.read_pdfs("test") == []

    
    shutil.rmtree(testFolderName)
# %%
test_collection_crud()
# %%
test_pdf_crud()

# %%
