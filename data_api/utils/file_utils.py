# System Imports
import os
import shutil

def create_temp_local_directory(directory_path: str) -> None:
	if not os.path.exists(directory_path):
		os.makedirs(directory_path)


def delete_temp_local_directory(directory_path: str) -> None:
	try:
	    shutil.rmtree(directory_path)
	except OSError as e:
	    print("Error: %s - %s." % (e.filename, e.strerror))