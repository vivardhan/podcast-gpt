# System Imports
import os

# Third Party Imports
from qdrant_client import QdrantClient


class QdrantClientProvider:

    client = QdrantClient(
        url="https://6b57b75d-0e64-4089-92a9-942a637167e6.us-east4-0.gcp.cloud.qdrant.io:6333",
        api_key=os.environ["QDRANT_API_KEY"],
    )
