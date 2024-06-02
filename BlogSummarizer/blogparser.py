import feedparser
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from datetime import date, timedelta, datetime
import time

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
model = OpenAI()
today = datetime.now().strftime("%Y%m%d")
todayBlogs = today + '.txt'
tFormat = "%Y-%m-%d %H:%M:%S"
yesterday = datetime.now() - timedelta(days=1)
print(yesterday)

def get_blog_summary(html_content):
    try:
        # Use the OpenAI API to summarize the blog post
        response = model.chat.completions.create(
        	model="gpt-4o",
            messages=[
                {"role": "system", "content": """IDENTIY and PURPOSE
You are a super-intelligent cybersecurity expert. You specialize in extracting the insightful and interesting information from cybersecurity threat reports.
Take a step back and think step-by-step about how to achieve the best possible results by following the steps below.
STEPS
Read the entire threat report from an expert perspective, thinking deeply about what's new, interesting, and surprising in the report. Think about what parts are are most useful to for understanding the threat or main theme of the report.
Create a summary that captures the spirit of the report and its insights. Use plain and conversational language when creating this summary. Pull out and talk about at least two key insights from the report. Don't use jargon or marketing language. Ignore anything that isn't relevant to the article's main theme or purpose such as advertisements for other services.
Extract all indicators of compromise and return them as comma separated lists. For example, if there are domain names, IP addresses, and file hashes, return each type in it's own section. Here is an example: 1.1.1.1,192.168.22.1,10.10.10.10
test.com,peace.com,c2domain.com 362b9f497fce52a3f14ad9de2a027d974cc810473c929fed7c37526d2f13f83a,bff674439ea8333b227f6d05caa05b2e3fe592825abd63272d4f1e4c2dfa88ea,0373ef0a7874bd8506dc64dd82ef2c6d7661a3250c8a9bb8cb8cb75a7330c1d2
If the article contains references to CVE's you will also parse those out and list them in comma separated format just like the indicators of compromise. Here is an example: CVE-2023-0669, CVE-2023-0670, CVE-2023-0674
Ensure you follow ALL these instructions when creating your output.
Do not give warnings or notes; only output the requested sections.
Do not use markdown in your responses.
Do not give headers for sections, they should be delineated by spacing.
If there are no indicators of compromise or CVEs, do not state it, just stop writing after the summary.
                """},
                {"role": "user", "content": f"Summarize the following blog post: {html_content}"}
            ]
        )
        #print(response)
        summary = response.choices[0].message.content
        #print(summary)
        return summary

    except Exception as e:
        print(f"An error occurred: caught {type(e)}: {e}")
        return None

def fileWrite(content, title, link):
    if os.path.isfile(todayBlogs):
        blogsOutContent = open(todayBlogs, 'a')
    else:
        blogsOutContent = open(todayBlogs, 'w')
    blogsOutContent.write(f'[blog entry] {title}\n{link}\n{content}\n[end blog]\n')
    blogsOutContent.close()

def blogParser(blogentry):
    blogfeed = feedparser.parse(blogentry)
    entries = blogfeed.entries
    for entry in entries:
        if datetime.fromtimestamp(time.mktime(entry.published_parsed)) > yesterday:
            if 'summary' in entry:
                print(f'[+] sending {entry.title} to summarizer')
                blogContent = entry.summary
                blog_results = get_blog_summary(blogContent)
                fileWrite(blog_results,entry.title,entry.link)
            else:
                print(f'[-] {blogentry} does not have summary')
        else:
            print(f'[-] no new {blogentry} entries since {yesterday}')

blogsFile = open('blogs.txt', 'r')
for blog in blogsFile:
    blogParser(blog)
blogsFile.close()

cisaFile = open('cisa.txt', 'r')
for cisablog in cisaFile:
    blogParser(cisablog)
cisaFile.close()
