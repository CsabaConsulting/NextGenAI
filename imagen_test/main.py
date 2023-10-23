import base64
import functions_framework
import vertexai

from flask import jsonify
from vertexai.vision_models import ImageQnAModel, ImageTextModel, Image

PROJECT_ID = "gdg-demos"
LOCATION = "us-central1"

@functions_framework.http
def imagen_test(request):
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

    if request_json and 'image' in request_json:
        image_b64 = request_json['image']
    elif request_args and 'image' in request_args:
        image_b64 = request_args['image']
    else:
        image_b64 = None

    if not image_b64:
        return jsonify(dict(data=[]))

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = ImageQnAModel.from_pretrained("imagetext@001")

    image_binary = base64.b64decode(image_b64)
    image = Image(image_binary)
    answers = model.ask_question(
        image=image,
        question="Describe what is on the photo in great detail, be very verbose",
        number_of_results=3,
    )
    return jsonify(dict(data=answers))
