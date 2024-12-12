### Install requirements:

pip install -r requirements.txt

#### Test:

make lint
make type-check
make test

#### Google Consent Screen

App Domain
http://localhost
http://localhost/privacy-policy
http://localhost/terms-of-service

ProjectID
clean-tower-442813-k8

GCloud
set up user

set up project
gcloud config set project [PROJECT_NAME]


Gcloud commands
https://cloud.google.com/sdk/gcloud/reference/auth/list


Default Auth credentials Login:

gcloud auth application-default login \
    --client-id-file="credentials.json" \
    --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/gmail.readonly"


gcloud auth application-default login \
    --client-id-file="credentials.json" \
    --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive"


clear cache data
rm -rf ~/.cache
