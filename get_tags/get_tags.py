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
    "SELECT im.image_id, tg.tag, tg.priority FROM `gdg-demos.images.images` AS im "
    "JOIN `gdg-demos.images.tags` AS tg ON im.image_id = tg.image_id "
    "WHERE im.user_id = @user_id AND datetime BETWEEN @start_date AND @end_date "
    "GROUP BY im.image_id, tg.tag, tg.priority "
    "ORDER BY im.image_id, tg.priority;"
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
  tags = dict()
  all_tags = dict()
  for row in rows:
    if row.image_id not in tags:
      tags[row.image_id] = dict()

    tag_dict = tags[row.image_id]
    if row.tag not in tag_dict or row.tag in tag_dict and tag_dict[row.tag] > row.priority:
      tags[row.image_id][row.tag] = row.priority

    if row.tag not in all_tags or row.tag in all_tags and all_tags[row.tag] > row.priority:
      all_tags[row.tag] = row.priority

  tags_return = []
  for image_id in sorted(tags.keys()):
    tag_dict = tags[image_id]
    tag_tuples = [(tag, priority) for tag, priority in tags[image_id].items()]
    sorted_by_priority = sorted(tag_tuples, key=lambda tup: tup[1])
    tags_return.append(
      dict(
        image_id=image_id,
        tags=[tag_tuple[0] for tag_tuple in sorted_by_priority]
      )
    )

  tag_tuples = [(tag, priority) for tag, priority in all_tags.items()]
  sorted_by_priority = sorted(tag_tuples, key=lambda tup: tup[1])
  tags_return.append(
    dict(
      image_id="all_tags",
      tags=[tag_tuple[0] for tag_tuple in sorted_by_priority]
    )
  )

  return jsonify(tags_return)
