import os
import re
import json
import sys
sys.path.append("/yaas")

from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

## Pinecone에 인덱스 생성
def Pinecone_CreateIndex(CollectionName, IndexDimension = 1536):
    PineConeClient = Pinecone(api_key = os.getenv("PINECONE_API_KEY"))
    # Pinecone 인덱스 생성
    if not PineConeClient.has_index(CollectionName):
        PineConeClient.create_index(
            name = CollectionName,
            dimension = IndexDimension,
            metric = "cosine",
            spec = ServerlessSpec(
                cloud = 'aws',
                region = 'us-east-1'
            )
        )
    
    return PineConeClient