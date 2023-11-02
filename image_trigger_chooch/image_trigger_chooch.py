import base64
import datetime
import functions_framework
import google.cloud.bigquery as bq
import io
import json
import os
import requests
import urllib.request

from flask import jsonify

@functions_framework.http
def image_trigger_chooch(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'user_id' in request_json:
        user_id = request_json['user_id']
    elif request_args and 'user_id' in request_args:
        user_id = request_args['user_id']
    else:
        user_id = '1'

    if request_json and 'image_id' in request_json:
        image_id = request_json['image_id']
    elif request_args and 'image_id' in request_args:
        image_id = request_args['image_id']
    else:
        return jsonify({})

    if request_json and 'date_time' in request_json:
        date_time = request_json['date_time']
    elif request_args and 'date_time' in request_args:
        date_time = request_args['date_time']
    else:
        date_time = datetime.datetime.utcnow().isoformat()

    if request_json and 'image_url' in request_json:
        image_url = request_json['image_url']
    elif request_args and 'image_url' in request_args:
        image_url = request_args['image_url']

    byte_content = None
    if image_url:
        with urllib.request.urlopen(image_url) as response:
            byte_content = response.read()

    if not byte_content:
        if request_json and 'image_base64' in request_json:
            image_base64 = request_json['image_base64']
        elif request_args and 'image_base64' in request_args:
            image_base64 = request_args['image_base64']

        if not image_base64:
            return jsonify({})

        byte_content = base64.b64decode(image_base64)

    # 1. Query the content
    parameters = dict(
        parameters=dict(
            deep_inference=True,
            prompt="Describe the image in the greatest detail possible"
        ),
        model_id=model_id_image_chat
    )
    parameters_json =  json.dumps(parameters)
    payload = dict(data=parameters_json)
    file_param = dict(file=('image.jpg', io.BytesIO(byte_content)))

    # Chooch ImageChat-3 model_id
    model_id_image_chat = "chooch-image-chat-3"
    CHOOCH_API_KEY = os.getenv("CHOOCH_API_KEY") or "CHOOCH_API_KEY"
    host_name = "https://chat-api.chooch.ai"
    url = f"{host_name}/predict?api_key={CHOOCH_API_KEY}"
    #-- url = f"{host_name}/predict_image_chat?api_key={CHOOCH_API_KEY}"
    description_response = requests.post(url, data=payload, files=file_param)
    description_json_data = json.loads(description_response.content)
    description = description_json_data["predictions"][0]["class_title"]

    client = bq.Client(project='gdg-demos')

    DESCRIPTION_QUERY = (
      "INSERT INTO `gdg-demos.images.images` (user_id, image_id, datetime, description)"
      "VALUES ('@user_id', '@image_id', '@date_time', '@description';"
    )
    description_job_config = bq.QueryJobConfig(
      query_parameters=[
        bq.ScalarQueryParameter("user_id", "STRING", user_id),
        bq.ScalarQueryParameter("image_id", "STRING", image_id),
        bq.ScalarQueryParameter("date_time", "STRING", date_time),
        bq.ScalarQueryParameter("description", "STRING", description),
      ]
    )
    client.query(DESCRIPTION_QUERY, job_config=description_job_config)

    # 1. Query tags
    parameters = dict(
        parameters=dict(
            deep_inference=True,
            prompt="Identify a list of objects and entities on this photo. List as many as you can separated by commas without extra explanations in decreased importance and confidence order."
        ),
        model_id=model_id_image_chat
    )
    parameters_json =  json.dumps(parameters)
    tags_payload = dict(data=parameters_json)
    file_param = dict(file=('image.jpg', io.BytesIO(byte_content)))
    tags_response = requests.put(url, data=tags_payload, files=file_param)
    tags_json_data = json.loads(tags_response.content)
    tags = tags_json_data["prediction_keywords"]

    TAGS_QUERY = "INSERT INTO `gdg-demos.images.tags` (image_id, tag, priority) VALUES "
    query_parameters=[]
    for index, tag in enumerate(tags):
      TAGS_QUERY += f"('@image_id_{index}', '{tag}', {index})"
      if index == len(tags) - 1:
        TAGS_QUERY += ";"
      else:
        TAGS_QUERY += ", "

      query_parameters.append(bq.ScalarQueryParameter(f"image_id_{index}", "STRING", image_id))

    tags_job_config = bq.QueryJobConfig(query_parameters=query_parameters)
    client.query(TAGS_QUERY, job_config=tags_job_config)

    return 'OK'
