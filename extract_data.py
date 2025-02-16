# System Imports
import argparse

# Package Imports
from data_api.embeddings.vector_db.db_update import DBUpdate
from podcasts import PODCASTS

def main(args):
    if not args.vector_db_only:
        for podcast in PODCASTS:
            podcast.run_data_extraction_pipeline()

    DBUpdate.generate_and_store_embeddings([podcast.name for podcast in PODCASTS])
    DBUpdate.create_and_deploy_index_and_endpoint()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the data extraction pipeline for all podcasts.")
    parser.add_argument(
        "--vector-db-only",
        help="Only update the vector database.",
        type=bool,
        default=False,
    )

    args = parser.parse_args()
    main(args)
