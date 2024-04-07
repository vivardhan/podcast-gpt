from flask import (
    Flask,
    render_template,
    request,
    Response,
)
import json
from qa_bot.qa_bot import QABot

app = Flask(__name__)

podcast_gpt = QABot()

@app.route("/")
def home():    
    return render_template("index.html")

def generate_response(user_text: str):
    db_matches, response = podcast_gpt.answer_question(user_text)
    for chunk in response:
        content = chunk.choices[0].delta.content
        yield f"data: {json.dumps({'type': 'chunk', 'text': content})}\n\n"

    yield f"data: {json.dumps({'type': 'db_matches', 'matches': [m.to_dict() for m in db_matches]})}\n\n"

@app.route("/get")
def get_bot_response():    
    user_text = request.args.get('msg')
    return Response(generate_response(user_text), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run()
