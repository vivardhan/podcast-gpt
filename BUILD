py_library(
	name="configs",
	srcs=[
		"configs.py",
	],
)

py_library(
	name="google_utils",
	srcs=[
		"google_oauth_credentials.py",
		"google_client_provider.py",
	],
	data=[
		"assets/google_oauth_token.json",
	],
)

py_library(
	name="utils",
	srcs=[
		"data_api/utils/file_utils.py",
		"data_api/utils/gcs_utils.py",
	],
	deps=[
		":google_utils",
	]
)

py_binary(
	name="audio_download",
	srcs=[
		"data_api/audio_download/main.py",
		"data_api/audio_download/audio_downloader.py",
		"data_api/audio_download/rss/rss_audio_downloader.py",
		"data_api/audio_download/youtube/youtube_audio_downloader.py",
		"data_api/audio_download/youtube/video_lister.py",
	],
	main="data_api/audio_download/main.py",
	deps=[
		":configs",
		":google_utils",
		":utils",
	],
)

py_binary(
	name="speech_to_text",
	srcs=[
		"data_api/speech_to_text/assembly_ai_transcriber.py"
	],
	main="data_api/speech_to_text/assembly_ai_transcriber.py",
	deps=[
		":configs",
		":utils",
	],
)