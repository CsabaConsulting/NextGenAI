import functions_framework

@functions_framework.http
def hello_http(request):
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

    image_base64 = None
    if image_url:
        with urllib.request.urlopen(image_url) as response:
            byte_content = response.read()
            base64_bytes = b64encode(byte_content)
            image_base64 = base64_bytes.decode("utf-8")

    if not image_base64:
        if request_json and 'image_base64' in request_json:
            image_base64 = request_json['image_base64']
        elif request_args and 'image_base64' in request_args:
            image_base64 = request_args['image_base64']

    if not image_base64:
        return jsonify({})

    # Chooch ImageChat-3 model_id
    model_id_image_chat_pt = "ad420c2a-d565-48eb-b963-a8297a0e4000"
    CHOOCH_API_KEY = "***"
    url = f"https://apiv2.chooch.ai/predict?api_key={CHOOCH_API_KEY}"

    description_payload = dict(
        base64str=image_base64,
        model_id=model_id_image_chat_pt,
        parameters=dict(
            deep_inference=True,
            prompt="Describe the image in the greatest detail possible"
        ),
    )

    description_response = requests.put(url, data=json.dumps(description_payload))
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

    tags_payload = dict(
        base64str=image_base64,
        model_id=model_id_image_chat_pt,
        parameters=dict(
            deep_inference=True,
            prompt="Identify a list of objects and entities on this photo. List as many as you can separated by commas without extra explanations in decreased importance and confidence order."
        ),
    )

    tags_response = requests.put(url, data=json.dumps(tags_payload))
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
