下面是新版Google Gen AI api，之后关于gemini的api都要参照这个最新版修改，请先不做代码改动，只需了解
---
升级到 Google Gen AI SDK

在推出 Gemini 2.0 模型系列时，我们还发布了一组适用于 Gemini API 的新 Google Gen AI 库：

Python
TypeScript 和 JavaScript
Go
这些更新后的库将与所有 Gemini API 模型和功能完全兼容，包括最近添加的 Live API 和 Veo 等。

我们建议您开始将项目从旧版 Gemini SDK 迁移到新版 Gen AI SDK。本指南提供了迁移后的代码示例，以帮助您上手。我们会继续在此处添加示例，以帮助您快速上手使用新库。

注意 ：Go 示例省略了导入和其他样板代码，以提高可读性。
安装 SDK
之前

Python
JavaScript
Go

pip install -U -q "google-generativeai"
之后

Python
JavaScript
Go

pip install -U -q "google-genai"
身份验证
使用 API 密钥进行身份验证。您可以在 Google AI 工作室中创建 API 密钥。

之前

Python
JavaScript
Go
旧版 SDK 会隐式处理 API 客户端对象。在新 SDK 中，您可以创建 API 客户端并使用它调用 API。请注意，无论是哪种情况，如果您未将 API 密钥传递给客户端，SDK 都会从 GOOGLE_API_KEY 环境变量中提取 API 密钥。


import google.generativeai as genai

genai.configure(api_key=...)
之后

Python
JavaScript
Go

export GOOGLE_API_KEY="YOUR_API_KEY"

from google import genai

client = genai.Client() # Set the API key using the GOOGLE_API_KEY env var.
                        # Alternatively, you could set the API key explicitly:
                        # client = genai.Client(api_key="your_api_key")
生成内容
之前

Python
JavaScript
Go
新版 SDK 通过 Client 对象提供对所有 API 方法的访问权限。除了一些有状态的特殊情况（chat 和实时 API session）外，这些都是无状态函数。为了实用性和统一性，返回的对象是 pydantic 类。


import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    'Tell me a story in 300 words'
)
print(response.text)
之后

Python
JavaScript
Go

from google import genai
client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Tell me a story in 300 words.'
)
print(response.text)

print(response.model_dump_json(
    exclude_none=True, indent=4))
之前

Python
JavaScript
Go
新版 SDK 中也提供了许多相同的实用功能。例如，系统会自动转换 PIL.Image 对象。


import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    'Tell me a story based on this image',
    Image.open(image_path)
])
print(response.text)
之后

Python
JavaScript
Go

from google import genai
from PIL import Image

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'Tell me a story based on this image',
        Image.open(image_path)
    ]
)
print(response.text)
流式
之前

Python
JavaScript
Go

import google.generativeai as genai

response = model.generate_content(
    "Write a cute story about cats.",
    stream=True)
for chunk in response:
    print(chunk.text)
之后

Python
JavaScript
Go

from google import genai

client = genai.Client()

for chunk in client.models.generate_content_stream(
  model='gemini-2.0-flash',
  contents='Tell me a story in 300 words.'
):
    print(chunk.text)
配置
之前

Python
JavaScript
Go
对于新版 SDK 中的所有方法，必需的参数都以关键字参数的形式提供。所有可选输入均在 config 参数中提供。配置参数可以指定为 google.genai.types 命名空间中的 Python 字典或 Config 类。为了提高实用性和统一性，types 模块中的所有定义都是 pydantic 类。


import google.generativeai as genai

model = genai.GenerativeModel(
  'gemini-1.5-flash',
    system_instruction='you are a story teller for kids under 5 years old',
    generation_config=genai.GenerationConfig(
      max_output_tokens=400,
      top_k=2,
      top_p=0.5,
      temperature=0.5,
      response_mime_type='application/json',
      stop_sequences=['\n'],
    )
)
response = model.generate_content('tell me a story in 100 words')
之后

