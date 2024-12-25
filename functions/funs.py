import openai
from groq import Groq
import anthropic

import json
import re
import subprocess
import os
import time
import base64

from os.path import join, dirname
from dotenv import load_dotenv

import sys
import threading
import queue
from typing import Union, List

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

SYSTEM_PROMPT = """あなたは、高度な自然言語処理能力と生成能力を持つ、AIアシスタントです。
以下の点を厳守してください。
* ユーザーからの質問や要求には、正確かつ適切に、可能な限り詳細に答えること。
* 専門用語や技術用語は、必要に応じて分かりやすく解説すること。
* 常に礼儀正しく、友好的な態度で接すること。
* 倫理的に問題のある要求や、差別的、侮辱的な要求には応じないこと。
* 個人情報やプライバシーに関わる情報については、適切に保護すること。
* 回答は原則として日本語で行うこと。ただし、ユーザーからの質問が英語などの外国語であった場合は、その言語で答えても良い。
* 文脈によっては、創造的な文章や詩、コードなどを生成することも許可する。
* 最新の情報に基づいて回答するように努めること。ただし、情報の正確性を保証するものではないことを明記すること。
* もし質問の意味が不明な場合は、質問を明確にするための質問を返すこと。
* 自分がAIアシスタントであること、人間ではないことを明確に示すこと。
* 上記の指示に矛盾しない範囲で、状況に応じて柔軟に対応すること。

これらの指示に加えて、以下の点も考慮してください。
* 質問に対して簡潔に答えるだけでなく、背景や関連情報なども含めて、より深く理解できるような回答を心がけること。
* ユーザーの知識レベルに合わせて、適切な表現や言葉遣いを選択すること。
* もし回答が複数考えられる場合は、それぞれの可能性を示し、それぞれのメリットとデメリットを説明すること。
* 常に学習し、自身の知識と能力を向上させるように努めること。

このシステムプロンプトに従い、最高のパフォーマンスを発揮してください。"""

IMG_SYSTEM_PROMPT = """あなたは、高度な画像認識能力と自然言語処理能力を持つAIアシスタントです。
提供された画像を詳細に分析し、以下の点を厳守して回答してください：

画像認識に関する基本方針:
* 画像の内容を詳細かつ正確に説明すること
* 画像内の重要な要素、特徴、パターンを漏らさず指摘すること
* 画像の品質、明るさ、構図などの技術的な特徴にも言及すること
* 不適切な内容や機密情報が含まれる可能性がある場合は、適切に警告すること

回答方式について:
* 原則として日本語で回答すること
* 専門用語を使用する場合は、分かりやすく解説を加えること
* 画像の文脈や目的に応じて、適切な詳細度で説明すること
* 不確かな要素については、その旨を明確に示すこと

分析の構造:
1. 画像の概要（何が写っているか、全体的な印象）
2. 重要な詳細（主要な被写体、特徴的な要素）
3. 背景や環境の説明
4. 技術的な観察（画質、照明、アングルなど）
5. 必要に応じた追加コメント（文化的背景、類似事例など）

注意事項:
* 個人を特定できる情報については、プライバシーに配慮して言及を控えること
* 著作権や知的財産権に関する懸念がある場合は、その旨を指摘すること
* 画像の真偽性が疑わしい場合は、その可能性について言及すること
* 画像に含まれる文字情報は可能な限り抽出して提供すること

このシステムプロンプトに従い、画像認識と説明において最高のパフォーマンスを発揮してください。"""

client_gpt = openai.OpenAI(
    api_key = os.environ.get("OPENAI_API_KEY")
)
client_groq = Groq(
    api_key = os.environ.get("GROQ_API_KEY")
)
client_ollama = openai.OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)
client_llamacpp = openai.OpenAI(
    base_url = 'http://localhost:8080/v1',
    api_key='any_thing', # required, but unused
)
client_pplx = openai.OpenAI(
    api_key = os.environ.get("PPLX_API_KEY"),
    base_url="https://api.perplexity.ai"
)
client_xai = openai.OpenAI(
    api_key = os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)
