import requests


def requestqanything(question):
    requesturl = "http://10.25.10.154:10101/api/local_doc_qa/local_doc_chat"
    requestdata = {
        "user_id": "zzp",
        "kb_ids": ["KB26198140e6c243e1931550d1120c017c"],
        "history": [],
        "question": question,
        "streaming": False,
        "networking": False,
        "product_source": "saas"
    }
    try:
        response = requests.post(requesturl, json=requestdata)
        if response.status_code == 200:
            content = response.json()
            return {
                'status': True,
                'message': {
                    'answer': content['history'][0][1],
                    'source': [{'content': item['content'], 'filename': item['file_name']} for item in
                               content['source_documents']]
                }
            }
        else:
            return {
                'status': False,
                'message': response.text
            }
    except Exception as e:
        return {
            'status': False,
            'message': str(e.args())
        }


test_content = requestqanything('减速器齿轮检查要求是什么？')
test_source = test_content['message']['source']
filenames = [item['filename'] for item in test_source]




import random
from http import HTTPStatus
import dashscope

dashscope.api_key="sk-3d3b31396f2f4576a78c901e0fcafc03"
def call_with_messages():
    messages = [
        {'role': 'user', 'content': '用萝卜、土豆、茄子做饭，给我个菜谱'}]
    response = dashscope.Generation.call(
        'qwen1.5-14b-chat',
        messages=messages,
        # set the random seed, optional, default to 1234 if not set
        seed=random.randint(1, 10000),
        result_format='message',  # set the result to be "message" format.
    )
    if response.status_code == HTTPStatus.OK:
        print(response)
    else:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))


if __name__ == '__main__':
    call_with_messages()














if __name__ == "__main__":
    questionlist=[]
    answerlist=[]
    for index, question in enumerate(questionlist):
        print(f'-------current index: {index}-----------')
        answercontent = requestqanything(question)
        if answercontent['status']:
            answerlist.append(answercontent['message'])
