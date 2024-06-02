# Intro
Summarize blog posts from RSS feeds through AI. This is intended to be scheduled in a cron job run every 24 hours. It will output a text file with the current date as the file name. It will check for blog posts that are new within the last 24 hours, send them to the OpenAI API to be summarized, have IOCs taken out and written to a file. I have very particular format requirements for the IOCs which is why they exist the way they are. If you have other requirements, please modify the prompt template in blogparser.py. Shout out to @DanielMiessler for the prompt format idea.

You'll need to populate blogs.txt with blogs that have RSS feeds with a "content" key. CISA posts are broken into their own file as they post content to a "summary" key. So, you must know your RSS feed and what key the actual content is posted under.

You are responsible for adhering to the terms of any blog or RSS feed you parse.

### Setup
```
1. Add your API key to the .env file.
2. pip install -r requirements.txt
3. Add RSS feeds to blogs.txt
4. python blogparser.py
```

### TODO
1. Add Logger function
2. Create vectorize class to add to vector database with the PDF_RAG project
3. Actually Test this
4. Learn how to code
5. Create a cleanup function or script to clear out old text file entries
6. Add slack hook
