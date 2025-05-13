# System Imports
import os

# Third Party Imports
from qdrant_client import QdrantClient


class QdrantClientProvider:

    client = QdrantClient(
        url="https://ec6d5030-0711-4cda-8173-61f68ed3d693.us-east4-0.gcp.cloud.qdrant.io:6333",
        api_key=os.environ["QDRANT_API_KEY"],
    )
