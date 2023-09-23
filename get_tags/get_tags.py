import functions_framework
import google.cloud.bigquery as bq
from datetime import date
from flask import jsonify

@functions_framework.http
def get_categories(request):
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

    client = bq.Client(project='gdg-demos')

    QUERY = (
      "SELECT im.image_id, tg.tag FROM `gdg-demos.images.images` AS im "
      "JOIN `gdg-demos.images.tags` AS tg ON im.image_id = tg.image_id "
      "WHERE im.user_id = @user_id AND datetime BETWEEN @start_date AND @end_date "
      "GROUP BY im.datetime, tg.tag, im.image_id "
      "ORDER BY im.datetime;"
    )
    job_config = bq.QueryJobConfig(
      query_parameters=[
        bq.ScalarQueryParameter("user_id", "STRING", user_id),
        bq.ScalarQueryParameter("start_date", "STRING", start_date),
        bq.ScalarQueryParameter("end_date", "STRING", end_date),
      ]
    )
    query_job = client.query(QUERY, job_config=job_config)
    rows = query_job.result()
    tags = list()
    all_tags = set()
    current_image_id = ""
    current_image = None
    for row in rows:
        if current_image_id == "" or current_image_id != row.image_id:
            if current_image_id != "":
                current_image["tags"] = sorted(list(current_image["tags"]))
                tags.append(current_image)

            current_image_id = row.image_id
            current_image = dict(
                image_id=current_image_id,
                tags=set({row.tag})
            )
        else:
            current_image["tags"].add(row.tag)

        all_tags.add(row.tag)

    if not tags or tags[-1]["image_id"] != current_image_id:
        current_image["tags"] = sorted(list(current_image["tags"]))
        tags.append(current_image)

    tags.append(
        dict(
            image_id="all_tags",
            tags=sorted(list(all_tags))
        )
    )

    return jsonify(tags)
