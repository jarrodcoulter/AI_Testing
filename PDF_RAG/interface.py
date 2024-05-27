import gradio as gr
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

#Setup Chat environment
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4-turbo-preview")
#Setup DB
embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
db = Chroma(persist_directory="db", embedding_function=embedding)  # Adjust the path as necessary

#Method to perform retrieval and return answer
def ask_chroma(msg, history):
    try:
        template = """Given the context - {context} 

        Answer the following question - {question} if you don't know the answer, or it does not exist in the given context say 'I don't know'"""
        pt = PromptTemplate(
            template=template, input_variables=["context", "question"]
        )
        retriever = db.as_retriever(search_type='similarity')
        qa = RetrievalQA.from_chain_type(llm=model, retriever=retriever, chain_type_kwargs={"prompt": pt, "verbose": True}, return_source_documents=True)
        result = qa.invoke(msg)
        print(f'answer: {result}')
        if "I don't know" in result['result']:
            finalAnswer = "I don't know. Information is not available for that question in my vector db."
        else:
            answer = result['result']
            docSource = result['source_documents'][0].metadata['source']
            finalAnswer = answer + f'\nSource: {docSource}'
        return finalAnswer
    except Exception as e:
        return str(e)

# Set up the Gradio interface
interface = gr.ChatInterface(
    fn=ask_chroma,
    #theme=THEME,
    title="Security PDF Chat",
    #examples=EXAMPLES,
    clear_btn=None,
    retry_btn=None,
    undo_btn=None,
)

if __name__ == "__main__":
    interface.launch()
