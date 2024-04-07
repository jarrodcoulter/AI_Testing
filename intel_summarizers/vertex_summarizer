import os, requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain_google_genai import GoogleGenerativeAI
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import json
from autogen import config_list_from_json
from autogen import UserProxyAgent
import autogen
from serpapi import GoogleSearch
import google.generativeai as genai
import argparse

load_dotenv()
broswerless_api_key = os.getenv("BROWSERLESS_API_KEY")
vertext_api_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
config_list = config_list_from_json("OAI_CONFIG_LIST")
#genai.configure(api_key="GOOGLE_APPLICATION_CREDENTIALS")
  
llm_config = {
    "config_list": config_list,
    "temperature": 0,
    "timeout": 120,
}
parser = argparse.ArgumentParser(description="Scrape a website and process its content.")
parser.add_argument("-u", "--url", help="The URL to scrape", required=True)
args = parser.parse_args()
#Create functions
#Function for scraping
def summary(content):
    llm = GoogleGenerativeAI(temperature = 0, model = "gemini-pro", google_api_key = vertext_api_key)
    text_splitter = RecursiveCharacterTextSplitter(separators=["]n]n", "\n"], chunk_size = 10000, chunk_overlap=500)
    docs = text_splitter.create_documents([content])
    map_prompt = """
    write a summary of the following and include all indicators of compromise (IOCS) such as IP addresses, file hashes, and domain names. This will be a complete list of IOCs from the article, include every IOC encounted including the type, and context of the IOC.:
    "{text}"
    """
    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])
    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type='map_reduce',
        map_prompt = map_prompt_template,
        combine_prompt = map_prompt_template,
        verbose = True
    )
    output = summary_chain.run(input_documents=docs)
    return output

def scraping(url):
    print("Scraping website...")
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    data = {
        "url": url,
    }
    #data_json = json.dumps(data)
    #print(data_json)
    response = requests.post(f"https://chrome.browserless.io/content?token={broswerless_api_key}",headers=headers,json=data)
    print(response.text)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text()
        print("CONTENT... ", text)
        if len(text) > 10000:
            output = summary(text)
            return output
        else:
            return text
    else:
        print(f"HTTP request failed with status code {response.status_code}")
#Create user proxy agent
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    code_execution_config={
        "work_dir": "coding"
        },
        #llm_config=llm_config,
        is_termination_msg=lambda msg: msg["content"] is not None and "TERMINATE" in msg["content"],
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=1)
#Create research agent
researcher = autogen.AssistantAgent(
    name = "researcher",
    llm_config = llm_config,
    system_message="""
    You are an expert cyber security threat analyst. You provide accurate summaries of intelligence articles that you are provided. 
    In addition to a comprehensive summary, you pull out all indicators of compromise. 
    You will visit relevant links to ensure complete coverage and understanding of current threat actor behavior and IOCs and take all sites into consideration for your summary. 
    Your final output contains a summary of the article and a section below for each IOC type. Below the Type, include the IOCS of that type separated by a comma, there should be no other formatting, no ` ofr . If the URLs or domains have been 'defanged' add back the 'http' and remove any brackets. 
    If you encounter errors, just print the information you currently have. You must wait for web scraping to occur before looking for IOCs in the content."""
)

scrape_text = scraping(args.url)
task = f"Use the following to pull all IOCs and produce them in a table format: {scrape_text}"
#print(task)
user_proxy.initiate_chat(researcher,message=task)
