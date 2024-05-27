from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os
import shutil
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_openai.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI

#setup chat environment, embeddings will be sent to AI defined here
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4o-2024-05-13")
#Setup DB
embedding = OpenAIEmbeddings()
directory = 'Docs'
persist_directory = 'db'
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

#clean the Docs directory by moving processed pdf's to vectorized folder
def pdf_cleanup(pdfName):
    vectorized_folder = 'Docs/vectorized'
    if not os.path.exists(vectorized_folder):
        os.makedirs(vectorized_folder)
    pdf_name = os.path.basename(pdfName)
    destination = os.path.join(vectorized_folder, pdf_name)
    shutil.move(pdfName, destination)
    print(f"{pdfName} has been moved to the 'vectorized' folder.")

#check if this document has already been added to the DB. Uses embeddings so gets sent to AI
def doc_exists(pdfName):
    """Check if a document with the given PDF name exists in the database."""
    existing_docs = vectordb.get(where={"source": pdfName})['metadatas'][1]
    print(existing_docs)
    if existing_docs:
    	return True

#Load the docs to db after checking if they exist
def docLoader(pdfName):
    try:
        if doc_exists(pdfName):
            print(f"[!] Skipping already processed PDF: {pdfName}")
            pdf_cleanup(pdfName)
            return
        
        print("[+] loading ", pdfName)
        loader = PyPDFLoader(pdfName)
        pages = loader.load_and_split()
        vectordb.from_documents(pages, embedding=embedding,persist_directory=persist_directory)
        pdf_cleanup(pdfName)
    except Exception as e:
        print(f'[-] unable to load doc: caught {type(e)}: {e}')

#Load pdfs from Docs folder to DB by sending to docLoader
for filename in os.listdir(directory):
	if filename.endswith('.pdf'):
		f = os.path.join(directory, filename)
		print(f)
		try:
			docLoader(f)
		except:
			print("doc not found")
	else:
		print(f'{filename} is not a pdf')



