# 星火大模型推理服务接口文档(turing-spark-gpt)

## 接口说明

### 1 推理服务接口

#### 1.1 ws流式接口
##### 1.1.1 请求地址

**样例：`ws://127.0.0.1:9990/turing/v3/gpt` 

**说明：会话接口为webscoket流式接口，支持大模型结果实时输出**
##### 1.1.2 接口鉴权

  默认关闭，暂不做详细说明.
##### 1.3 接口请求
请求参数:
```json
# 参数构造示例如下
{
        "header": {
            "traceId": "SPARK_DEMO",
        },
        "parameter": {
            "chat": {
                "temperature": 0.5,
                "max_tokens": 1024, 
                "top_k":1
            }
        },
        "payload": {
            "lora":{
               "md5":"xxx",
               "url":"http://xxx"
            },
            "message": {
                # 如果想获取结合上下文的回答，需要开发者每次将历史问答信息一起传给服务端，如下示例
                # 注意：text里面的所有content内容加一起的tokens需要控制在8192以内，开发者如有较长对话需求，需要适当裁剪历史信息
                # 拼历史的时候，模型出来的结尾要加 <end>
                "text": [
                    {"role": "user", "content": "你是谁"}, # 用户的历史问题
                    {"role": "assistant", "content": "....."}, # AI的历史回答结果
                    # ....... 省略的历史对话
                    {"role": "user", "content": "你会做什么"}  # 最新的一条问题，如无需上下文，可只传最新一条问题
                ]
        }
    }
}
```

接口请求字段由三个部分组成：header，parameter, payload。 字段解释如下
**header部分:**

| 参数名称 | 类型   | 必传 | 参数要求 | 参数说明   |
| -------- | ------ | ---- | -------- | :--------- |
| traceId  | string | 是   |          | 流程跟踪ID |

**parameter.chat部分**:

| 参数名称     | 类型   | 必传 | 参数要求                   | 参数说明                                                     |
| ------------ | ------ | ---- | -------------------------- | :----------------------------------------------------------- |
| temperature  | float  | 否   | 取值为[0,1],默认为0.5      | 核采样阈值。用于决定结果随机性，取值越高随机性越强即相同的问题得到的不同答案的可能性越高 |
| max_tokens   | int    | 否   | 取值为[1,4096]，默认为2048 | 模型回答的tokens的最大长度                                   |
| top_k        | int    | 否   | 取值为[1，6],默认为4       | 从k个候选中随机选择⼀个，控制回答的随机性。top_k=1时temperature失效                          |
| chat_id      | string | 否   | 需要保障用户下的唯一性     | 暂不支持用户设置                                             |
| adjustTokens | Bool   | 否     | 默认为fasle                | 输入tokens超过限制，自动截断历史信息文本进行tokens调整       |

**payload.message.text部分:**

*注：text下所有content累计内容 tokens需要控制在8192内*

| 参数名称 | 类型   | 必传 | 参数要求                              | 参数说明                                    |
| -------- | ------ | ---- | ------------------------------------- | ------------------------------------------- |
| role     | string | 是   | 取值为[user,assistant,system]                | user表示是用户的问题，assistant表示AI的回复，system表示系统助手指令 |
| content  | string | 是   | 所有content的累计tokens需控制8192以内 | 用户和AI的对话内容                          |

#### 1.4 接口响应

```json
# 接口为流式返回，此示例为最后一次返回结果，开发者需要将接口多次返回的结果进行拼接展示
{
    "header":{
        "code":0,
        "message":"Success",
        "sid":"cht000cb087@dx18793cd421fb894542",
        "status":2
    },
    "payload":{
        "choices":{
            "status":2,
            "seq":0,
            "text":[
                {
                    "content":"我可以帮助你的吗？",
                    "role":"assistant"
                }
            ]
        },
        "usage":{
            "text":{
                "question_tokens":4,
                "prompt_tokens":5,
                "completion_tokens":9,
                "total_tokens":14
            }
        }
    }
}
```

接口返回字段分为两个部分，header，payload。字段解释如下

**header部分**

| 字段名  | 类型   | 字段说明                                                     |
| ------- | ------ | ------------------------------------------------------------ |
| code    | int    | 错误码，0表示正常，非0表示出错；详细释义可在接口说明文档最后的错误码说明了解 |
| message | string | 会话是否成功的描述信息                                       |
| sid     | string | 会话的唯一id，用于讯飞技术人员查询服务端会话日志使用,出现调用错误时建议留存该字段 |
| status  | int    | 会话状态，取值为[0,1,2]；0代表首次结果；1代表中间结果；2代表最后一个结果 |

**payload.choices部分**

| 字段名  | 类型   | 字段说明                                                     |
| ------- | ------ | ------------------------------------------------------------ |
| status  | int    | 文本响应状态，取值为[0,1,2]; 0代表首个文本结果；1代表中间文本结果；2代表最后一个文本结果 |
| seq     | int    | 返回的数据序号，取值为[0,9999999]                            |
| content | string | AI的回答内容                                                 |
| role    | string | 角色标识，固定为assistant，标识角色为AI                      |

**payload.usage部分(在最后一次结果返回)**

| 字段名            | 类型 | 字段说明                                                     |
| ----------------- | ---- | ------------------------------------------------------------ |
| question_tokens   | int  | 保留字段，可忽略                                             |
| prompt_tokens     | int  | 包含历史问题的总tokens大小                                   |
| completion_tokens | int  | 回答的tokens大小                                             |
| total_tokens      | int  | prompt_tokens和completion_tokens的和，也是本次交互计费的tokens大小 |
#### 1.2 HTTP接口说明
此接口不建议使用，部分版本不支持此接口
##### 1.2.1 请求方式

