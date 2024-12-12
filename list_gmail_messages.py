import pandas as pd
import google.auth
from googleapiclient.discovery import build

def list_messages(service, query, max_results=10):

    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            print("No messages found.")
            return []
        
        data = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])

            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            snippet = msg.get('snippet', 'No Snippet')

            data.append({
                'Message ID': message['id'],
                'Subject': subject,
                'Sender': sender,
                'Date': date,
                'Snippet': snippet
            })
        
        df = pd.DataFrame(data)
        print(df)
        return df     
    
    except Exception as e:
        print(f"An error ocurred: {e}")
        return []

def get_message_details(service, message_id):
    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'
    ).execute()

    payload = message['payload']
    headers = payload['headers']

    print("\nMessage Details:")
    for header in headers:
        if header['name'] in ['From', 'To', 'Subject', 'Date']:
            print(f"{header['name']}: {header['value']}")

    print("\nSnippet:")
    print(message['snippet'])

if __name__ == "__main__":
    creds, _ = google.auth.default()
    gmail_service = build("gmail", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    df = list_messages(gmail_service, query="from:idealista", max_results=50)