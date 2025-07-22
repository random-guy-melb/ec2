# Slack Messages Fetcher API Documentation

## Overview
This Flask API fetches messages from Slack channels within a specified date range, including thread replies.

## Base URL
```
http://YOUR_AZURE_VM_IP/
```

## Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running properly.

**Response:**
```json
{
    "status": "healthy"
}
```

### 2. Fetch Slack Messages
**POST** `/fetch-slack-messages`

Fetch messages from a Slack channel within a date range.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "token": "xoxb-your-slack-bot-token",
    "channel_id": "C1234567890",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

**Parameters:**
- `token` (required): Your Slack Bot User OAuth Token
- `channel_id` (required): The Slack channel ID
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format

**Response:**
```json
[
    {
        "thread": "John Doe | 15/01/2024: Hello team!",
        "replies": [
            {
                "user": "Jane Smith",
                "date": "15/01/2024",
                "text": "Hi John!"
            }
        ],
        "date": "15/01/2024",
        "timestamp": "1705344000.123456"
    }
]
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "Missing required parameter. Required: token, channel_id, start_date, end_date"
}
```

### 404 Not Found
```json
{
    "error": "Endpoint not found"
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error"
}
```

## Example Usage

### Using cURL:
```bash
curl -X POST http://YOUR_VM_IP/fetch-slack-messages \
  -H "Content-Type: application/json" \
  -d '{
    "token": "xoxb-your-token",
    "channel_id": "C1234567890",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### Using Python:
```python
import requests

url = "http://YOUR_VM_IP/fetch-slack-messages"
payload = {
    "token": "xoxb-your-token",
    "channel_id": "C1234567890",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}

response = requests.post(url, json=payload)
print(response.json())
```

## Slack Token Setup

1. Go to https://api.slack.com/apps
2. Create a new app or select existing one
3. Go to OAuth & Permissions
4. Add these Bot Token Scopes:
   - `channels:history`
   - `channels:read`
   - `groups:history`
   - `groups:read`
   - `users:read`
   - `usergroups:read`
5. Install the app to your workspace
6. Copy the Bot User OAuth Token

## Rate Limiting
The API implements exponential backoff for Slack API rate limits. If you encounter rate limiting, the API will automatically retry with increasing delays.
