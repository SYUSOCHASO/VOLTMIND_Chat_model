## スクレイピング関連のライブラリ
import requests
from bs4 import BeautifulSoup
import json

## 文章検索エンジン
from langchain.retrievers import TFIDFRetriever
from langchain.retrievers import BM25Retriever
from sklearn.metrics.pairwise import cosine_similarity
from typing import List

import re

import os
from os.path import join, dirname
from dotenv import load_dotenv

## 検索エンジンのライブラリ関連
from duckduckgo_search import DDGS #search系の関数

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
## APIキーやエンジンIDがない場合にはこのリンクを参考にしてください。[https://qiita.com/zak_y/items/42ca0f1ea14f7046108c]


def scrape_web_page(url,whiteing_type = "0"):
    """
    指定されたURLのWebページをスクレイピングし、
    タグの種類と内容をJSONL形式で出力する関数。
    同じタグが連続する場合は、内容を結合します。
    h2, h3タグに囲まれた20文字以下のpタグは削除します。

    Args:
        url (str): webページのURL

    Returns:
        None
    """

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # 解析対象のタグを指定
    target_tags = ['h2', 'h3', 'p']

    c_data = []
    last_tag = None
    last_data = None

    for tag in soup.find_all(target_tags):
        # h2, h3タグに囲まれた20文字以下のpタグをスキップ
        if whiteing_type == "1":
            if tag.name == 'p' and len(tag.get_text(strip=True)) < 20 and tag.find_parent(['h2', 'h3']):
                continue
        data = {
            "tag_type": tag.name,
            "context": tag.get_text(strip=True)
        }

        if last_tag == tag.name:
            # 同じタグが連続する場合、contextを結合
            last_data["context"] += "\n\n" + data["context"]
        else:
            # 新しいタグの場合、前のデータをリストに追加し、現在のデータを保持
            if last_data:
                c_data.append(last_data)
            last_tag = tag.name
            last_data = data

    # 最後のデータをリストに追加
    if last_data:
        c_data.append(last_data)

    return c_data

def scrape_web_page_with_code(url, whiteing_type="0"):
    """
    指定されたURLのWebページをスクレイピングし、
    タグの種類と内容をJSONL形式で出力する関数。
    同じタグが連続する場合は、内容を結合します。
    h2, h3タグに囲まれた20文字以下のpタグは削除します。
    codeタグに対応し、内容は整形します。
    note,qiita,zennはこれで大丈夫です

    Args:
        url (str): webページのURL
        whiteing_type (str): ホワイトニングのタイプ。
                              "0": ホワイトニングなし
                              "1": h2, h3タグに囲まれた20文字以下のpタグを削除

    Returns:
        list: スクレイピング結果のリスト
    """

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # 解析対象のタグを指定
    target_tags = ['h2', 'h3', 'p', 'code']

    c_data = []
    last_tag = None
    last_data = None

    for tag in soup.find_all(target_tags):
        # h2, h3タグに囲まれた20文字以下のpタグをスキップ
        if whiteing_type == "1":
            if tag.name == 'p' and len(tag.get_text(strip=True)) < 20 and tag.find_parent(['h2', 'h3']):
                continue

        # codeタグの内容を整形
        if tag.name == 'code':
            code_content = tag.get_text()
            # インデントの調整など、必要に応じて整形処理を追加
            formatted_code = code_content.strip() 
            data = {
                "tag_type": tag.name,
                "context": formatted_code
            }
        else:
            data = {
                "tag_type": tag.name,
                "context": tag.get_text(strip=True)
            }

        if last_tag == tag.name:
            # 同じタグが連続する場合、contextを結合
            last_data["context"] += "\n\n" + data["context"]
        else:
            # 新しいタグの場合、前のデータをリストに追加し、現在のデータを保持
            if last_data:
                c_data.append(last_data)
            last_tag = tag.name
            last_data = data

    # 最後のデータをリストに追加
    if last_data:
        c_data.append(last_data)

    return c_data

