from flask import Flask, request, jsonify
from flask_cors import CORS
from meta_ai_api import MetaAI
import praw
import os

app = Flask(__name__)
CORS(app)

ai = MetaAI()

# Setup Reddit API (read-only mode)
reddit = praw.Reddit(
    client_id="eRvXnNKoa6pKobGhmszyRg",  # <-- Replace with your actual client_id
    client_secret="",
    user_agent="rvcircle-reddit-chatbot"
)

def fetch_rvce_posts(limit=10):
    subreddit = reddit.subreddit("rvce")
    posts = []
    for post in subreddit.new(limit=limit):
        post_data = {
            "title": post.title,
            "content": post.selftext,
            "comments": [c.body for c in post.comments[:5] if hasattr(c, "body")],
        }
        posts.append(post_data)
    return posts

@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        user_question = data.get("question", "")

        # Get Reddit context
        reddit_posts = fetch_rvce_posts()
        context = "\n\n".join([
            f"Title: {p['title']}\nContent: {p['content']}\nComments: {', '.join(p['comments'])}"
            for p in reddit_posts
        ])

        # Construct prompt
        prompt = f"""
You are a highly responsible, respectful, and safety-focused AI chatbot for the RVCircle platform. 
You only use publicly available Reddit discussions from r/rvce to answer questions from students.

Your behavior must follow these principles:
- Be polite, neutral, and informative.
- Never assume or speculate. Only use data from the Reddit context.
- Avoid sharing or reinforcing any controversial, offensive, or negative opinions.
- If a question asks for something inappropriate, unsafe, or unavailable in the Reddit data, respond with a polite message like:
  "Sorry, I couldn't find any verified information about that topic in the Reddit posts I've seen."

Here is the user’s question:
{user_question}

And here is the Reddit context you may use:
{context}

Provide a respectful, non-toxic, safe response:
"""


        # Get response from MetaAI
        response = ai.prompt(message=prompt)
        return jsonify({ "answer": response.get("message", "Sorry, no answer found.") })

    except Exception as e:
        print("❌ Chatbot Error:", e)
        return jsonify({ "error": str(e) }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
