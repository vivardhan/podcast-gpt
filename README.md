# podcast-gpt
Answers questions from users based on podcasts. Currently the supported podcasts are [TheDrive](https://peterattiamd.com/podcast/) and [Huberman Lab](https://www.hubermanlab.com/podcast).

## 1. Setup

### 1.1 First Time Setup

#### 1.1.1 Create your virtual environment and activate it.
Run the following commands from the repo root directory:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 1.1.2 Validate virtual environment:
Confirm that the above has worked by running
```bash
which python3
```
This should print a path starting with '.venv/bin/'


#### 1.1.3 Install Requirements

##### 1.1.3.1 Python packages
```bash
python3 -m pip install -r requirements.txt
```

##### 1.1.3.2 Bazel
Bazel is used as the build system. Install it using these [instructions](https://bazel.build/install) for your operating system.


### 1.2 Future Setup

#### 1.2.1 Activating your virtual environment
Run the following command from the repo root:
```bash
source .venv/bin/activate
```

#### 1.2.2 Deactivating your virtual environment
Once done working on the repo, run:
```bash
deactivate
```

## 2. Data API
The data API supports downloading audio files for podcast episodes, transcribing audio to text files and accessing transcribed data.

### 2.1 Downloading audio
To download all audio files for the supported podcasts and upload them to GCS, run the following:
```bash
bazel run //:audio_download
```

### 2.2 Transcribing audio
To transcribe audio files that have been put in GCS, run the following:
```bash
bazel run //:speech_to_text
```
This will create 2 sets of transcriptions, one without speaker identifiers and one with speaker identifiers. Both transcripts will be uploaded to GCS.

### 2.3 Accessing transcripts
Run the following to see how many words are in all the raw transcripts for each podcast:
```bash
bazel run //:transcript_stats
```
This binary (see `data_api/transcript_inspector/main.py`) also shows how to access the contents of transcripts.

