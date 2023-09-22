import functions_framework
import google.cloud.bigquery as bq
from datetime import date
from flask import jsonify

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

    if request_json and 'start_date' in request_json:
        start_date = request_json['start_date']
    elif request_args and 'start_date' in request_args:
        start_date = request_args['start_date']
    else:
        start_date = date.today().isoformat()

    if request_json and 'end_date' in request_json:
        end_date = request_json['end_date']
    elif request_args and 'end_date' in request_args:
        end_date = request_args['end_date']
    else:
        end_date = date.today().isoformat()

    print(start_date, end_date)

    client = bq.Client(project='gdg-demos')

    # Perform a query.
    QUERY = (
        "SELECT DISTINCT(tg.tag) AS tag FROM `gdg-demos.images.images` AS im "
        "JOIN `gdg-demos.images.tags` AS tg ON im.image_id = tg.image_id "
        "WHERE datetime BETWEEN '2023-09-19' AND '2023-09-20' ORDER BY tg.tag;"
    )
    query_job = client.query(QUERY)
    rows = query_job.result()  # Waits for query to finish
    tags = [row.tag for row in rows]
    return jsonify(tags)
