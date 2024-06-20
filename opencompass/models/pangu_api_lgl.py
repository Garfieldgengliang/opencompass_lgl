import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Union
import http.client
import ssl
import requests
import json

from opencompass.utils.prompt import PromptList

from opencompass.models.base_api import BaseAPIModel

PromptType = Union[PromptList, str]


class PanGu(BaseAPIModel):
    """Model wrapper around PanGu.

    Args:
        path (str): The name of Pangu model.
            e.g. `pangu`
        access_key (str): provided access_key
        secret_key (str): secretkey in order to obtain access_token
        url (str): provide url for requests
        token_url (str): url of token server
        project_name (str): project name for generate the token
        query_per_second (int): The maximum queries allowed per second
            between two consecutive calls of the API. Defaults to 1.
        max_seq_len (int): Unused here.
        meta_template (Dict, optional): The model's meta prompt
            template if needed, in case the requirement of injecting or
            wrapping of any meta instructions.
        retry (int): Number of retires if the API call fails. Defaults to 2.
    """

    def __init__(
        self,
        path: str,
        url: str,
        query_per_second: int = 1,
        max_seq_len: int = 2048,
        meta_template: Optional[Dict] = None,
        retry: int = 10,
    ):
        super().__init__(path=path,
                         max_seq_len=max_seq_len,
                         query_per_second=query_per_second,
                         meta_template=meta_template,
                         retry=retry)

        self.url = url
        self.model = path


    def generate(
        self,
        inputs: List[PromptType],
        max_out_len: int = 4096,
    ) -> List[str]:
        """Generate results given a list of inputs.

        Args:
            inputs (List[PromptType]): A list of strings or PromptDicts.
                The PromptDict should be organized in OpenCompass'
                API format.
            max_out_len (int): The maximum length of the output.

        Returns:
            List[str]: A list of generated strings.
        """
        '''
        with ThreadPoolExecutor() as executor:
            results = list(
                executor.map(self._generate, inputs,
                             [max_out_len] * len(inputs)))
        self.flush()
        '''
        results = []
        for input_i in inputs:
            result = self._generate(input_i, max_out_len)
            time.sleep(0.2)
            results.append(result)
        return results


    def _generate(
        self,
        input: PromptType,
        max_out_len: int = 4096,
    ) -> str:
        """Generate results given an input.

        Args:
            inputs (PromptType): A string or PromptDict.
                The PromptDict should be organized in OpenCompass'
                API format.
            max_out_len (int): The maximum length of the output.

        Returns:
            str: The generated string.
        """
        assert isinstance(input, (str, PromptList))

        if isinstance(input, str):
            messages = [{'role': 'user', 'content': input}]
        else:
            messages = []
            for item in input:
                msg = {'content': item['prompt']}
                if item['role'] == 'HUMAN':
                    msg['role'] = 'user'
                elif item['role'] == 'BOT':
                    msg['role'] = 'system'

                messages.append(msg)

        # print('input message, ' , messages)
        data = {'messages': messages,
                'user': 'Jack',
                "max_tokens": 40960,
                "temperature": 0.1,
                "n": 1,
                "stream": False}

        # headers = {
        #     'Content-Type': 'application/json',
        #     # 'X-Auth-Token': 'MIIFHgYJKoZIhvcNAQcCoIIFDzCCBQsCAQExDTALBglghkgBZQMEAgEwggLsBgkqhkiG9w0BBwGgggLdBIIC2XsidG9rZW4iOnsiZXhwaXJlc19hdCI6IjIwMjQtMDUtMTZUMDE6NTU6MjguMDkwMDAwWiIsIm1ldGhvZHMiOlsicGFzc3dvcmQiXSwiY2F0YWxvZyI6W10sInJvbGVzIjpbeyJuYW1lIjoiYXBwcm92X2FkbSIsImlkIjoiMWZkYmFlZmM4ZmE2NDkyODkwOGU1M2NkMDYxYmE0NWMifSx7Im5hbWUiOiJ2ZGNfYWRtIiwiaWQiOiI5MGM0OGFhYzIyZmI0ODE2OWM2NmNkNGI1OWFlZTk4OSJ9LHsibmFtZSI6InRlX2FkbWluIiwiaWQiOiJmYTE2M2VmZWRiNTc3ZjU1MGIxOWMwNWE2MzhkZGNkNiJ9LHsibmFtZSI6InRhZ19hZG0iLCJpZCI6ImFmODRjMzFkMjhiZDQ1ZDA4YzRiM2U1ZTM3ZGMyMTE5In0seyJuYW1lIjoidmRjX293bmVyIiwiaWQiOiJmYTE2M2VmZWRiNTc3ZjU1MGIxOWMwNWE4NDZkZGNlMSJ9XSwicHJvamVjdCI6eyJkb21haW4iOnsibmFtZSI6InBhbmd1bG0iLCJpZCI6Ijk1MzYwNTg4MzZhNDQ1NjZhNTcyOGRmYmZiY2Y4MDZhIn0sIm5hbWUiOiJjbi1zaF9wYW5ndWxhcmdlbW9kZWxzIiwiaWQiOiJkYTZjZjJlMmQzNjM0ZGU4YTYxMGIwMmNmM2UwZjIxMSJ9LCJpc3N1ZWRfYXQiOiIyMDI0LTA1LTE1VDAxOjU1OjI4LjA5MDAwMFoiLCJ1c2VyIjp7ImRvbWFpbiI6eyJuYW1lIjoicGFuZ3VsbSIsImlkIjoiOTUzNjA1ODgzNmE0NDU2NmE1NzI4ZGZiZmJjZjgwNmEifSwibmFtZSI6InBhbmd1bG0iLCJpZCI6ImRmMjExMjY0ZjE2MTQyNDJiOTk0MDBjNzdmMjMxM2FkIn19fTGCAgUwggIBAgEBMFwwVjELMAkGA1UEBhMCQ04xCzAJBgNVBAgMAnNjMQswCQYDVQQHDAJjZDELMAkGA1UECgwCSFcxEDAOBgNVBAsMB0Nsb3VkQlUxDjAMBgNVBAMMBXRva2VuAgIQADALBglghkgBZQMEAgEwDQYJKoZIhvcNAQEBBQAEggGASWtHXpzuMdgDpDNOjBvmUxgHCeVk9kKta1t-zN+OTR7puokpAuRtH2eMM-ad7hynIX8i2-zDdo0ONKE4ydmuW+jLI9xCIEka0d4g0nH9rBuESv2YF83rEvs-HoI777OxuQf76cmCdO48GpYVLlXOB6uI7T7gv2rKPFX7yLdWNGK3L7JG3CnMtKZxKz0bgd9-azRTkt38pYiW8OHrf5peqnnHISVmWXyXActs80824uAkfLPXGFsBtsOdJILpQ2NarCKB00LleHn9adsIKFYkUyCU8W+qWsolzqTIKmxnXRSPVmUJ-Yrf+n91IuJc6sZLYuNwSrk19xIEV8imhHnBuJ07saNYEH1Gc+tI0ijEjfEu5ionENjHpP4kSai4CgCXW9ONvHTx+YycpJgIdk-SdLjvdsVTiFUb6hbeT9jQ3utUhqY-9q5voowVCDoA43qNnSYR38ZNebLQnQD9fXI05d4pkPAHHOWmTG0H3r+-5BXhZeKB6lIEB+fnIesHFQts'
        # }

        # max_num_retries = 0
        # while max_num_retries < self.retry:

        '''
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        endpoint_lgl = '10.83.8.247'
        conn = http.client.HTTPSConnection(
            host=endpoint_lgl, context=context)
        '''

        payload_json = json.dumps(data)
        headers = {
            'Content-Type': 'application/json'
        }
        '''
        conn.request(method="POST",
                     url=self.url,
                     body=payload_json, headers=headers)

        response = conn.getresponse()
        # print('response code ', response.getcode())
        '''

        max_num_retries = 0
        while max_num_retries < self.retry:
            '''
            if response is None:
                print('Connection error, reconnect.')
                self.wait()
                continue

            if response.getcode() == 200:
                data = response.read()
                # pprint(data.decode("utf-8"))
                decoded_data = data.decode("utf-8")
                content = json.loads(decoded_data)['choices'][0]['message']['content']
                # print('success get response', content)
                return content

            if (response.getcode() != 200):
                print('Failed response with code ', response.getcode())
                # return ''
                time.sleep(1)
                continue
            '''
            self.acquire()

            response = requests.request(method="POST", url=self.url, data=payload_json, headers=headers, verify=False)
            self.release()
            if response.status_code == 200:
                # print(json.loads(response.text)["choices"][0]["message"]["content"])
                return json.loads(response.text)["choices"][0]["message"]["content"]

            else:
                print('-------------------')
                print("first request error. begin try angin")
                print(f"status_code: {response.status_code}, errormessage: {response.text}")
                print(f"data is: {json.dumps(data)}")
                time.sleep(0.5)

                response = requests.request(method="POST", url=self.url, data=payload_json, headers=headers,
                                            verify=False)
                if response.status_code == 200:
                    return json.loads(response.text)["choices"][0]["message"]["content"]
                else:
                    print('-------------------')
                    print("second request error. begin try angin")
                    print(f"status_code: {response.status_code}, errormessage: {response.text}")
                    print(f"data is: {json.dumps(data)}")
                    time.sleep(2)
                    response = requests.request(method="POST", url=self.url, data=payload_json, headers=headers,
                                                verify=False)
                    if response.status_code == 200:
                        return json.loads(response.text)["choices"][0]["message"]["content"]
                    else:
                        print('-------------------')
                        print("third request error. begin try angin")
                        print(f"status_code: {response.status_code}, errormessage: {response.text}")
                        print(f"data is: {json.dumps(data)}")
                        time.sleep(10)

            max_num_retries += 1

        raise RuntimeError(response.status_code)




