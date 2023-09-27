import os
import requests
from base64 import b64encode
# import urllib.request

# download file
# image_file_url = ""

image_file = "pexels-soly-moses-5897400.jpg"
# urllib.request.urlretrieve(image_file_url, "test_image.jpg")

# Execute `export GCP_AUTH_TOKEN=$(gcloud auth print-access-token)` in the Cloud Shell before try
GCP_AUTH_TOKEN = os.getenv("GCP_AUTH_TOKEN") or "GCP_AUTH_TOKEN"
ENCODING = "utf-8"
IMAGE_NAME = image_file

with open(IMAGE_NAME, "rb") as open_file:
    byte_content = open_file.read()

base64_bytes = b64encode(byte_content)
base64_string = base64_bytes.decode(ENCODING)

VQA_PROMPT = "Describe the content of the image in great detail"
RESPONSE_COUNT = 1
payload = {
  "instances": [
    {
      "prompt": VQA_PROMPT,
      "image": {
          "bytesBase64Encoded": base64_string
      }
    }
  ],
  "parameters": {
      "sampleCount": RESPONSE_COUNT
  }
}

url = "https://us-central1-aiplatform.googleapis.com/v1/projects/gdg-demos/locations/us-central1/publishers/google/models/imagetext:predict"
headers = {
    "Authorization": "Bearer {}".format(GCP_AUTH_TOKEN),
    "Accept": "application/json; charset=utf-8",
}
json_data = requests.post(url, headers=headers, json=payload) #, verify=False)
print(json_data.content)
