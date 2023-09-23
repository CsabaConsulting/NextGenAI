import functions_framework
import google.cloud.bigquery as bq
import google.generativeai as palm
import requests
from datetime import date
from flask import jsonify

@functions_framework.http
def journal_entries(request):
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

    if request_json and 'tags' in request_json:
        tags = request_json['tags']
    elif request_args and 'tags' in request_args:
        tags = request_args['tags']
    else:
        return jsonify({})

    client = bq.Client(project='gdg-demos')

    if request_json and 'prompt' in request_json:
        prompt = request_json['prompt']
    elif request_args and 'prompt' in request_args:
        prompt = request_args['prompt']
    else:
        prompt = "Given the following images taken about an experience: {} generate a funny poem about the experience in the style of Shakespeare"

    MAKERSUITE_API_KEY = "***"
    palm.configure(api_key=MAKERSUITE_API_KEY)
    models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
    model = models[0].name

    journal_entries = []
    for tag in tags:
      QUERY = (
        "SELECT description FROM `gdg-demos.images.images` AS im "
        "JOIN `gdg-demos.images.tags` AS tg ON im.image_id = tg.image_id "
        "WHERE im.user_id = @user_id AND datetime BETWEEN @start_date AND @end_date "
        "AND tg.tag = @tag ORDER BY im.datetime;"
      )
      job_config = bq.QueryJobConfig(
        query_parameters=[
          bq.ScalarQueryParameter("user_id", "STRING", user_id),
          bq.ScalarQueryParameter("start_date", "STRING", start_date),
          bq.ScalarQueryParameter("end_date", "STRING", end_date),
          bq.ScalarQueryParameter("tag", "STRING", tag),
        ]
      )
      query_job = client.query(QUERY, job_config=job_config)
      rows = query_job.result()
      image_descriptions = ""
      for index, row in enumerate(rows):
        image_descriptions += "{}. {}".format(index, row.description)

      prompt = prompt.format(image_descriptions)

      # palm2_url = "https://generativelanguage.googleapis.com/v1beta3/models/text-bison-001:generateText"
      # params = dict(prompt=dict(text=prompt))
      # headers = {
      #     "Content-Type": "application/json",
      #     "x-goog-api-key": MAKERSUITE_API_KEY,
      # }
      # llm_response = requests.get(url=palm2_url, data=PARAMS, headers=headers, verify=False)
      # data = llm_response.json()

      completion = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0.5,
        max_output_tokens=800,
      )

      journal_entries.append(
        dict(
          tag=tag,
          entry=completion.result
        )
      )

    return jsonify(dict(data=journal_entries))

