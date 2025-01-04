# System Imports
import os

# Third Party Imports
from qdrant_client import QdrantClient


class QdrantClientProvider:

    client = QdrantClient(
        url="https://23f48a24-53f6-49ad-8a8a-40cc12a68baf.europe-west3-0.gcp.cloud.qdrant.io:6333",
        api_key=os.environ["QDRANT_API_KEY"],
    )
