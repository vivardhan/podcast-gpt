# podcast-gpt
Answers questions from users based on podcasts. Currently the supported podcasts are [TheDrive](https://peterattiamd.com/podcast/) and [Huberman Lab](https://www.hubermanlab.com/podcast).

## 1. Setup

### 1.1 First Time Setup

#### 1.1.1 Python version
Ensure that your python version is 3.11 or older. Python 3.12 causes failures during dependency installation. Check your python version by running the command from section 1.1.3. In case you need to downgrade your python version, running the following should suffice:
```bash
brew install python@3.11
```

Make sure to verify your version after trying this. If your python version is not 3.11 then you may need to modify your PATH environment variable accordingly. Eg. on Mac, edit your bash profile (`~/.bash_profile`) by adding the following line to the end of the file:
export PATH="$(brew --prefix)/opt/python@3.11/libexec/bin:$PATH"

#### 1.1.2 Create your virtual environment and activate it.
Run the following commands from the repo root directory:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 1.1.3 Validate virtual environment:
Confirm that the above has worked by running
```bash
which python3
```
This should print a path starting with '.venv/bin/'


#### 1.1.4 Install Requirements

##### 1.1.4.1 Python packages
```bash
python3 -m pip install -r requirements.txt
```

##### 1.1.4.2 Bazel
Bazel is used as the build system. Install it for your operating system:

For Mac:
```bash
brew install bazel
```

For Linux/Debian, follow these [instructions](https://bazel.build/install/ubuntu#install-on-ubuntu).

#### 1.1.5 Obtain Credentials

##### 1.1.5.1 GCP Credentials
1. Go to [Google Cloud Console](console.cloud.google.com) and make sure the 'podcast-gpt' project is selected in the drop down at the top.
2. Click on the menu button in the top left corner (3 horizontal lines)
3. Mouse over 'IAM and admin', then click on 'Service accounts' in the menu that opens on the right
4. Click on the link under email corresponding to the service account named 'Compute Engine default service account'
5. At the top, choose 'KEYS'
6. Click on 'ADD KEY' > Create new key
7. Choose 'JSON' and click on 'CREATE'. A file with a private key will be downloaded to your computer. 
8. Put the downloaded file in [repo_root]/credentials and name it 'compute_engine_key.json'.

Note: The credentials folder is in .gitignore so that you don't accidentally commit any credentials to the repo.

##### 1.1.5.2 OpenAI Credentials
1. Contact Sakshi Jain (sakshi.r.jain@gmail.com) to obtain the OpenAI API key for this project.
2. Add your API key as an environment variable. For Mac, add a line to your bash profile ('~/.bash_profile'):
`export OPENAI_API_KEY=[YOUR_API_KEY]`
3. Then execute:
```bash
source ~/.bash_profile
```
4. Verify that the key is now available by executing:
```bash
echo $OPENAI_API_KEY
```
It should print out your API key.

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

#### 1.2.3 Resolving OpenAI API Key Errors:
You may run into issues if python cannot find your OpenAI credentials in the environment variables. Rerun steps 3 and 4 from section 1.1.5.2 to resolve this.

## 2. Data API
The data API supports the following functionality.

### 2.1 Extracting Data
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
4. Uploads the database to QDrant as a searchable vector database

### 2.2 Accessing transcripts
Run the following to see how many words are in all the raw transcripts for each podcast:
```bash
bazel run //:transcript_stats
```
This binary (see `data_api/transcript_inspector/main.py`) also shows how to access the contents of transcripts.

### 2.3 Using LLMs to generate question/answer data
Here, we wish to generate question/answer pairs for the purpose of finetuning our Podcast GPT model as well as for evaluating it. The technique to do this automatically, is to provide chapterized transcripts of podcast episodes to existing LLMs in the form of a prompt that asks the LLM to convert the chapterized transcript into a list of question and answer pairs. These question and answer pairs will be saved to GCS for further use in training and evaluation.
Run the following binary (still WIP) to obtain the question/answer pairs:
```bash
bazel run //:generate_qa_data
```

## 3. Question Answer Bot
You can run a question answer bot that will answer your questions based on the 2 podcasts:

### 3.1 Testing locally

#### 3.1.2 On Command Line
```bash
bazel run //:run_qa_bot
```

#### 3.1.2 In the browser
```bash
gunicorn main:app --worker-class gevent --timeout 600
```
Then navigate to the URL that is printed out.

### 3.2 Testing and Deployment on Koyeb
Koyeb is a free web hosting service that integrates with Flask and Github to serve web apps. Test the [deployed version](https://podcast-gpt-podcastgpt.koyeb.app/).

In order to redeploy:
1. Create an account on Koyeb with your github login 
2. Push your changes to the develop branch of the repo
3. If you don't see the podcast-gpt project already available in Koyeb, connect it to your account
4. Navigate to the podcast-gpt app and click on Redeploy.
5. Monitor the build and deployment process through the UI on Koyeb.