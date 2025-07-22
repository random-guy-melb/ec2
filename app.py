from flask import Flask, request, jsonify
import logging
import json
import requests
import random
import time
import re
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def replace_name_tags(text):
    return re.sub(r"<@([A-Z0-9]+)>", "@user", text).strip()

def remove_misc(text):
    return re.sub(r"<!.*?>", " ", text)

def clean_data(text):
    text = replace_name_tags(text)
    return remove_misc(text)

def unix_ts(dt):
    return int(dt.timestamp())

def make_request_with_backoff(client, url, params, max_retries=5, initial_backoff=1):
    for attempt in range(max_retries):
        try:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                if attempt < max_retries - 1:
                    backoff_time = initial_backoff * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(backoff_time)
                else:
                    return None
            else:
                return None
        except requests.RequestException:
            return None

def fetch_users(client):
    users_url = 'https://slack.com/api/users.list'
    users = {}
    cursor = None
    while True:
        params = {'limit': 200}
        if cursor:
            params['cursor'] = cursor
        data = make_request_with_backoff(client, users_url, params)
        if data and data['ok']:
            for member in data['members']:
                try:
                    users[member['id']] = member['real_name']
                except:
                    users[member['id']] = member['profile']['real_name']
            if data.get('response_metadata', {}).get('next_cursor'):
                cursor = data['response_metadata']['next_cursor']
            else:
                break
        else:
            break
    return users

def fetch_channels(client):
    channels_url = 'https://slack.com/api/conversations.list'
    channels = {}
    cursor = None
    while True:
        params = {'limit': 200, 'types': 'public_channel,private_channel'}
        if cursor:
            params['cursor'] = cursor
        data = make_request_with_backoff(client, channels_url, params)
        if data and data['ok']:
            for channel in data['channels']:
                channels[channel['id']] = channel['name']
            if data.get('response_metadata', {}).get('next_cursor'):
                cursor = data['response_metadata']['next_cursor']
            else:
                break
        else:
            break
    return channels

def fetch_usergroups(client):
    usergroups_url = 'https://slack.com/api/usergroups.list'
    usergroups = {}
    data = make_request_with_backoff(client, usergroups_url, {})
    if data and data['ok']:
        for group in data['usergroups']:
            usergroups[group['id']] = group['handle']
    return usergroups

def resolve_names(text, users, channels, usergroups):
    def replace_id(match):
        full_match = match.group(0)
        if match.group(1) == '@':
            user_id = match.group(2)
            return f"@{users.get(user_id, user_id)}"
        elif match.group(1) == '#':
            channel_id = match.group(2)
            return f"#{channels.get(channel_id, channel_id)}"
        elif match.group(1) == '!':
            group_id = match.group(2)
            id = group_id.split("^")[1].strip()
            return f"@{usergroups.get(id, id)}"
        else:
            return full_match
    pattern = r'<([@#!])(U[A-Z0-9]+|C[A-Z0-9]+|subteam\^S[0-9A-Z]+)>'
    return re.sub(pattern, replace_id, text)

def fetch_replies(client, channel_id, thread_ts):
    replies_url = "https://slack.com/api/conversations.replies"
    replies_params = {
        "channel": channel_id,
        "ts": thread_ts
    }
    data = make_request_with_backoff(client, replies_url, replies_params)
    if data and data["ok"]:
        return data["messages"][1:]
    return []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/fetch-slack-messages', methods=['POST'])
def fetch_slack_messages():
    """Main endpoint to fetch Slack messages"""
    try:
        req_body = request.get_json()
        if not req_body:
            return jsonify({"error": "Invalid body"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    # Required params: token, channel_id, start_date, end_date
    token = req_body.get('token')
    channel_id = req_body.get('channel_id')
    start_date_str = req_body.get('start_date')
    end_date_str = req_body.get('end_date')

    if not token or not channel_id or not start_date_str or not end_date_str:
        return jsonify({"error": "Missing required parameter. Required: token, channel_id, start_date, end_date"}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except Exception as e:
        return jsonify({"error": "Date format must be YYYY-MM-DD"}), 400

    oldest = unix_ts(start_date)
    latest = unix_ts(end_date)

    base_url = "https://slack.com/api/conversations.history"
    params = {
        "channel": channel_id,
        "oldest": oldest,
        "latest": latest,
        "limit": 100
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    session = requests.Session()
    session.headers.update(headers)
    all_threads = []

    # Fetch metadata
    logger.info("Fetching users, channels, and usergroups...")
    users = fetch_users(session)
    channels = fetch_channels(session)
    usergroups = fetch_usergroups(session)

    # Fetch messages
    logger.info(f"Fetching messages from channel {channel_id} between {start_date_str} and {end_date_str}")
    while True:
        data = make_request_with_backoff(session, base_url, params)
        if data and data["ok"]:
            for message in data["messages"]:
                try:
                    user = message["user"]
                except:
                    user = message.get("subtype", "unknown")
                if user != "USLACKBOT" and "bot" not in user.lower():
                    thread = [message]
                    if message.get("thread_ts"):
                        replies = fetch_replies(session, channel_id, message["ts"])
                        if replies:
                            thread.extend(replies)
                    all_threads.append(thread)
            if data.get("has_more"):
                params["latest"] = data["messages"][-1]["ts"]
            else:
                break
        else:
            logger.error("Failed to fetch messages")
            break

    # Prepare output (JSON)
    results = []
    for thread in all_threads:
        user_id = thread[0].get('user', 'Unknown')
        user_name = users.get(user_id, user_id)
        clean_thread = resolve_names(thread[0]['text'], users, channels, usergroups)
        date = datetime.fromtimestamp(float(thread[0]['ts'])).strftime("%d/%m/%Y")
        thread_text = f"{user_name} | {date}: {clean_thread}"
        replies_array = []
        if len(thread) > 1:
            for reply in thread[1:]:
                reply_user_id = reply.get('user', 'Unknown')
                reply_user_name = users.get(reply_user_id, reply_user_id)
                clean_reply = resolve_names(reply['text'], users, channels, usergroups)
                replies_array.append({
                    "user": reply_user_name,
                    "date": datetime.fromtimestamp(float(reply['ts'])).strftime("%d/%m/%Y"),
                    "text": clean_reply
                })
        results.append({
            "thread": thread_text,
            "replies": replies_array,
            "date": date,
            "timestamp": thread[0]['ts']
        })
    
    logger.info(f"Successfully fetched {len(results)} threads")
    return jsonify(results), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    # For production, use gunicorn instead:
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
