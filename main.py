from flask import Flask, render_template, request
from qa_bot.qa_bot import QABot

app = Flask(__name__)

podcast_gpt = QABot()

@app.route("/")
def home():    
    return render_template("index.html")

@app.route("/get")
def get_bot_response():    
    userText = request.args.get('msg')  
    response = podcast_gpt.answer_question(userText)
    return response

if __name__ == "__main__":
    app.run()