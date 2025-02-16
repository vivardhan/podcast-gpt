# System Imports
import os

# Third Party Imports
from qdrant_client import QdrantClient


class QdrantClientProvider:

    client = QdrantClient(
        url="https://1f5dca92-803f-4fc2-8cfe-0a26622b0497.us-east4-0.gcp.cloud.qdrant.io:6333",
        api_key=os.environ["QDRANT_API_KEY"],
    )
