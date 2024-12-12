import re
import logging
import google.auth
from googleapiclient.discovery import build
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("googleapiclient").setLevel(logging.ERROR)

def get_application_statuses(drive_service, folder_ids):
    """
    Retrieves the application statuses for customers.
    :param drive_service: Google Drive API service instance.
    :param folder_ids: Dictionary mapping application stages to their Google Drive folder IDs.
    :return: List of customer statuses.
    """
    application_statuses = {}

    for status, top_folder_id in folder_ids.items():
        # Get batch folders in the top-level folder
        batch_folders = drive_service.files().list(
            q=f"'{top_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name, createdTime)"
        ).execute().get("files", [])

        for batch_folder in batch_folders:
            batch_name = batch_folder["name"]
            batch_id = batch_folder["id"]
            batch_date = datetime.strptime(batch_folder["createdTime"], "%Y-%m-%dT%H:%M:%S.%fZ")

            # Get customer files in the batch folder
            customer_files = drive_service.files().list(
                q=f"'{batch_id}' in parents and trashed=false",
                fields="files(id, name)"
            ).execute().get("files", [])

            for file in customer_files:
                customer_name = re.sub(r"\.pdf$", "", file["name"]).strip()
                file_id = file["id"]

                # Update status if it's newer or not already present
                if (customer_name not in application_statuses or
                        batch_date > application_statuses[customer_name]["batch_date"]):
                    application_statuses[customer_name] = {
                        "customer": customer_name,
                        "file_id": file_id,
                        "status": status,
                        "batch": batch_name,
                        "batch_date": batch_date
                    }

    # Format result for output
    return [
        {k: v for k, v in details.items() if k != "batch_date"}
        for details in application_statuses.values()
    ]

if __name__ == "__main__":
    # Authenticate and initialize the Drive API
    creds, _ = google.auth.default()
    drive_service = build("drive", "v3", credentials=creds)

    # Top folder IDs for each stage
    folder_ids = {
        "received": "1U7p8_7PFjBCVUPwEiDJhmkjMQ7DmJv__",  # Example folder ID for "Application received"
        "processing": "1Fct5I9sXVklIx1KB-gVKnbmiN-657E74",  # Example folder ID for "Application processing"
        "processed": "1L70ZQBvWzarM0SH23upvqzKm0MhFjbJO"  # Example folder ID for "Application processed"
    }

    statuses = get_application_statuses(drive_service, folder_ids)

    if statuses:
        for entry in statuses:
            print(f"{entry['customer']} {entry['batch']} status: {entry['status']}")
    else:
        logging.warning("No customer files found.")