client_claude = anthropic.Anthropic(
    api_key = os.environ.get("ANTHROPIC_API_KEY"), 
)
client_gemini = openai.OpenAI(
    api_key = os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

def gpt_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "chatgpt-4o-latest"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list :
        input_messages_list = user_inputs.copy()  # コピーを作成
        input_messages_list.insert(0, {"role": "system", "content": system_prompt})
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_gpt.chat.completions.create(
        model=main_model,
        messages=input_messages_list
    )
    return completion.choices[0].message.content

def ollama_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "qwen2.5:latest"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list:
        input_messages_list = user_inputs.copy()  # コピーを作成
        input_messages_list.insert(0, {"role": "system", "content": system_prompt})
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_ollama.chat.completions.create(
        model=main_model,
        messages=input_messages_list
    )
    return completion.choices[0].message.content
def llamacpp_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "gemma2:9b-instruct-q4_K_M"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list:
        input_messages_list = user_inputs.copy()  # コピーを作成
        input_messages_list.insert(0, {"role": "system", "content": system_prompt})
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_llamacpp.chat.completions.create(
        model=main_model,
        messages=input_messages_list
    )
    return completion.choices[0].message.content

def groq_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "llama-3.2-90b-vision-preview"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list:
        input_messages_list = user_inputs.copy()  # コピーを作成
        input_messages_list.insert(0, {"role": "system", "content": system_prompt})
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_groq.chat.completions.create(
        messages=input_messages_list,
        model=main_model
    )
    return completion.choices[0].message.content

def groq_con_fast(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "gemma2-9b-it"):
    completion = client_groq.chat.completions.create(
    model=main_model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_inputs},
    ]
    )
    return completion.choices[0].message.content

def gemini_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "gemini-2.0-flash-exp"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list:
        input_messages_list = user_inputs.copy()  # コピーを作成
        input_messages_list.insert(0, {"role": "system", "content": system_prompt})
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_gemini.chat.completions.create(
        messages=input_messages_list,
        model=main_model
    )
    return completion.choices[0].message.content

def claude_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "claude-3-5-haiku-latest"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list :
        input_messages_list = user_inputs.copy()
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_claude.messages.create(
        model=main_model,
        system = system_prompt,
        max_tokens = 8192,
        temperature=0.2,
        messages=input_messages_list
    )
    return completion.content[0].text

def xai_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "grok-2-1212"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list:
        input_messages_list = user_inputs.copy()  # コピーを作成
        input_messages_list.insert(0, {"role": "system", "content": system_prompt})
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_xai.chat.completions.create(
        model=main_model,
        messages=input_messages_list
    )
    return completion.choices[0].message.content

def pplx_chat(user_inputs,system_prompt = SYSTEM_PROMPT,main_model = "llama-3.1-sonar-large-128k-online"):
    if type(user_inputs) == str:
        input_messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_inputs},
        ]
    elif type(user_inputs) == list:
        input_messages_list = user_inputs.copy()  # コピーを作成
        input_messages_list.insert(0, {"role": "system", "content": system_prompt})
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加

    completion = client_pplx.chat.completions.create(
        model=main_model,
        messages=input_messages_list
    )
    return completion.choices[0].message.content
def integration_chat(user_input,system_prompt = SYSTEM_PROMPT,model_type = "gpt"):
    if model_type == "gpt":
        res = gpt_chat(user_input,system_prompt,"chatgpt-4o-latest")
    elif model_type == "ollama":
        res = ollama_chat(user_input,system_prompt)
    elif model_type == "groq":
        res = groq_chat(user_input,system_prompt,"llama-3.2-90b-text-preview")
    elif model_type == "llamacpp":
        res = llamacpp_chat(user_input,system_prompt)
    elif model_type == "gemini":
        res = gemini_chat(user_input,system_prompt,"gemini-1.5-pro-002")
    elif model_type == "claude":
        res = claude_chat(user_input,system_prompt,"claude-3-5-sonnet-latest")
    elif model_type == "grok":
        res = xai_chat(user_input,system_prompt)
    elif model_type == "pplx":
        res = pplx_chat(user_input,system_prompt)
    return res

