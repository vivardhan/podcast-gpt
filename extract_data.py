# Package Imports
from data_api.embeddings.vector_db import VectorDB
from google_client_provider import GoogleClientProvider
from podcasts import PODCASTS

def main():
	for podcast in PODCASTS:
		podcast.run_data_extraction_pipeline()

	gc_provider = GoogleClientProvider()
	vector_db = VectorDB(gc_provider)
	vector_db.generate_and_store_embeddings([podcast.name for podcast in PODCASTS])
	vector_db.create_and_deploy_index_and_endpoint()

if __name__ == "__main__":
    main()