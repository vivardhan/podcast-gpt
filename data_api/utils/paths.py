# System Imports
import os


class Paths:

    AUDIO_DATA_FOLDER = "audio_data"
    TEXT_DATA_FOLDER = "text_data"
    ASSEMBLY_AI_FOLDER = "assembly_ai_transcripts"
    RAW_TRANSCRIPT_FOLDER = "raw_transcripts"
    SPEAKER_TRANSCRIPT_FOLDER = "speaker_transcripts"
    QA_PAIRS_FOLDER = "qa_pairs"
    TXT_EXT = ".txt"
    JSON_EXT = ".json"
    VECTOR_DB_PATH = "vector_db" + JSON_EXT
    METADATA_SUFFIX = "metadata"
    CHAPTERIZED_DATA_FOLDER = "chapterized_data"

    @classmethod
    def get_title_from_path(cls, path: str) -> str:
        # Removes the extension of a file path
        filename = os.path.basename(path)
        dot_pos = filename.rfind(".")
        return filename[:dot_pos]

    @classmethod
    def get_audio_data_folder(cls, podcast_name: str) -> str:
        return os.path.join(podcast_name, cls.AUDIO_DATA_FOLDER)

    @classmethod
    def get_audio_path(cls, podcast_name: str, title: str, extension: str) -> str:
        return os.path.join(
            cls.get_audio_data_folder(podcast_name),
            f"{title}.{extension}",
        )

    @classmethod
    def get_text_data_folder(cls, podcast_name: str) -> str:
        return os.path.join(podcast_name, cls.TEXT_DATA_FOLDER)

    @classmethod
    def get_aai_transcript_folder(cls, podcast_name: str) -> str:
        return os.path.join(
            cls.get_text_data_folder(podcast_name),
            cls.ASSEMBLY_AI_FOLDER,
        )

    @classmethod
    def get_raw_transcript_folder(cls, podcast_name: str) -> str:
        return os.path.join(
            cls.get_text_data_folder(podcast_name),
            cls.RAW_TRANSCRIPT_FOLDER,
        )

    @classmethod
    def get_speaker_transcript_folder(cls, podcast_name: str) -> str:
        return os.path.join(
            cls.get_text_data_folder(podcast_name),
            cls.SPEAKER_TRANSCRIPT_FOLDER,
        )

    @classmethod
    def get_aai_transcript_path(cls, podcast_name: str, title: str) -> str:
        return os.path.join(
            cls.get_aai_transcript_folder(podcast_name), title + cls.JSON_EXT
        )

    @classmethod
    def get_raw_transcript_path(cls, podcast_name: str, title: str) -> str:
        return os.path.join(
            cls.get_raw_transcript_folder(podcast_name), title + cls.TXT_EXT
        )

    @classmethod
    def get_speaker_transcript_path(cls, podcast_name: str, title: str) -> str:
        return os.path.join(
            cls.get_speaker_transcript_folder(podcast_name), title + cls.TXT_EXT
        )

    @classmethod
    def get_chapterized_data_folder(cls, podcast_name: str) -> str:
        return os.path.join(
            cls.get_text_data_folder(podcast_name), cls.CHAPTERIZED_DATA_FOLDER
        )

    @classmethod
    def get_chapterized_transcript_path(cls, podcast_name: str, title: str) -> str:
        return os.path.join(
            cls.get_chapterized_data_folder(podcast_name), title + cls.JSON_EXT
        )

    @classmethod
    def get_metadata_file_name_for_title(cls, title: str) -> str:
        # Gets the file name (not full path) for a given episode title
        return "{}_{}{}".format(title, cls.METADATA_SUFFIX, cls.JSON_EXT)

    @classmethod
    def get_metadata_file_path(cls, podcast_name: str, title: str) -> str:
        # Gets the full path for the metadata file for a given episode
        return os.path.join(
            cls.get_audio_data_folder(podcast_name),
            cls.get_metadata_file_name_for_title(title),
        )

    @classmethod
    def get_qa_pairs_folder(cls, podcast_name) -> str:
        return os.path.join(
            cls.get_text_data_folder(podcast_name),
            cls.QA_PAIRS_FOLDER,
        )