def scrape_web_page_4_RAG(url, whiteing_type="0"):
    """
    指定されたURLのWebページをスクレイピングし、
    タグの種類と内容をJSONL形式で出力する関数。
    エラーハンドリングを追加。

    Args:
        url (str): webページのURL
        whiteing_type (str): ホワイトニングのタイプ。
            "0": ホワイトニングなし
            "1": h2, h3タグに囲まれた20文字以下のpタグを削除

    Returns:
        list: スクレイピング結果のリスト。エラー時は専用のエラーメッセージを含むリストを返す
    """
    try:
        response = requests.get(url, timeout=30)  # タイムアウトを設定
        
        # ステータスコードのチェック
        if response.status_code != 200:
            error_message = {
                "count": "1",
                "tag_name": "h2",
                "context": f"エラーが出たため、このページは使用できません（ステータスコード: {response.status_code}）"
            }
            return [error_message]

        soup = BeautifulSoup(response.content, 'html.parser')
        target_tags = ['h1', 'h2', 'h3', 'p', 'code']
        c_data = []
        count = 0

        for tag in soup.find_all(target_tags):
            count += 1
            if tag.name == 'code':
                code_content = tag.get_text()
                formatted_code = code_content.strip()
                data = {
                    "count": str(count),
                    "tag_name": tag.name,
                    "context": formatted_code
                }
            else:
                data = {
                    "count": str(count),
                    "tag_name": tag.name,
                    "context": tag.get_text(strip=True)
                }
            c_data.append(data)

        return c_data if c_data else [{
            "count": "1",
            "tag_name": "h2",
            "context": "エラーが出たため、このページは使用できません（コンテンツが見つかりません）"
        }]

    except requests.Timeout:
        return [{
            "count": "1",
            "tag_name": "h2",
            "context": "エラーが出たため、このページは使用できません（タイムアウト）"
        }]
    except requests.RequestException as e:
        return [{
            "count": "1",
            "tag_name": "h2",
            "context": f"エラーが出たため、このページは使用できません（接続エラー: {str(e)}）"
        }]
    except Exception as e:
        return [{
            "count": "1",
            "tag_name": "h2",
            "context": f"エラーが出たため、このページは使用できません（予期せぬエラー: {str(e)}）"
        }]


def scrape_web_page_jina(url):
    """
    jinaを用いてurlからマークダウンを作る関数(レート制限があるので注意)
    """
    r_url = "https://r.jina.ai/"
    is_json  = False # json 形式で取得するか

    params = {
        "url": f"{r_url}{url}",
    }
    if is_json:
        params["headers"] = {"Accept": "application/json"}

    response = requests.get(**params)
    return response.text

def get_readme_content(repository_url):
  """
  GitHubのリポジトリURLを入力して、README.mdファイルの内容を取得し、
  その内容を返す関数。

  Args:
    repository_url: GitHubのリポジトリURL (例: https://github.com/user/repo)

  Returns:
    str: README.mdファイルの内容。取得に失敗した場合はNoneを返す。
  """

  try:
    # リポジトリページのHTMLを取得
    response = requests.get(repository_url)
    response.raise_for_status()  # HTTPエラーが発生した場合、例外を発生させる

    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(response.content, "html.parser")

    # デフォルトブランチ名を取得 (class名が'Text-sc-17v1xeu-0 bOMzPg'のspanタグから)
    branch_name_element = soup.find("span", class_="Text__StyledText-sc-17v1xeu-0 eMMFM")
    if branch_name_element is None:
      print("デフォルトブランチ名が見つかりませんでした。")
      return None
    branch_name = branch_name_element.text.strip()

    # README.mdファイルのURLを生成
    repository_name = repository_url.replace('https://github.com/', '')
    readme_url = f"https://raw.githubusercontent.com/{repository_name}/{branch_name}/README.md"

    # README.mdファイルの内容を取得
    readme_response = requests.get(readme_url)
    readme_response.raise_for_status()  # HTTPエラーが発生した場合、例外を発生させる
    readme_content = readme_response.text

    return readme_content

  except requests.exceptions.RequestException as e:
    print(f"リクエストエラー: {e}")
    return None
  except Exception as e:
    print(f"エラー: {e}")
    return None
  
def extract_specific_tag(data, target_tag):
    """
    スクレイピング結果から特定のタグのデータのみを抽出する関数。

    Args:
        data (list): scrape_web_page_with_code 関数の出力結果 (リスト形式)
        target_tag (str): 抽出したいタグ名 (e.g., "p", "h1", "code")

    Returns:
        list: 指定されたタグのデータのみを含むリスト
    """
    extracted_data = []
    for item in data:
        if item["tag_name"] == target_tag:
            extracted_data.append(item)
    return extracted_data