Python
JavaScript
Go

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents='Tell me a story in 100 words.',
  config=types.GenerateContentConfig(
      system_instruction='you are a story teller for kids under 5 years old',
      max_output_tokens= 400,
      top_k= 2,
      top_p= 0.5,
      temperature= 0.5,
      response_mime_type= 'application/json',
      stop_sequences= ['\n'],
      seed=42,
  ),
)
安全设置
使用安全设置生成回答：

之前

Python
JavaScript

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    'say something bad',
    safety_settings={
        'HATE': 'BLOCK_ONLY_HIGH',
        'HARASSMENT': 'BLOCK_ONLY_HIGH',
  }
)
之后

Python
JavaScript

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents='say something bad',
  config=types.GenerateContentConfig(
      safety_settings= [
          types.SafetySetting(
              category='HARM_CATEGORY_HATE_SPEECH',
              threshold='BLOCK_ONLY_HIGH'
          ),
      ]
  ),
)
异步
之前

Python
如需将新 SDK 与 asyncio 搭配使用，client.aio 下每个方法都有单独的 async 实现。


import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content_async(
    'tell me a story in 100 words'
)
之后

Python

from google import genai

client = genai.Client()

response = await client.aio.models.generate_content(
    model='gemini-2.0-flash',
    contents='Tell me a story in 300 words.'
)
聊天
发起聊天并向模型发送消息：

之前

Python
JavaScript
Go

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat()

response = chat.send_message(
    "Tell me a story in 100 words")
response = chat.send_message(
    "What happened after that?")
之后

Python
JavaScript
Go

from google import genai

client = genai.Client()

chat = client.chats.create(model='gemini-2.0-flash')

response = chat.send_message(
    message='Tell me a story in 100 words')
response = chat.send_message(
    message='What happened after that?')
函数调用
之前

Python
在新版 SDK 中，自动函数调用是默认设置。您可以在此处停用此功能。


import google.generativeai as genai
from enum import Enum

def get_current_weather(location: str) -> str:
    """Get the current whether in a given location.

    Args:
        location: required, The city and state, e.g. San Franciso, CA
        unit: celsius or fahrenheit
    """
    print(f'Called with: {location=}')
    return "23C"

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[get_current_weather]
)

response = model.generate_content("What is the weather in San Francisco?")
function_call = response.candidates[0].parts[0].function_call
之后

Python

from google import genai
from google.genai import types

client = genai.Client()

def get_current_weather(location: str) -> str:
    """Get the current whether in a given location.

    Args:
        location: required, The city and state, e.g. San Franciso, CA
        unit: celsius or fahrenheit
    """
    print(f'Called with: {location=}')
    return "23C"

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents="What is the weather like in Boston?",
  config=types.GenerateContentConfig(
      tools=[get_current_weather],
      automatic_function_calling={'disable': True},
  ),
)

function_call = response.candidates[0].content.parts[0].function_call
自动函数调用
之前

Python
旧版 SDK 仅支持在聊天中自动调用函数。在新版 SDK 中，这是 generate_content 的默认行为。


import google.generativeai as genai

def get_current_weather(city: str) -> str:
    return "23C"

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[get_current_weather]
)

chat = model.start_chat(
    enable_automatic_function_calling=True)
result = chat.send_message("What is the weather in San Francisco?")
之后

Python

from google import genai
from google.genai import types
client = genai.Client()

def get_current_weather(city: str) -> str:
    return "23C"

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents="What is the weather like in Boston?",
  config=types.GenerateContentConfig(
      tools=[get_current_weather]
  ),
)
代码执行
代码执行工具可让模型生成 Python 代码、运行该代码并返回结果。

之前

Python
JavaScript

import google.generativeai as genai

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools="code_execution"
)

result = model.generate_content(
  "What is the sum of the first 50 prime numbers? Generate and run code for "
  "the calculation, and make sure you get all 50.")
之后

