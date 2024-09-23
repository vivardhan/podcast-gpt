# System Imports
import json
import numpy as np
import os
from typing import Dict, List, Tuple

# Third Party Imports
from qdrant_client.models import (
    Distance,
    VectorParams,
)
import tiktoken
from tqdm import tqdm

# Package Imports
from data_api.audio_download.audio_downloader import MetadataKeys
from data_api.chapterizer.transcript_chapterizer import (
    convert_timestamp_string_to_milliseconds,
)
from data_api.embeddings.embeddings_generator import EmbeddingsGenerator
from data_api.embeddings.vector_db.constants import VectorDBConstants
from data_api.embeddings.vector_db.qdrant_client_provider import QdrantClientProvider
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def create_chapter_title_to_timestamps_dict(
    chapters_metadata: List[Tuple[str, str]]
) -> Dict[str, Tuple[int, int]]:
    second_timestamps = [
        convert_timestamp_string_to_milliseconds(t[0]) // 1000
        for t in chapters_metadata
    ]

    title_to_timestamps = {}
    num_chapters = len(second_timestamps)
    for index in range(num_chapters):
        start_timestamp = second_timestamps[index]
        next_index = index + 1
        end_timestamp = (
            second_timestamps[next_index] if next_index < num_chapters else None
        )
        title_to_timestamps[chapters_metadata[index][1]] = (
            start_timestamp,
            end_timestamp,
        )

    return title_to_timestamps


class DBUpdate:

    @classmethod
    def generate_and_store_embeddings(cls, podcast_names: List[str]) -> None:
        print("Creating Vector Database")
        count_exceeds = 0
        total_chapters = 0

        js = json.loads(GCSClient.download_textfile_as_string(Paths.VECTOR_DB_PATH))
        js_embeddings = js[VectorDBConstants.EMBEDDINGS_FIELD]
        js_data = js[VectorDBConstants.DATA_FIELD]

        embeddings = []
        data = []
        for index in range(len(js_data)):
            if js_data[index][VectorDBConstants.CHAPTER_TRANSCRIPT_FIELD] == "":
                continue

            embeddings.append(js_embeddings[index])
            data.append(js_data[index])

        searchable_embeddings = set(
            [
                d[VectorDBConstants.PODCAST_TITLE_FIELD]
                + d[VectorDBConstants.EPISODE_TITLE_FIELD]
                + d[VectorDBConstants.CHAPTER_TITLE_FIELD]
                for d in data
            ]
        )

        for podcast_name in podcast_names:
            chapterized_data_folder = Paths.get_chapterized_data_folder(podcast_name)
            chapterized_files = GCSClient.list_files(
                chapterized_data_folder, Paths.JSON_EXT
            )
            print("Generating embeddings for {}".format(podcast_name))
            for chapterized_file in tqdm(chapterized_files):
                text = GCSClient.download_textfile_as_string(chapterized_file)
                chapters = json.loads(text)

                episode_title = Paths.get_title_from_path(chapterized_file)
                metadata_file = Paths.get_metadata_file_path(
                    podcast_name, episode_title
                )
                metadata = json.loads(
                    GCSClient.download_textfile_as_string(metadata_file)
                )
                chapter_title_to_timestamps = create_chapter_title_to_timestamps_dict(
                    metadata[MetadataKeys.CHAPTERS_KEY]
                )

                for chapter_title, chapter_text in chapters.items():
                    if chapter_text == "":
                        continue

                    if (
                        podcast_name + episode_title + chapter_title
                        in searchable_embeddings
                    ):
                        continue

                    full_text = "Title: {} \n\nTranscript\n: {}".format(
                        chapter_title, chapter_text
                    )
                    token_count = num_tokens_from_string(full_text)
                    total_chapters += 1
                    if token_count > EmbeddingsGenerator.EMBEDDING_TOKEN_LIMIT:
                        count_exceeds += 1
                        continue

                    start_timestamp, end_timestamp = chapter_title_to_timestamps[
                        chapter_title
                    ]

                    embeddings.append(EmbeddingsGenerator.get_embedding(full_text))
                    data.append(
                        {
                            VectorDBConstants.PODCAST_TITLE_FIELD: podcast_name,
                            VectorDBConstants.EPISODE_TITLE_FIELD: episode_title,
                            VectorDBConstants.CHAPTER_TITLE_FIELD: chapter_title,
                            VectorDBConstants.EPISODE_URL_FIELD: metadata[
                                MetadataKeys.URL_KEY
                            ],
                            VectorDBConstants.PODCAST_GUEST_FIELD: metadata[
                                MetadataKeys.GUEST_KEY
                            ],
                            VectorDBConstants.START_TIMESTAMP_FIELD: start_timestamp,
                            VectorDBConstants.END_TIMESTAMP_FIELD: end_timestamp,
                            VectorDBConstants.CHAPTER_TRANSCRIPT_FIELD: chapter_text,
                        }
                    )

        GCSClient.upload_string_as_textfile(
            Paths.VECTOR_DB_PATH,
            json.dumps(
                {
                    VectorDBConstants.EMBEDDINGS_FIELD: embeddings,
                    VectorDBConstants.DATA_FIELD: data,
                }
            ),
        )

        print(
            "{} chapters exceeded token limit out of {}".format(
                count_exceeds, total_chapters
            )
        )

    @classmethod
    def create_and_deploy_index_and_endpoint(cls):
        print("Uploading database to qdrant")
        QdrantClientProvider.client.recreate_collection(
            collection_name=VectorDBConstants.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VectorDBConstants.EMBEDDINGS_DIMENSION,
                distance=Distance.COSINE,
            ),
        )

        database = json.loads(
            GCSClient.download_textfile_as_string(Paths.VECTOR_DB_PATH)
        )

        QdrantClientProvider.client.upload_collection(
            collection_name=VectorDBConstants.COLLECTION_NAME,
            vectors=np.array(database[VectorDBConstants.EMBEDDINGS_FIELD]),
            payload=database[VectorDBConstants.DATA_FIELD],
        )
