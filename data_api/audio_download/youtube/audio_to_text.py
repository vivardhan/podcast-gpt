# Third Party Imports
from google.cloud import speech

# Package Imports
from google_oauth_credentials import obtain_google_oauth_credentials

credentials = obtain_google_oauth_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])

def transcribe_gcs(gcs_uri: str) -> str:
    """Asynchronously transcribes the audio file specified by the gcs_uri.

    params:
        gcs_uri: The Google Cloud Storage path to an audio file.

    Returns:
        The generated transcript from the audio file provided.
    """
    

    client = speech.SpeechClient(credentials=credentials)

    audio = speech.RecognitionAudio(uri=gcs_uri)

    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=1,
        max_speaker_count=4,
    )

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=44100,
        language_code="en-US",
        audio_channel_count=2,
        enable_automatic_punctuation=True,
        diarization_config=diarization_config,
    )

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=3000)

    # The transcript within each result is separate and sequential per result.
    # However, the words list within an alternative includes all the words
    # from all the results thus far. Thus, to get all the words with speaker
    # tags, you only have to take the words list from the last result
    result = response.results[-1]
    words_info = result.alternatives[0].words

    curr_speaker = words_info[0].speaker_tag
    transcript = "Speaker {}:".format(curr_speaker)

    for word_info in words_info:
        if word_info.speaker_tag != curr_speaker:
            curr_speaker = word_info.speaker_tag
            transcript += "\n Speaker{}: ".format(curr_speaker)

        transcript += " {}".format(word_info.word)

    return transcript