| 协议 | PATH                | Method |
| ---- | ------------------- | ------ |
| HTTP | /turing/v3/func/gpt | POST   |

##### 1.2.2 请求体

```json
{
    "header": {
        "traceId": "05428801-2c7f-4da8-9365-2912b7bb811e"
    },
    "parameter": {
        "chat": {
            "temperature": 0.5,
             "max_tokens": 1024
        }
    },
    "payload": {
        "message": {
            "text": [
                {
                    "content": "高考前怎样缓解紧张的情绪?",
                    "role": "user"
                }
            ]
        }
    }
}
```

请求体和请求结果与会话接口保持一致，参考上面说明

#### 2.3 请求结果

```json
{
  "header": {
    "code": 0,
    "message": "success",
    "traceId": "05428801-2c7f-4da8-9365-2912b7bb811e"
  },
  "payload": {
    "choices": {
      "seq": 0,
      "status": 2,
      "text": [
        {
          "content": "1. 深呼吸：在考试前，可以进行几次深呼吸来放松身体和心情。<ret><ret>2. 运动：适当的运动可以帮助释放紧张情绪，例如散步、慢跑、瑜伽等。<ret><ret>3. 放松音乐：听一些轻松的音乐可以帮助缓解紧张情绪，例如轻音乐、古典音乐等。<ret><ret>4. 冥想：冥想可以帮助放松身心，减轻压力和焦虑。<ret><ret>5. 与朋友聊天：与朋友聊天可以分散注意力，缓解紧张情绪。<ret><ret>6. 睡眠充足：保持充足的睡眠可以帮助身体和心情得到充分的休息和恢复。<ret><ret>7. 积极心态：保持积极的心态，相信自己的能力，不要过分担心和紧张。<end>",
          "role": "assistant"
        }
      ]
    },
    "usage": {
      "text": {
        "question_tokens": 0,
        "prompt_tokens": 16,
        "completion_tokens": 152,
        "total_tokens": 168
      }
    }
  }
}
```

###  2.个性化LORA接口
#### 2.1 请求地址
接口请求地址见ws流式接口
#### 2.3 请求参数

```json
{
    "header": {
        "traceId": "SPARK-DEMO"
    },
    "parameter": {
        "chat": {
            "max_tokens": 4096,
            "punish": 1.2,
            "top_k": 1
        },
        "lora": {
            "md5": "xxxx",
            "url": "http://127.0.0.1:2230/lora.bin"
        }
    },
    "payload": {
        "message": {
            "text": [
                {
                    "content": "合肥明天天气",
                    "content_meta": {},
                    "content_type": "text",
                    "role": "user"
                }
            ]
        }
    }
}
```
**parameter.lora部分**:

| 参数名称 | 类型 | 必传 | 参数要求 | 参数说明 |
| ---- | ---- | ---- | ---- | :--- |
| url | string | 是 | 无 | lora小包的下载地址，目前一次会话只支持一个lora包 |
| md5 | string | 是 | 无 | 对应的lora包md5值 |
备注：其他请求字段和请求接口字段与上面推理接口中一致


## 错误码说明

| 错误码 | 说明                  |
| ------ | --------------------- |
| -1     | 未知异常              |
| 4      | 请求体JSON解析错误    |
| 10000  | schema校验错误        |
| 10002  | 缺少对话内容          |
| 10003  | 输入文本超过token限制 |
| 11000  | GPT推理模块会话异常   |

## 接口调用示例

#### 流式接口java语言调用示例：

**Maven依赖库：**

```java
	<dependency>
			<groupId>org.java-websocket</groupId>
			<artifactId>Java-WebSocket</artifactId>
			<version>1.4.0</version>
	</dependency>
```

**调用示例：**

```java
public class SprakTest {
    public static void main(String[] args) throws Exception {
        CountDownLatch countDownLatch = new CountDownLatch(1);
        URI uri = new URI("http://172.31.101.142:9990/turing/v3/gpt");
        WebSocketClient  webSocketClient = new WebSocketClient(uri, new Draft_6455()) {
            @Override
            public void onOpen(ServerHandshake handshakedata) {
            }

            @Override
            public void onMessage(String message) {
                JSONObject response = JSON.parseObject(message);
                if (response.getJSONObject("header").getInteger("code") != 0){
                    countDownLatch.countDown();
                    return;
                }
                int status = response.getJSONObject("payload").getJSONObject("choices").getInteger("status");
                if (status == 2){
                    countDownLatch.countDown();
                }
                System.out.println(message);
            }

            @Override
            public void onClose(int code, String reason, boolean remote) {
                countDownLatch.countDown();
            }

            @Override
            public void onError(Exception ex) {
                countDownLatch.countDown();
            }
        };
        boolean isConnect =  webSocketClient.connectBlocking(10000, TimeUnit.MILLISECONDS);
        if (isConnect){
            // TODO: 异常判断
        }

        JSONObject apiRequest = new JSONObject();
        JSONObject header = new JSONObject();
        header.put("traceId", "spark-demo-test");
        apiRequest.put("header", header);
        JSONObject parma = new JSONObject();
        parma.put("max_tokens", 2048);
        parma.put("temperature", 0.1);
        parma.put("top_k", 5);
        apiRequest.put("chat", parma);

        JSONObject content = new JSONObject();
        content.put("content", "今天天气怎么样");
        content.put("role", "user");
        JSONArray contentList = new JSONArray();
        contentList.add(content);
        JSONObject text = new JSONObject();
        text.put("text", contentList);
        JSONObject payload = new JSONObject();
        payload.put("message", text);
        apiRequest.put("payload", payload);

        webSocketClient.send(apiRequest.toString());

        countDownLatch.await();
        webSocketClient.close();
        System.out.println("end");
    }
}
```

