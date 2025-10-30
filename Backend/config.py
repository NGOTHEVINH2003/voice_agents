import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

GOOGLE_API_TOKEN = os.getenv("GOOGLE_API_TOKEN")
PINECONE_API_TOKEN = os.getenv("PINECONE_API_TOKEN")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# pc = Pinecone(api_key=PINECONE_API_TOKEN)


# if PINECONE_INDEX_NAME not in [i["name"] for i in pc.list_indexes()]:
#     pc.create_index(
#         name=PINECONE_INDEX_NAME,
#         dimension=768,
#         metric="cosine",
#         spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
#     )