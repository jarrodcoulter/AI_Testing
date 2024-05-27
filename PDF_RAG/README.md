# Intro
This is a method to have a conversation with your PDF documents through AI. This version is setup to run through ChatGPT, however I recommend testing by running this through something like Ollama.
Ollama has a Docker image, so setup is easy. You can modify the model variable and use a LangChain import to use Ollama.

### Setup
```
1. Add your API key to the .env file.
2. pip install -r requirements.txt
3. Add PDFs to the Docs folder
4. python Vectorize.py
5. python interface.py
6. open browser to 127.0.0.1:7860
```

### TODO
1. Test various local embeddings
2. Attempt to poison local models
3. Create rules to prevent poisoning
4. Extend to other doc types
5. Add file upload feature to interface
