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

    if request_json and 'image_id' in request_json:
        image_id = request_json['image_id']
    elif request_args and 'image_id' in request_args:
        image_id = request_args['image_id']
    else:
        return jsonify({})

    image_file = None
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
    url = "https://apiv2.chooch.ai/predict?api_key={}".format(api_key)

    description_payload = dict(
        base64str=base64_string,
        model_id=model_id_image_chat_pt,
        parameters=dict(
            deep_inference=True,
            prompt=""
        ),
    )

    description_response = requests.put(url, data=json.dumps(description_payload))
    description_json_data = json.loads(description_response.content)
    description = description_json_data["predictions"][0]["class_title"]

    tags_payload = dict(
        base64str=base64_string,
        model_id=model_id_image_chat_pt,
        parameters=dict(
            deep_inference=True,
            prompt="Identify a list of objects and entities on this photo. List as many as you can separated by commas without extra explanations in decreased importance and confidence order."
        ),
    )

    tags_response = requests.put(url, data=json.dumps(tags_payload))
    tags_json_data = json.loads(tags_response.content)
    tags = tags_json_data["prediction_keywords"]


    return 'Hello {}!'.format(name)
