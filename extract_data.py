# Package Imports
from data_api.embeddings.vector_db.db_update import DBUpdate
from podcasts import PODCASTS

def main():
	for podcast in PODCASTS:
		podcast.run_data_extraction_pipeline()

	DBUpdate.generate_and_store_embeddings([podcast.name for podcast in PODCASTS])
	DBUpdate.create_and_deploy_index_and_endpoint()

if __name__ == "__main__":
    main()