def jsonl_file_to_markdown(input_path, mode="web_page"):
  """
  JSONL形式のデータをMarkTown形式に変換する関数

  Args:
    input_path (str): JSONLファイルのパス
    mode (str): 変換モード。現在、"web_page"のみ対応

  Returns:
    str: MarkTown形式のテキストデータ
  """

  markdown_text = ""
  with open(input_path, 'r') as f:
    for line in f:
      data = json.loads(line)
      if mode == "web_page":
        if data["tag_type"] == "h2":
          markdown_text += f"## {data['context']}\n\n"
        elif data["tag_type"] == "h3":
          markdown_text += f"### {data['context']}\n\n"
        else:  # pタグの場合
          markdown_text += f"{data['context']}\n"
      else:
        raise ValueError("Invalid mode. Only 'web_page' is supported.")

  return markdown_text

def jsonl_to_markdown(jsonl_data):
    markdown_text = ""
    for item in jsonl_data:
        tag_type = item['tag_type']
        context = item['context']

        if tag_type == 'p':
            markdown_text += context + "\n\n"
        elif tag_type == 'h2':
            markdown_text += "## " + context + "\n\n"
        elif tag_type == 'h3':
            markdown_text += "### " + context + "\n\n"

    return markdown_text

def ddgs_text_web_search(query, num_results=10,time_limit=None):
  """
  DuckDuckGo Search APIを使用して、指定されたクエリに基づいてWeb検索を実行し、
  結果をJSON形式で返す関数。

  形式は以下のようになります。
  '''json
  {
  "title": "タイトル",
  "href": "URL",
  "body": "Webページの概要(一部)"
  }
  '''
  """
  with DDGS() as ddgs:
    results = list(ddgs.text(
        keywords=query,      # 検索ワード
        region='jp-jp',       # リージョン 日本は"jp-jp",指定なしの場合は"wt-wt"
        safesearch='off',     # セーフサーチOFF->"off",ON->"on",標準->"moderate"
        timelimit=time_limit,       # 期間指定 指定なし->None,過去1日->"d",過去1週間->"w",
                              # 過去1か月->"m",過去1年->"y"
        max_results=num_results         # 取得件数
    ))

    return results

def google_text_web_search(query, num_results=10,time_limit=None):
  url = f'https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={query}' 
  response = requests.get(url)
  results = response.json()

  try:
    formatted_results = []
    for item in results['items']:
        formatted_item = {
            'title': item['title'],
            'href': item['link'],
            'body': item.get('snippet', ''), # snippetがない場合もあるため、getメソッドを使用
            'displayLink': item['displayLink']
            }
        formatted_results.append(formatted_item)
        res = json.dumps(formatted_results, indent=2, ensure_ascii=False)
  except Exception as e:
    print(f"An error occurred: {e}")
  res = res[:num_results]
  return res

def extract_urls(text):
    """
    テキストからURLを抽出し、リストで返します。

    Args:
        text: URLが含まれている可能性のあるテキスト。

    Returns:
        URLのリスト。URLが見つからない場合は空のリストを返します。
    """
    url_pattern = re.compile(r"https?://[a-zA-Z0-9\-\.:/?#\[\]@!$&'()*+,;=~%]+(?=\s|$|[.,!?;]|(?:[^a-zA-Z0-9\-\.:/?#\[\]@!$&'()*+,;=~%]))")
    urls = url_pattern.findall(text)
    return urls

def generate_character_ngrams(text, i, j, binary=False):
    """文字列から指定した文字数のn-gramを生成する関数。"""
    ngrams = []
    for n in range(i, j + 1):
        for k in range(len(text) - n + 1):
            ngram = text[k:k + n]
            ngrams.append(ngram)
    if binary:
        ngrams = list(set(ngrams))
    return ngrams

def preprocess_func(text):
    i, j = 1, 3
    if len(text) < i:
        return [text]
    return generate_character_ngrams(text, i, j, True)

