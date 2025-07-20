from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

# Store conversations in memory (per session)
conversations = {}

def call_deepseek_r1(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": messages,
        "temperature": 0.7
    }

    response = requests.post(OPENROUTER_ENDPOINT, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        goal = request.form.get('goal')
        deadline = request.form.get('deadline')
        free_time = float(request.form.get('free_time'))

        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        today = datetime.now()
        days_remaining = (deadline_date - today).days

        prompt = f"""
        Create a detailed strategy to achieve the following goal:
        Goal: {goal}
        Deadline: {deadline} ({days_remaining} days from now)
        Available time per day: {free_time} hours

        Provide:
        1. A breakdown of milestones (weekly/monthly)
        2. Daily action items
        3. Potential obstacles and solutions
        4. Recommended resources

        Format the response with clear headings and bullet points.
        """

        try:
            strategy = call_deepseek_r1([{"role": "user", "content": prompt}])
        except Exception as e:
            strategy = f"Error generating strategy: {str(e)}"

        return render_template('index.html',
                               goal=goal,
                               deadline=deadline,
                               free_time=free_time,
                               strategy=strategy)

    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data['message']
    session_id = data.get('session_id', 'default')

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({"role": "user", "content": user_message})

    try:
        ai_message = call_deepseek_r1(conversations[session_id])
        conversations[session_id].append({"role": "assistant", "content": ai_message})

        return jsonify({'response': ai_message, 'session_id': session_id})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}", 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True)
