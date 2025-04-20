# Google Drive Automation Snippets

This repo contains a collection of random automation scripts and experiments using the Google Drive API. Each file demonstrates standalone use cases to showcase experience working with Google APIs. Nothing here is connected—just isolated examples.

---

### Setup

Install requirements:

```bash
pip install -r requirements.txt
```

### Run checks

```bash
make lint         # Run linter
make type-check   # Run mypy
make test         # Run tests
```

###  Google Consent Screen & GCP Setup

	1.	Create a project on Google Cloud Console
	2.	Set up the OAuth consent screen
	3.	Create OAuth credentials and download credentials.json
	4.	Configure your gcloud CLI:


```bash
gcloud config set project [PROJECT_NAME]
``` 

### Authenticate with Application Default Credentials

Basic scopes (Drive + Cloud Platform):

```bash
gcloud auth application-default login \
  --client-id-file="credentials.json" \
  --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive"
```


Extended scopes (Drive + Gmail):

```bash
gcloud auth application-default login \
  --client-id-file="credentials.json" \
  --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/gmail.readonly"
```

More info:

https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login




Built by Patricia Osorio