def TF_IDF_score_contexts(json_data, keyword):
    """
    JSONデータのリストとキーワードを受け取り、TF-IDFを用いてコンテキストをスコアリングする。

    Args:
        json_data: JSONデータのリスト. 各要素は{"count": "カウントされた数", "context": "スコアリング対象の文章"}の形式.(contextのみあればOK)
        keyword: スコアリングに使用するキーワード.

    Returns:
        スコアリングされたJSONデータのリスト. 各要素は{"count": "カウントされた数", "context": "スコアリング対象の文章", "score": スコア}の形式.
        キーワードが空の場合、またはjson_dataが空の場合、元のjson_dataを返す。
    """
    if not keyword or not json_data:
        return json_data

    contexts = [item["context"] for item in json_data]
    retriever = TFIDFRetriever.from_texts(contexts, tfidf_params={"analyzer": preprocess_func})

    query_vec = retriever.vectorizer.transform([keyword])
    scores = cosine_similarity(retriever.tfidf_array, query_vec).reshape((-1,))

    scored_json_data = []
    for i, item in enumerate(json_data):
        new_item = item.copy()  # 元のデータを変更しないようにコピー
        new_item["score"] = float(scores[i]) # floatに変換
        scored_json_data.append(new_item)

    return scored_json_data

def bm25_score_contexts(json_data, keyword):
    """
    JSONデータのリストとキーワードを受け取り、BM25を用いてコンテキストをスコアリングする。

    Args:
        json_data: JSONデータのリスト. 各要素は{"count": "カウントされた数", "context": "スコアリング対象の文章"}の形式.(contextのみあればOK)
        keyword: スコアリングに使用するキーワード.

    Returns:
        スコアリングされたJSONデータのリスト. 各要素は{"count": "カウントされた数", "context": "スコアリング対象の文章", "score": スコア}の形式.
        キーワードが空の場合、またはjson_dataが空の場合、元のjson_dataを返す。
    """
    if not keyword or not json_data:
        return json_data

    contexts = [item["context"] for item in json_data]
    retriever = BM25Retriever.from_texts(contexts, preprocess_func=preprocess_func) 

    scores = retriever.vectorizer.get_scores(preprocess_func(keyword))

    scored_json_data = []
    for i, item in enumerate(json_data):
        new_item = item.copy()
        new_item["score"] = float(scores[i])
        scored_json_data.append(new_item)

    return scored_json_data

def generate_markdown_4_RAG(data, keywords, top_p_percentage=50,tfidf_pre_filter_percentage=80,include_code=False):
    """
    JSONデータをMarkdown形式に変換し、TF-IDFで大まかに絞り込み、BM25で最終的に絞り込む関数。

    Args:
        data (list): scrape_web_page_with_code 関数の出力結果
        keywords (str): スコアリングに使用するキーワード
        top_p_percentage (int): BM25の上位何%のpタグを使用するか (デフォルト: 50)
        include_code (bool): codeタグを含めるかどうか (デフォルト: False)
        tfidf_pre_filter_percentage (int): TF-IDFで事前に絞り込む割合 (上位何%残すか) デフォルトは80%

    Returns:
        str: Markdown形式のテキスト
    """

    p_tags = extract_specific_tag(data, "p")

    # 1. TF-IDFで事前フィルタリング
    tfidf_scored_p_tags = TF_IDF_score_contexts(p_tags, keywords)
    sorted_tfidf_p_tags = sorted(tfidf_scored_p_tags, key=lambda x: x["score"], reverse=True)
    num_tfidf_p_tags_to_keep = int(len(sorted_tfidf_p_tags) * tfidf_pre_filter_percentage / 100)
    pre_filtered_p_tags = sorted_tfidf_p_tags[:num_tfidf_p_tags_to_keep]
    

    # 2. BM25でスコアリング & 最終フィルタリング
    bm25_scored_p_tags = bm25_score_contexts(pre_filtered_p_tags, keywords) # TF-IDFで絞り込んだ結果をBM25にかける
    sorted_bm25_p_tags = sorted(bm25_scored_p_tags, key=lambda x: x["score"], reverse=True)
    num_bm25_p_tags_to_use = int(len(sorted_bm25_p_tags) * top_p_percentage / 100)
    selected_p_tags = sorted_bm25_p_tags[:num_bm25_p_tags_to_use]  # 最終的に使用するpタグ


    markdown_text = ""
    for item in data:
        if item["tag_name"] in ("h1", "h2", "h3"):
            markdown_text += f"#{'#' * int(item['tag_name'][1:])} {item['context']}\n\n"
        elif item["tag_name"] == "p" and any(item["count"] == p["count"] for p in selected_p_tags):  # "count"キーの値で比較
            markdown_text += f"{item['context']}\n\n"
        elif item["tag_name"] == "code" and include_code:
            markdown_text += f"\n{item['context']}\n\n\n"

    return markdown_text