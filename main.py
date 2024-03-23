# Package Imports
from podcasts import PODCASTS

def main():
	for podcast in PODCASTS:
		podcast.run_data_extraction_pipeline()


if __name__ == "__main__":
    main()