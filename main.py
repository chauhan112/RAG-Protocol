import streamlit as st
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains import RetrievalQA

# Set up the Streamlit app
st.title("Ollama PDF RAG Chat")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getvalue())

    # Load the PDF using PDFPlumberLoader
    loader = PDFPlumberLoader("temp.pdf")
    docs = loader.load()

    # Split documents into semantic chunks using HuggingFaceEmbeddings
    text_splitter = SemanticChunker(HuggingFaceEmbeddings())
    documents = text_splitter.split_documents(docs)

    # Create a vector store (FAISS) from the document chunks
    embedder = HuggingFaceEmbeddings()
    vector_store = FAISS.from_documents(documents, embedder)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    # Set up the LLM using Ollama – adjust the model name as needed (e.g., "deepseek-r1" or "llama3")
    llm = Ollama(model="deepseek-r1")

    # Define a prompt template for combining retrieved context and the user query
    prompt_template = PromptTemplate.from_template(
        """
        Use the following context to answer the question.
        If you do not know the answer, say "I don't know" and do not make up information.
        Context: {context}
        Question: {question}
        Answer:
        """
    )

    # Build an LLM chain with the prompt
    llm_chain = LLMChain(llm=llm, prompt=prompt_template, verbose=True)
    combine_docs_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="context")

    # Create the RetrievalQA chain that ties everything together
    qa_chain = RetrievalQA(
        combine_documents_chain=combine_docs_chain,
        retriever=retriever,
        verbose=True,
        return_source_documents=True
    )

    # Get a question from the user
    user_query = st.text_input("Ask a question about the PDF:")
    if user_query:
        with st.spinner("Processing..."):
            result = qa_chain(user_query)
            st.write("Response:")
            st.write(result["result"])
else:
    st.write("Please upload a PDF file to begin.")

# import streamlit as st
# from threading import Thread
# from streamlit.runtime.scriptrunner import add_script_run_ctx

# def target():
#     st.text("This is running in a separate thread")

# thread = Thread(target=target)
# add_script_run_ctx(thread)
# thread.start()