Python
JavaScript

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the sum of the first 50 prime numbers? Generate and run '
            'code for the calculation, and make sure you get all 50.',
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
    ),
)
搜索接地
GoogleSearch（Gemini>=2.0）和 GoogleSearchRetrieval（Gemini < 2.0）是可让模型检索公开 Web 数据以进行“接地”的工具，由 Google 提供支持。

之前

Python

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    contents="what is the Google stock price?",
    tools='google_search_retrieval'
)
之后

Python

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the Google stock price?',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ]
    )
)
JSON 响应
以 JSON 格式生成回答。

之前

Python
JavaScript
通过指定 response_schema 并设置 response_mime_type="application/json"，用户可以约束模型，使其按照给定结构生成 JSON 响应。新版 SDK 使用 pydantic 类提供架构（不过，您也可以传递 genai.types.Schema 或等效的 dict）。在可能的情况下，SDK 会解析返回的 JSON，并在 response.parsed 中返回结果。如果您将 pydantic 类作为架构提供，SDK 将将该 JSON 转换为该类的实例。


import google.generativeai as genai
import typing_extensions as typing

class CountryInfo(typing.TypedDict):
    name: str
    population: int
    capital: str
    continent: str
    major_cities: list[str]
    gdp: int
    official_language: str
    total_area_sq_mi: int

model = genai.GenerativeModel(model_name="gemini-1.5-flash")
result = model.generate_content(
    "Give me information of the United States",
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema = CountryInfo
    ),
)
之后

Python
JavaScript

from google import genai
from pydantic import BaseModel

client = genai.Client()

class CountryInfo(BaseModel):
    name: str
    population: int
    capital: str
    continent: str
    major_cities: list[str]
    gdp: int
    official_language: str
    total_area_sq_mi: int

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Give me information of the United States.',
    config={
        'response_mime_type': 'application/json',
        'response_schema': CountryInfo,
    },
)

response.parsed
文件
上传
上传文件：

之前

Python

import requests
import pathlib
import google.generativeai as genai

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

file = genai.upload_file(path='a11.txt')

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    'Can you summarize this file:',
    my_file
])
print(response.text)
之后

Python

import requests
import pathlib
from google import genai

client = genai.Client()

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

my_file = client.files.upload(file='a11.txt')

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'Can you summarize this file:',
        my_file
    ]
)
print(response.text)
列出和获取
列出已上传的文件并获取具有文件名的已上传文件：

之前

Python

import google.generativeai as genai

for file in genai.list_files():
  print(file.name)

file = genai.get_file(name=file.name)
之后

Python

from google import genai
client = genai.Client()

for file in client.files.list():
    print(file.name)

file = client.files.get(name=file.name)
删除
删除文件：

之前

Python

import pathlib
import google.generativeai as genai

pathlib.Path('dummy.txt').write_text(dummy)
dummy_file = genai.upload_file(path='dummy.txt')

file = genai.delete_file(name=dummy_file.name)
之后

Python

import pathlib
from google import genai

client = genai.Client()

pathlib.Path('dummy.txt').write_text(dummy)
dummy_file = client.files.upload(file='dummy.txt')

response = client.files.delete(name=dummy_file.name)
上下文缓存
借助上下文缓存，用户可以将内容传递给模型一次，缓存输入 token，然后在后续调用中引用缓存的 token 以降低费用。

之前

Python
JavaScript

import requests
import pathlib
import google.generativeai as genai
from google.generativeai import caching

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file
document = genai.upload_file(path="a11.txt")

# Create cache
apollo_cache = caching.CachedContent.create(
    model="gemini-1.5-flash-001",
    system_instruction="You are an expert at analyzing transcripts.",
    contents=[document],
)

# Generate response
apollo_model = genai.GenerativeModel.from_cached_content(
    cached_content=apollo_cache
)
response = apollo_model.generate_content("Find a lighthearted moment from this transcript")
之后

Python
JavaScript

import requests
import pathlib
from google import genai
from google.genai import types

client = genai.Client()

