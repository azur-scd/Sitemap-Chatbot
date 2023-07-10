# Sitemap Chatbot

![forthebadge](forthebadge.svg)

This repo is an illustration (with a little bit adaptation) of this post on the Exlibris Developer Network blog : [https://developers.exlibrisgroup.com/blog/create-an-gpt-based-chatbot-on-exlibris-knowledge-center/](https://developers.exlibrisgroup.com/blog/create-an-gpt-based-chatbot-on-exlibris-knowledge-center/)

It's a simple implementation with the Chainlit framework of a GPT-based chatbot that can be used to interact with textual content extracted from the web through a sitemap url.

## Installation

### Locally

```
git clone https://github.com/azur-scd/AurehalNetwork.git
```

Create a virtualenv and install dependencies

```
python -m venv YOUR_VENV

# Windows
cd YOUR_VENV/Scripts & activate
# Linux
source VENV_NAME/bin/activate

pip install -r requirements.txt
```
Run the app (on http://localhost:8000)

```
chainlit run app.py
```

### Docker

```
git clone https://github.com/azur-scd/AurehalNetwork.git
```

```
docker build -t YOUR_IMAGE_NAME:TAG .
docker run --name YOUR_CONTAINER_NAME -d -p 8000:8000 YOUR_IMAGE_NAME:TAG
```

## Customization

1. Create a .env file on the model of .example.env with 

  - your own OpenAI API Key (free account but cost calculated on the use)
  - the sitemap url to be explored : all the links can be extracted from a generic sitemap or they are also seamlessly filtered for patterns, e.g. using https://knowledge.exlibrisgroup.com/Primo as argument implies taking all URLs only corresponding to the Primo category.
  - and potentially your own HuggingFace API token (free account) if you plan to use a free model available on HuggingFace hub

2. The app uses the llamaindex local data storage mechanism : the documents, index and vector stores are persist in the ./storage folder. The name and location can be changed, don't forget to change the parameter in app.py file
```
storage = "./storage"
```

3. The chatbot uses the default llamindex environment from OpenAI with the text-embedding-ada-002 model for embeddings and the gpt-3.5-turbo model as chat model. They can be overwritten in the app.py file

```
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", streaming=True) # can be changed to another OpenAI model like the new  - and more expensive - "gpt-4" or "text-davinci-003"
```

```
# Embeddings are implicit in the code, add these lines to overwrite
embeddings = OpenAIEmbeddings(model="<your_openai_embeddingd_model>", chunk_size=1)
# and modifiy
service_context = ServiceContext.from_defaults(
    llm_predictor=llm_predictor,
    embed_model=embeddings,
    chunk_size=512,
    callback_manager=CallbackManager([cl.LlamaIndexCallbackHandler()]),
)

```
4. To use an open source LLM from HuggingFace in place of GPT, apply the following

```
# Comment
#llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", streaming=True)

# and uncomment
llm = HuggingFaceHub(repo_id="lmsys/vicuna-13b-v1.3", model_kwargs={"temperature":0.7, "max_length":2048}) # for example
```

## How it works

When launched, the app looks if storage context exists in the ./storage folder :
- if it does exist : the chatbot is ready
- if not : the content of each webpage of the sitemap given in the SITEMAP_URL environment variable is extracted and stored in a temporary local directory, then converted in chunked documents, embeddings and nodes stored in the ./storage folder. the cahtbot is then ready.

**On a first launch and depending on the number of urls to browse, it may take a long time before the chatbot is ready.**




