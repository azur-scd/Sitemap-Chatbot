import os
from trafilatura import sitemaps, fetch_url, extract
import re
import tempfile
import openai
from langchain.chat_models import ChatOpenAI
from langchain import HuggingFaceHub
from llama_index.callbacks.base import CallbackManager
from llama_index import (
    VectorStoreIndex,
    LLMPredictor,
    ServiceContext,
    StorageContext,
    SimpleDirectoryReader,
    load_index_from_storage,
)
import chainlit as cl
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
huggingfacehub_api_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
sitemap_url = os.environ.get("SITEMAP_URL")

storage = "./storage"

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", streaming=True)
# Example of open source model from Huggingface
# llm = HuggingFaceHub(repo_id="lmsys/vicuna-13b-v1.3", model_kwargs={"temperature":0.7, "max_length":2048})
llm_predictor = LLMPredictor(llm=llm)
service_context = ServiceContext.from_defaults(
    llm_predictor=llm_predictor,
    chunk_size=512,
    callback_manager=CallbackManager([cl.LlamaIndexCallbackHandler()]),
)


def get_pagename_from_url(url):
    """
    The function `get_pagename_from_url` takes a URL as input and returns the last part of the URL after
    the last slash, with any non-alphabetic characters removed, and truncated to a maximum length of 100
    characters.

    :param url: A string representing the URL of a webpage
    :type url: str
    :return: the cleaned pagename extracted from the given URL.
    """
    pagename = url.rsplit("/", 1)[-1]
    cleaned_pagename = re.sub("[^A-Z]", "", pagename, 0, re.IGNORECASE)
    # to avoid too long pagenames
    if len(cleaned_pagename) > 100:
        return cleaned_pagename[:100]
    else:
        return cleaned_pagename


def get_urls_from_sitemap(sitemap_url: str) -> str:
    """
    The function `get_urls_from_sitemap` takes a sitemap URL as input and returns a list of URLs found
    in the sitemap.

    :param sitemap_url: The sitemap_url parameter is a string that represents the URL of the sitemap. A
    sitemap is a file that lists all the URLs of a website and helps search engines crawl and index the
    website's pages
    :type sitemap_url: str
    :return: a list of URLs extracted from the provided sitemap URL.
    """
    return sitemaps.sitemap_search(sitemap_url, target_lang="en")


def load_sitemap_to_dirfiles(
    dir: str,
    sitemap_url: str,
) -> None:
    """
    The function `load_sitemap_to_dirfiles` takes a directory path and a sitemap URL, retrieves the URLs
    from the sitemap, downloads the web pages, extracts the content, and saves it as text files in the
    specified directory.

    :param dir: The `dir` parameter is a string that represents the directory where the downloaded files
    will be saved
    :type dir: str
    :param sitemap_url: The `sitemap_url` parameter is a string that represents the URL of a sitemap. A
    sitemap is a file that lists all the URLs of a website, allowing search engines to crawl and index
    the website's pages more efficiently
    :type sitemap_url: str
    """
    urls = get_urls_from_sitemap(sitemap_url)
    for url in urls:
        page_name = get_pagename_from_url(url)
        downloaded = fetch_url(url)
        if downloaded is not None:
            result = extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=True,
            )
            with open(f"{dir}/{page_name}.txt", "w", encoding="utf-8") as f:
                f.write(result)


if len(os.listdir(storage)) != 1:  # because of .gitkeep file
    # Rebuild the storage context
    storage_context = StorageContext.from_defaults(persist_dir=storage)
    # Load the index
    index = load_index_from_storage(storage_context)
else:
    # Storage not found; create a new one
    with tempfile.TemporaryDirectory(
        suffix="_llamaindex", prefix=None, dir="./"
    ) as tmpdir:
        load_sitemap_to_dirfiles(tmpdir, sitemap_url)
        filename_fn = lambda filename: {"file_name": filename}
        documents = SimpleDirectoryReader(tmpdir, file_metadata=filename_fn).load_data()
        # create index
        index = VectorStoreIndex.from_documents(
            documents, service_context=service_context
        )
        index.storage_context.persist(storage)


@cl.llama_index_factory
def factory():
    return index.as_query_engine(
        service_context=service_context,
        streaming=True,
    )