if __name__ == '__main__':
    import time
    start = time.time()
    model = PanGu(
        path='pangu',
        url = 'http://10.83.8.91:8080/v1/da6/deployments/3dc/chat/completions')
    #
    print(model.generate(["Follow the given examples and answer the question.\nName geometric shapes from their SVG paths.\n\nQ: This SVG path element <path d=\"M 31.00,73.00 L 32.00,59.00 L 44.00,50.00 L 49.00,41.00 L 64.00,37.00 L 71.00,55.00 L 64.00,76.00 L 52.00,61.00 L 31.00,73.00\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step.\nThis SVG path element contains \"M\" and \"L\" commands. M takes two parameters (x,y) and moves the current point to the coordinates (x,y). L takes two parameters (x,y) and draws a line from the previous coordinate to the new coordinate (x,y).\nThis path can be decomposed into 9 separate commands.\n(1) M 31.00,73.00: Move the current point to 31.00,73.00.\n(2) L 32.00,59.00: Create a line from 31.00,73.00 to 32.00,59.00.\n(3) L 44.00,50.00: Create a line from 32.00,59.00 to 44.00,50.00.\n(4) L 49.00,41.00: Create a line from 44.00,50.00 to 49.00,41.00.\n(5) L 64.00,37.00: Create a line from 49.00,41.00 to 64.00,37.00.\n(6) L 71.00,55.00: Create a line from 64.00,37.00 to 71.00,55.00.\n(7) L 64.00,76.00: Create a line from 71.00,55.00 to 64.00,76.00.\n(8) L 52.00,61.00: Create a line from 64.00,76.00 to 52.00,61.00.\n(9) L 31.00,73.00: Create a line from 52.00,61.00 to 31.00,73.00.\nThis SVG path starts at point 31.00,73.00, creates eight consecutive and touching lines, and then returns back its starting point, thereby creating an eight-sided shape. It does not have any curves or arches. \"octagon\" is the only eight-sided object on the list. So the answer is (F).\n\nQ: This SVG path element <path d=\"M 14.19,26.04 L 51.43,39.21 L 58.44,36.69 L 56.63,30.17 L 48.53,26.66 L 14.19,26.04\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step.\nThis SVG path element contains \"M\" and \"L\" commands. M takes two parameters (x,y) and moves the current point to the coordinates (x,y). L takes two parameters (x,y) and draws a line from the previous coordinate to the new coordinate (x,y).\nThis path can be decomposed into 6 separate commands.\n(1) M 14.19,26.04: Move the current point to 14.19,26.04.\n(2) L 51.43,39.21: Create a line from 14.19,26.04 to 51.43,39.21.\n(3) L 58.44,36.69: Create a line from 51.43,39.21 to 58.44,36.69.\n(4) L 56.63,30.17: Create a line from 58.44,36.69 to 56.63,30.17.\n(5) L 48.53,26.66: Create a line from 56.63,30.17 to 48.53,26.66.\n(6) L 14.19,26.04: Create a line from 48.53,26.66 to 14.19,26.04.\nThis SVG path starts at point 14.19,26.04, creates five consecutive and touching lines, and then returns back its starting point, thereby creating a five-sided shape. It does not have any curves or arches. \"pentagon\" is the only five-sided polygon on the list. So the answer is (G).\n\nQ: This SVG path element <path d=\"M 41.00,43.00 L 37.00,34.00 L 41.00,33.00 L 45.00,34.00 L 41.00,43.00\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step.\nThis SVG path element contains \"M\" and \"L\" commands. M takes two parameters (x,y) and moves the current point to the coordinates (x,y). L takes two parameters (x,y) and draws a line from the previous coordinate to the new coordinate (x,y).\nThis path can be decomposed into 5 separate commands.\n(1) M 41.00,43.00: Move the current point to 41.00,43.00.\n(2) L 37.00,34.00: Create a line from 41.00,43.00 to 37.00,34.00.\n(3) L 41.00,33.00: Create a line from 37.00,34.00 to 41.00,33.00.\n(4) L 45.00,34.00: Create a line from 41.00,33.00 to 45.00,34.00.\n(5) L 41.00,43.00: Create a line from 45.00,34.00 to 41.00,43.00.\nThis SVG path starts at point 41.00,43.00, creates four consecutive and touching lines, and then returns back its starting point, thereby creating a four-sided shape. \"kite\" and \"rectangle\" are the only two four-sided polygons on the list. So, we need to determine which one is the correct answer.\nA kite has two pairs of equal-length adjacent sides, whereas a rectangle has two pairs of equal-length alternate (opposite) sides. Now, let's check whether the two adjacent sides of this shape are equal.\nLength of side A: |A| = sqrt((41.00-37.00)^2 + (43.00-34.00)^2) = sqrt((4)^2 + (9)^2) = sqrt(16 + 81) = sqrt(97).\nLength of side B: |B| = sqrt((37.00-41.00)^2 + (34.00-33.00)^2)) = sqrt((4)^2 + (1)^2) = sqrt(16 + 1) = sqrt(17).\nLength of side C: |C| = sqrt((41.00-45.00)^2 + (33.00-34.00)^2)) = sqrt((-4)^2 + (-1)^2) = sqrt(16 + 1) = sqrt(17).\nLength of side D: |D| = sqrt((45.00-41.00)^2 + (34.00-43.00)^2)) = sqrt((4)^2 + (-9)^2) = sqrt(16 + 81) = sqrt(97).\nNote that |A| = |D| and |B| = |C|. Furthermore, A and D are adjacent and B and C are adjacent. Thus, this polygon has two pairs of equal-length adjacent sides and is \"kite\". So the answer is (D).\n\nQ: This SVG path element <path d=\"M 55.57,80.69 L 57.38,65.80 M 57.38,65.80 L 48.90,57.46 M 48.90,57.46 L 45.58,47.78 M 45.58,47.78 L 53.25,36.07 L 66.29,48.90 L 78.69,61.09 L 55.57,80.69\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step."]))
    end = time.time()
    print('Huawei time used ', end - start)


    '''

    import pandas as pd
    import time


    N2_basic_questions_file = pd.read_excel('C:\\Users\\ShuttleChaser\\Documents\\python_script\\LLM\\opencompass\\N2_basic_questions_lgl.xlsx')
    N2_questions = N2_basic_questions_file['语料']
    response_list = []
    for i in range(len(N2_questions)):
        current_response = model._generate(N2_questions[i])
        time.sleep(2)
        print(current_response)
        response_list.append(current_response)
    N2_basic_questions_file['华为回答'] = response_list
    N2_basic_questions_file.to_excel('C:\\Users\\ShuttleChaser\\Documents\\python_script\\LLM\\opencompass\\N2_basic_questions_huawei_answers.xlsx', index=False)

    # print(model._generate('写一个穿越到南宋的故事'))
    end = time.time()
    print('Huawei time used ', end - start)
    '''
