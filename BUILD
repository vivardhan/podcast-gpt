py_library(
	name="google_utils",
	srcs=[
		"google_oauth_credentials.py",
		"google_client_provider.py",
	],
	data=[
		"credentials/compute_engine_key.json"
	],
)

py_library(
	name="utils",
	srcs=[
		"data_api/utils/file_utils.py",
		"data_api/utils/gcs_utils.py",
		"data_api/utils/paths.py",
		"data_api/utils/youtube_utils.py",
	],
	deps=[
		":google_utils",
	]
)

py_library(
	name="download_audio_files",
	srcs=[
		"data_api/audio_download/audio_downloader.py",
		"data_api/audio_download/chapter_extractor.py",
		"data_api/audio_download/factory.py",
		"data_api/audio_download/feed_config.py",
		"data_api/audio_download/rss/rss_audio_downloader.py",
		"data_api/audio_download/youtube/youtube_audio_downloader.py",
		"data_api/audio_download/youtube/video_lister.py",
	],
	deps=[
		":utils",
	],
)

py_library(
	name="transcribe_audio_files",
	srcs=[
		"data_api/speech_to_text/assembly_ai_transcriber.py"
	],
	deps=[
		":utils",
	],
)

py_library(
	name="chapterize_transcripts",
	srcs=[
		"data_api/chapterizer/transcript_chapterizer.py",
	],
	deps=[
		":utils",
		":transcribe_audio_files",
	],
)

py_library(
	name="generate_embeddings",
	srcs=[
		"data_api/embeddings/embeddings_generator.py",
		"data_api/embeddings/vector_db/constants.py",
		"data_api/embeddings/vector_db/db_update.py",
		"data_api/embeddings/vector_db/qdrant_client_provider.py",
		"data_api/embeddings/vector_db/vector_search.py",
	],
)

py_library(
	name="podcast_data",
	srcs=[
		"podcasts.py",
	],
	deps=[
		":chapterize_transcripts",
		":download_audio_files",
		":generate_embeddings",
		":transcribe_audio_files",
	],
)

py_binary(
	name="run_qa_bot",
	srcs=[
		"qa_bot/main.py",
		"qa_bot/qa_bot.py",
	],
	main="qa_bot/main.py",
	deps=[
		":podcast_data",
		":utils",
	]
)

py_binary(
	name="extract_data",
	srcs=[
		"extract_data.py",
	],
	deps=[
		":podcast_data",
	]
)

py_binary(
	name="transcript_stats",
	srcs=[
		"data_api/transcript_inspector/main.py",
	],
	main="data_api/transcript_inspector/main.py",
	deps=[
		":utils",
		":podcast_data",
	],
)

py_binary(
	name="generate_qa_data",
	srcs=[
		"data_api/qa_generator/llm_qa_generator.py",
		"data_api/qa_generator/main.py",
		"data_api/qa_generator/gpt4.py",
	],
	main="data_api/qa_generator/main.py",
	deps=[
		":utils",
		":podcast_data",
	],
)

py_binary(
	name="backfill_raw_transcripts",
	srcs=[
		"data_api/speech_to_text/raw_transcript_backfill.py",
	],
	main="data_api/speech_to_text/raw_transcript_backfill.py",
	deps=[
		":utils",
	],
)

py_binary(
	name="modify_speaker_labels",
	srcs=[
		"data_api/speech_to_text/speakers_modifier.py",
	],
	main="data_api/speech_to_text/speakers_modifier.py",
	deps=[
		":utils",
	],
)