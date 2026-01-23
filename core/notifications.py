import requests
import json

def send_push_notification(token, title, body, data=None):
    """
    Sends a push notification to a specific Expo push token.
    """
    if not token:
        return # User has no token, skip

    url = "https://exp.host/--/api/v2/push/send"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default",
        "data": data or {}, # Optional data payload (e.g., to open a specific chat)
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"✅ Notification sent to {token}")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")