def integration_chat_lc(user_input,system_prompt = SYSTEM_PROMPT,model_type = "gpt"):
    if model_type == "gpt":
        res = gpt_chat(user_input,system_prompt,"gpt-4o-mini")
    elif model_type == "ollama":
        res = ollama_chat(user_input,system_prompt)
    elif model_type == "groq":
        res = groq_chat(user_input,system_prompt,"gemma2-9b-it")
    elif model_type == "llamacpp":
        res = llamacpp_chat(user_input,system_prompt)
    elif model_type == "gemini":
        res = gemini_chat(user_input,system_prompt)
    elif model_type == "claude":
        res = claude_chat(user_input,system_prompt)
    elif model_type == "grok":
        res = xai_chat(user_input,system_prompt)
    elif model_type == "pplx":
        res = pplx_chat(user_input,system_prompt)
    return res

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def add_img_url_4_gpt(messages, image_base64):
    """
    メッセージリストの最初のユーザーメッセージを変換する関数
    
    Args:
        messages (list): メッセージの辞書のリスト
        image_base64 (str): Base64エンコードされた画像データ
    
    Returns:
        list: 変換後のメッセージリスト
    """
    # メッセージリストが空の場合は空リストを返す
    if not messages:
        return []
    
    # 最初のメッセージを取得
    first_message = messages[0]
    
    # 最初のメッセージがユーザーのものでない場合は変換せずに返す
    if first_message.get("role") != "user":
        return messages
    
    # 変換後のメッセージリストを作成
    transformed_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": first_message["content"]
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    
    # 2番目以降のメッセージを追加
    transformed_messages.extend(messages[1:])
    
    return transformed_messages

def add_img_url_4_claude(messages, image_base64):
    """
    メッセージリストの最初のユーザーメッセージを変換する関数
    
    Args:
        messages (list): メッセージの辞書のリスト
        image_base64 (str): Base64エンコードされた画像データ
    
    Returns:
        list: 変換後のメッセージリスト
    """
    # メッセージリストが空の場合は空リストを返す
    if not messages:
        return []
    
    # 最初のメッセージを取得
    first_message = messages[0]
    
    # 最初のメッセージがユーザーのものでない場合は変換せずに返す
    if first_message.get("role") != "user":
        return messages
    
    # 変換後のメッセージリストを作成
    transformed_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": first_message["content"]
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                }
            ]
        }
    ]
    
    # 2番目以降のメッセージを追加
    transformed_messages.extend(messages[1:])
    
    return transformed_messages

def img_inf_gpt(message,image_path,system_prompt = IMG_SYSTEM_PROMPT,main_model = "gpt-4o-mini"):
    if type(message) == str:
        input_messages_list = [
            {"role": "user", "content": message},
        ]
    elif type(message) == list:
        input_messages_list = message.copy()  # コピーを作成
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加
    base64_image = encode_image(image_path)
    user_inputs = add_img_url_4_gpt(input_messages_list, base64_image)
    user_inputs.insert(0, {"role": "system", "content": system_prompt})
    completion = client_gpt.chat.completions.create(
        model=main_model,
        messages=user_inputs
    )
    return completion.choices[0].message.content

def img_inf_groq(message,image_path,main_model = "llama-3.2-90b-vision-preview"):
    if type(message) == str:
        input_messages_list = [
            {"role": "user", "content": message},
        ]
    elif type(message) == list:
        input_messages_list = message.copy()  # コピーを作成
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加
    base64_image = encode_image(image_path)
    user_inputs = add_img_url_4_gpt(input_messages_list, base64_image)
    completion = client_groq.chat.completions.create(
        model=main_model,
        messages=user_inputs
    )
    return completion.choices[0].message.content

def img_inf_ollama(message,image_path,main_model = "llama3.2-vision:11b"):
    if type(message) == str:
        input_messages_list = [
            {"role": "user", "content": message},
        ]
    elif type(message) == list:
        input_messages_list = message.copy()  # コピーを作成
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加
    base64_image = encode_image(image_path)
    user_inputs = add_img_url_4_gpt(input_messages_list, base64_image)
    completion = client_ollama.chat.completions.create(
        model=main_model,
        messages=user_inputs
    )
    return completion.choices[0].message.content

def img_inf_claude(message,image_path,system_prompt = IMG_SYSTEM_PROMPT,main_model = "claude-3-5-sonnet-latest"):
    if type(message) == str:
        input_messages_list = [
            {"role": "user", "content": message},
        ]
    elif type(message) == list:
        input_messages_list = message.copy()  # コピーを作成
    else:
        raise ValueError("user_inputs should be a string or a list.")  # エラーハンドリングを追加
    base64_image = encode_image(image_path)
    user_inputs = add_img_url_4_claude(input_messages_list, base64_image)
    completion = client_claude.messages.create(
        model=main_model,
        system = system_prompt,
        max_tokens = 8192,
        temperature=0.2,
        messages=user_inputs
    )
    return completion.content[0].text