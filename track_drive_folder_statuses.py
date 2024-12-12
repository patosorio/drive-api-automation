import logging
from datetime import datetime
from collections import OrderedDict
import time
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Set Logging for error management
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("googleapiclient").setLevel(logging.ERROR)


def get_files(service, parent_id, fields="nextPageToken, files(id, name)"):
    """Fetch files in batches from parent folder ID"""
    files = []
    try:
        page_token = None
        while True:
            try:
                response = (
                    service.files()
                    .list(
                        q=f"'{parent_id}' in parents and trashed=false",
                        spaces="drive",
                        fields=fields,
                        pageToken=page_token,
                    )
                    .execute()
                )
                files.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                if page_token is None:
                    break
            except HttpError as error:
                logging.error(f"Error fetching files from parent ID {parent_id}: {error}")
                break
    except Exception as e:
        logging.critical(f"Unexpected error is get_files: {e}", exc_info=True)
        raise e  
    return files


def get_application_statuses(service, folder_ids):
    """Get application statuses across multiple folders"""
    application_statuses = OrderedDict()
    
    try:
        for folder_id in folder_ids:
            try: 
                folder_metadata = service.files().get(fileId=folder_id, fields="name").execute()
                folder_name = folder_metadata.get("name", "Unknown")
                status = folder_name.split()[-1].lower()
            except KeyError as e:
                logging.warning(f"KeyError while parsing folder data for ID {folder_id}: {e}")
                continue
            
            batches = get_files(service, folder_id) or []
            for batch in batches:
                try : 
                    applications = get_files(service, batch.get("id", "")) or []
                except KeyError as error:
                    logging.error(f"KeyError fetching applications from batch {batch}: {error}")
                    continue

                for application in applications:
                    try:
                        application_name = application["name"].split(".pdf")[0].strip().lower()
                        batch_date = datetime.strptime(batch.get("name", "").split(" ")[0], "%Y-%m-%d")

                        if application_name in application_statuses:
                            existing_date = application_statuses[application_name]["batch_date"]

                            if batch_date > existing_date:
                                application_statuses[application_name] = {
                                    "file_id": application.get("id"),
                                    "status": status,
                                    "batch": batch.get("name", "Unknown"),
                                    "batch_date": batch_date
                                }

                        else:
                            application_statuses[application_name] = {
                                "customer": application_name,
                                "file_id": application.get("id"),
                                "status": status,
                                "batch": batch.get("name", "Unknown"),
                                "batch_date": batch_date
                            }
                    except ValueError as e:
                        logging.warning(f"Error parsing batch date for batch {batch}: {e}")
                    except KeyError as e:
                        logging.warning(f"Missing expected data for application {application}: {e}")               
    except HttpError as error:
        logging.error(f"Error fetching folder metadata for ID {folder_id}: {error}")
    except Exception as e:
        logging.critical(f"Unexpected error in get_application_statuses: {e}", exc_info=True)
        raise e                    

    return [entry for entry in application_statuses.values()]


def main():

    creds, _ = google.auth.default()
    drive_service = build("drive", "v3", credentials=creds)

    folder_ids = [
        "1U7p8_7PFjBCVUPwEiDJhmkjMQ7DmJv__",
        "1Fct5I9sXVklIx1KB-gVKnbmiN-657E74",
        "1L70ZQBvWzarM0SH23upvqzKm0MhFjbJO"
    ]

    statuses = get_application_statuses(drive_service, folder_ids)

    if statuses:
        for entry in statuses:
            print(f"{entry['customer'].title()} {entry['batch']} status: {entry['status']}")
    else:
        logging.warning(f"No files found for folder ID {folder_ids}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"execution_time = {end_time - start_time} seconds.")