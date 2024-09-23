# podcast-gpt
Answers questions from users based on podcasts. Currently the supported podcasts are [TheDrive](https://peterattiamd.com/podcast/) and [Huberman Lab](https://www.hubermanlab.com/podcast).

## 1. Question Answer Bot
You can run a question answer bot that will answer your questions based on the 2 podcasts:

### 1.1 Testing and Deployment on Koyeb
Koyeb is a free web hosting service that integrates with Flask and Github to serve web apps. Test the [deployed version](https://podcast-gpt-podcastgpt.koyeb.app/).

In order to redeploy:
1. Create an account on Koyeb with your github login 
2. Push your changes to the develop branch of the repo
3. If you don't see the podcast-gpt project already available in Koyeb, connect it to your account
4. Navigate to the podcast-gpt app and click on Redeploy.
5. Monitor the build and deployment process through the UI on Koyeb.

### 1.2 Testing locally (requires dev setup, see below)

#### 1.2.1 On Command Line
```bash
bazel run //:run_qa_bot
```

#### 1.2.2 In the browser
```bash
gunicorn main:app --worker-class gevent --timeout 600
```
Then navigate to the URL that is printed out.

## 2. Dev Setup

### 2.1 First Time Setup

#### 2.1.1 Python version
Ensure that your python version is 3.11 or older. Python 3.12 causes failures during dependency installation. Check your python version by running the command from section 1.1.3. In case you need to downgrade your python version, running the following should suffice:
```bash
brew install python@3.11
```

Make sure to verify your version after trying this. If your python version is not 3.11 then you may need to modify your PATH environment variable accordingly. Eg. on Mac, edit your bash profile (`~/.bash_profile`) by adding the following line to the end of the file:
export PATH="$(brew --prefix)/opt/python@3.11/libexec/bin:$PATH"

#### 2.1.2 Create your virtual environment and activate it.
Run the following commands from the repo root directory:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 2.1.3 Validate virtual environment:
Confirm that the above has worked by running
```bash
which python3
```
This should print a path starting with '.venv/bin/'


#### 2.1.4 Install Requirements

##### 2.1.4.1 Python packages
```bash
python3 -m pip install -r requirements.txt
```

##### 2.1.4.2 Bazel
Bazel is used as the build system. Install it for your operating system:

For Mac:
```bash
brew install bazel
```

For Linux/Debian, follow these [instructions](https://bazel.build/install/ubuntu#install-on-ubuntu).

#### 2.1.5 Obtain Credentials

Note: Contact Vivardhan Kanoria (vivardhan@gmail.com) to obtain credentials/access for the GCS project and all API keys below. If you'd like to fork this repo and use your own paid accounts on these services, you may do so.

##### 2.1.5.1 GCP Credentials
1. Go to [Google Cloud Console](console.cloud.google.com) and make sure the 'podcast-gpt' project is selected in the drop down at the top.
2. Click on the menu button in the top left corner (3 horizontal lines)
3. Mouse over 'IAM and admin', then click on 'Service accounts' in the menu that opens on the right
4. Click on the link under email corresponding to the service account named 'Compute Engine default service account'
5. At the top, choose 'KEYS'
6. Click on 'ADD KEY' > Create new key
7. Choose 'JSON' and click on 'CREATE'. A file with a private key will be downloaded to your computer. 
8. Put the downloaded file in [repo_root]/credentials and name it 'compute_engine_key.json'.

Note: The credentials folder is in .gitignore so that you don't accidentally commit any credentials to the repo.

##### 2.1.5.2 OpenAI Credentials
1. Add your API key as an environment variable. For Mac, add a line to your bash profile ('~/.bash_profile'):
`export OPENAI_API_KEY=[YOUR_API_KEY]`
2. Then execute:
```bash
source ~/.bash_profile
```
3. Verify that the key is now available by executing:
```bash
echo $OPENAI_API_KEY
```
It should print out your API key.

##### 2.1.5.3 qdrant Credentials
1. Add your API key as an environment variable. For Mac, add a line to your bash profile ('~/.bash_profile'):
`export QDRANT_API_KEY=[YOUR_API_KEY]`
2. Then execute:
```bash
source ~/.bash_profile
```
3. Verify that the key is now available by executing:
```bash
echo $QDRANT_API_KEY
```
It should print out your API key.

##### 2.1.5.4 AssemblyAI Credentials
1. Add your API key as an environment variable. For Mac, add a line to your bash profile ('~/.bash_profile'):
`export ASSEMBLYAI_API_KEY=[YOUR_API_KEY]`
2. Then execute:
```bash
source ~/.bash_profile
```
3. Verify that the key is now available by executing:
```bash
echo $ASSEMBLYAI_API_KEY
```
It should print out your API key.

### 2.2 Future Setup

#### 2.2.1 Activating your virtual environment
Run the following command from the repo root:
```bash
source .venv/bin/activate
```

#### 2.2.2 Deactivating your virtual environment
Once done working on the repo, run:
```bash
deactivate
```

#### 2.2.3 Resolving OpenAI/qdrant/AssemblyAI API Key Errors:
You may run into issues if python cannot find your OpenAI/qdrant/AssemblyAI credentials in the environment variables. Rerun steps 2 and 3 from sections 2.1.5.2/2.1.5.3/2.1.5.4 to resolve this.

#### Resolving dependency errors
If you get python import errors, use the following steps to resolve the error:
1. Make sure your virtual environment is enabled (section 1.2.1)
2. Re-run dependency installation (section 1.1.4.1)
3. Ensure that any missing dependencies are installed with python3 -m pip install [dependency_name]
4. Add any newly installed dependencies to requirements.txt as follows (see [https://stackoverflow.com/questions/62885911/pip-freeze-creates-some-weird-path-instead-of-the-package-version](stackoverflow) for why this particular command is used). Please make sure you don't push unused dependencies into the requirements file though!
```bash
python3 -m pip list --format=freeze > requirements.txt
```

## 3. Data API
The data API supports the following functionality.

### 3.1 Extracting Data
To run the data extraction pipeline, run the following:
```bash
bazel run //:extract_data
```

This does the following for each podcast:
1. Retrieves a list of episodes
2. For episodes whose data isn't already available on GCS:
    - Retrieve and upload audio data to GCS
    - Parse chapters for the episode (timestamps and chapter descriptions) from the episode description and store it on GCS
    - Transcribe the audio to text using Assembly AI and upload 3 types of transcripts to GCS - without speaker identifiers, with speaker identifiers and json output taken directly from assembly AI. Upload all of these to GCS
    - Create transcripts for each chapter, given the chapter information above and upload these to GCS
3. Creates and uploads to GCS a database podcast titles, episode titles, chapter titles and chapter transcripts, along with embeddings for each chapter title and chapter transcript pair.
4. Uploads the database to QDrant as a searchable vector database for RAG

### 3.2 Accessing transcripts
Run the following to see how many words are in all the raw transcripts for each podcast:
```bash
bazel run //:transcript_stats
```
This binary (see `data_api/transcript_inspector/main.py`) also shows how to access the contents of transcripts.
