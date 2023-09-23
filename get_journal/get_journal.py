import asyncio
import functions_framework
import google.cloud.bigquery as bq
import google.generativeai as palm
import requests
from datetime import date
from flask import jsonify

async def llm_result(model, prompt, temperature, max_output_tokens, tag, task_type):
    completion = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    return dict(tag=tag, task_type=task_type, text=completion.result.strip())

async def journal_entry(user_id, start_date, end_date, tag, model, title_prompt, journal_prompt, temperature):
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
    client = bq.Client(project='gdg-demos')
    query_job = client.query(QUERY, job_config=job_config)
    rows = query_job.result()
    if not rows:
        return {}

    image_descriptions = ""
    for index, row in enumerate(rows):
        image_descriptions += "{}. {}".format(index, row.description)

    tasks = [
        llm_result(model, title_prompt.format(image_descriptions), temperature, 800, tag, "title"),
        llm_result(model, journal_prompt.format(image_descriptions), temperature, 800, tag, "journal")
    ]
    tasks_outputs = await asyncio.gather(*tasks)
    journal_entry = dict(tag=tag, title="", entry="")
    for task_output in tasks_outputs:
        if task_output["task_type"] == "title":
            journal_entry["title"] = task_output["text"]
        elif task_output["task_type"] == "journal":
            journal_entry["entry"] = task_output["text"]

    return journal_entry

async def journal_entries_core(request):
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

    if request_json and 'title_prompt' in request_json:
        title_prompt = request_json['title_prompt']
    elif request_args and 'title_prompt' in request_args:
        title_prompt = request_args['title_prompt']
    else:
        title_prompt = "Descriptions of images taken of a journey: {}. Given these images generate a short, one line journal entry title"

    if request_json and 'journal_prompt' in request_json:
        journal_prompt = request_json['journal_prompt']
    elif request_args and 'journal_prompt' in request_args:
        journal_prompt = request_args['journal_prompt']
    else:
        journal_prompt = "Descriptions of images taken of a journey: {}. Given these images generate a journal entry about the experiences depicted. Try to not recite the image descriptions verbatim."

    if request_json and 'temperature' in request_json:
        temperature = request_json['temperature']
    elif request_args and 'temperature' in request_args:
        temperature = request_args['temperature']
    else:
        temperature = 0.2

    MAKERSUITE_API_KEY = "***"
    palm.configure(api_key=MAKERSUITE_API_KEY)
    models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
    model = models[0].name

    journal_entries = []
    tasks = []
    for tag in tags:
        tasks.append(journal_entry(user_id, start_date, end_date, tag, model, title_prompt, journal_prompt, temperature))

    tasks_outputs = await asyncio.gather(*tasks)
    for task_output in tasks_outputs:
        if task_output:
            journal_entries.append(task_output)

    return jsonify(dict(data=journal_entries))

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
    return asyncio.run(journal_entries_core(request))
