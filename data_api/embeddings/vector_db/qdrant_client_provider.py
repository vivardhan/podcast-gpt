# System Imports
import os

# Third Party Imports
from qdrant_client import QdrantClient

class QdrantClientProvider:

	client = QdrantClient(
	    url="https://f9b5e12e-96e8-4a0d-92e3-154fad93523a.us-east4-0.gcp.cloud.qdrant.io:6333",
	    api_key=os.environ["QDRANT_API_KEY"],
	)