# Check which models support caching.
for m in client.models.list():
  for action in m.supported_actions:
    if action == "createCachedContent":
      print(m.name)
      break

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file
document = client.files.upload(file='a11.txt')

# Create cache
model='gemini-1.5-flash-001'
apollo_cache = client.caches.create(
      model=model,
      config={
          'contents': [document],
          'system_instruction': 'You are an expert at analyzing transcripts.',
      },
  )

# Generate response
response = client.models.generate_content(
    model=model,
    contents='Find a lighthearted moment from this transcript',
    config=types.GenerateContentConfig(
        cached_content=apollo_cache.name,
    )
)
统计词元数
统计请求中的令牌数量。

之前

Python
JavaScript

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.count_tokens(
    'The quick brown fox jumps over the lazy dog.')
之后

Python
JavaScript

from google import genai

client = genai.Client()

response = client.models.count_tokens(
    model='gemini-2.0-flash',
    contents='The quick brown fox jumps over the lazy dog.',
)
生成图片
生成图片：

之前

Python

#pip install https://github.com/google-gemini/generative-ai-python@imagen
import google.generativeai as genai

imagen = genai.ImageGenerationModel(
    "imagen-3.0-generate-001")
gen_images = imagen.generate_images(
    prompt="Robot holding a red skateboard",
    number_of_images=1,
    safety_filter_level="block_low_and_above",
    person_generation="allow_adult",
    aspect_ratio="3:4",
)
之后

Python

from google import genai

client = genai.Client()

gen_images = client.models.generate_images(
    model='imagen-3.0-generate-001',
    prompt='Robot holding a red skateboard',
    config=types.GenerateImagesConfig(
        number_of_images= 1,
        safety_filter_level= "BLOCK_LOW_AND_ABOVE",
        person_generation= "ALLOW_ADULT",
        aspect_ratio= "3:4",
    )
)

for n, image in enumerate(gen_images.generated_images):
    pathlib.Path(f'{n}.png').write_bytes(
        image.image.image_bytes)
嵌入内容
生成内容嵌入。

之前

Python
JavaScript

import google.generativeai as genai

response = genai.embed_content(
  model='models/text-embedding-004',
  content='Hello world'
)
之后

Python
JavaScript

from google import genai

client = genai.Client()

response = client.models.embed_content(
  model='text-embedding-004',
  contents='Hello world',
)
调整模型
创建和使用已调参模型。

新版 SDK 通过 client.tunings.tune 简化了调整流程，该函数会启动调整作业并轮询，直到作业完成。

之前

Python

import google.generativeai as genai
import random

# create tuning model
train_data = {}
for i in range(1, 6):
  key = f'input {i}'
  value = f'output {i}'
  train_data[key] = value

name = f'generate-num-{random.randint(0,10000)}'
operation = genai.create_tuned_model(
    source_model='models/gemini-1.5-flash-001-tuning',
    training_data=train_data,
    id = name,
    epoch_count = 5,
    batch_size=4,
    learning_rate=0.001,
)
# wait for tuning complete
tuningProgress = operation.result()

# generate content with the tuned model
model = genai.GenerativeModel(model_name=f'tunedModels/{name}')
response = model.generate_content('55')
之后

Python

from google import genai
from google.genai import types

client = genai.Client()

# Check which models are available for tuning.
for m in client.models.list():
  for action in m.supported_actions:
    if action == "createTunedModel":
      print(m.name)
      break

# create tuning model
training_dataset=types.TuningDataset(
        examples=[
            types.TuningExample(
                text_input=f'input {i}',
                output=f'output {i}',
            )
            for i in range(5)
        ],
    )
tuning_job = client.tunings.tune(
    base_model='models/gemini-1.5-flash-001-tuning',
    training_dataset=training_dataset,
    config=types.CreateTuningJobConfig(
        epoch_count= 5,
        batch_size=4,
        learning_rate=0.001,
        tuned_model_display_name="test tuned model"
    )
)

# generate content with the tuned model
response = client.models.generate_content(
    model=tuning_job.tuned_model.model,
    contents='55',
)