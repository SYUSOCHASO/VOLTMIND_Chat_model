from . import funs
from . import search_funs
import traceback

def process_web_search(user_input, model):
    """
    @webタグを使用したWeb検索とRAG処理を行う関数

    Args:
        user_input (str): ユーザーの入力テキスト
        model: 使用するモデル

    Returns:
        str: アシスタントの応答メッセージ
    """
    try:
        search_query = user_input[5:]  # '@web '以降のテキストを取得
        if not search_query.strip():
            return "検索クエリが空です。@webの後に検索したい内容を入力してください。"

        search_results = []
        make_serch_keyword_SP = """
        あなたはgoogle検索などで使われる検索キーワードを作成するのが世界で一番とくいな検索エージェントです。
        以下のルールとコツを守りながら検索キーワードを出力してください。

        ## ルール
        - 検索キーワードは2~3個の単語や語句で構成されています。
        - 戦略を立てて検索キーワードを作成してください。
        - できるだけ、具体的であり欲しい情報を得られるワードにしてください。

        ## 出力例
        この情報を効果的に得るためには00の概要を検索するべきだと考えます。
        <search_keyword>00 概要</search_keyword>
        """

        try:
            search_keyword_response = funs.integration_chat_lc(
                f"以下の質問を元にweb検索をするための検索キーワードを作成してください。\n\n\n\n## ユーザーの質問:\n{search_query}",
                make_serch_keyword_SP,
                model
            )
            search_keyword = search_query  # デフォルト値として元のクエリを使用
            if search_keyword_response:
                extracted_keyword = funs.extract_tag(search_keyword_response, "text", "search_keyword")
                if extracted_keyword:
                    search_keyword = extracted_keyword
        except Exception as e:
            print(f"キーワード生成エラー: {str(e)}")
            search_keyword = search_query  # エラー時は元のクエリを使用

        try:
            search_url_list = search_funs.ddgs_text_web_search(search_keyword, 3)
            if not search_url_list:
                return "検索結果が見つかりませんでした。別のキーワードで試してください。"

            for url in search_url_list:
                try:
                    search_result_list = search_funs.scrape_web_page_4_RAG(url["href"])
                    search_result_markdown = search_funs.generate_markdown_4_RAG(search_result_list, search_keyword)
                    search_results.append({
                        "url": url["href"],
                        "title": url.get("title", "タイトルなし"),
                        "search_result_markdown": search_result_markdown
                    })
                except Exception as e:
                    print(f"ページ処理エラー ({url['href']}): {str(e)}")
                    continue

            if not search_results:
                return "検索結果の処理中にエラーが発生しました。別のキーワードで試してください。"

        except Exception as e:
            print(f"検索エラー: {str(e)}")
            return f"検索処理中にエラーが発生しました: {str(e)}"

        SP_4_RAG = """
あなたは検索機能を備えた世界レベルのchatエージェントです。以下のルールに乗っ取りユーザーの質問に対応してください。

## ルール
- できる限りユーザーには親切に接する
- 数学的問題を解く必要がある場合、すべての作業を明示的に示し、正式な表記にはLaTeXを使用し、詳細な証明を提供すること。各ステップを論理的に説明し、使用する定理や法則の根拠を明確にすること。
- 論理的に回答をする必要がある場合にはステップバイステップで考えて下さい。
- 情報どうしのつながりを考えて出力してください。
        """

        RAG_PROMPT = f"""
あなたの仕事はユーザーの質問にweb検索をした情報を元に回答をすることです。

## ユーザーの質問

{user_input}
        """

        for i in search_results:
            RAG_PROMPT += f"""
            \n\n
ソース元URL:{i["url"]}
ソースページのタイトル:{i["title"]}

ページ内容:
```markdown
{i["search_result_markdown"]}
```
            """

        return RAG_PROMPT

    except Exception as e:
        print(f"予期せぬエラー: {str(e)}")
        print(traceback.format_exc())
        return f"エラーが発生しました: {str(e)}"

def process_url_search(user_input, model):
    """
    @urlタグを使用したURL検索とRAG処理を行う関数

    Args:
        user_input (str): ユーザーの入力テキスト
        model: 使用するモデル

    Returns:
        str: アシスタントの応答メッセージ
    """
    try:
        search_query = user_input[5:]  # '@url '以降のテキストを取得
        if not search_query.strip():
            return "URLが空です。@urlの後にURLを入力してください。"

        search_results = []
        urls = search_funs.extract_urls(search_query)
        
        if not urls:
            return "有効なURLが見つかりませんでした。正しいURLを入力してください。"

        for url in urls:
            try:
                search_result_list = search_funs.scrape_web_page_4_RAG(url)
                search_result_markdown = search_funs.generate_markdown_4_RAG(search_result_list, "")
                search_results.append({
                    "url": url,
                    "title": "ページタイトル",
                    "search_result_markdown": search_result_markdown
                })
            except Exception as e:
                print(f"ページ処理エラー ({url}): {str(e)}")
                continue

        if not search_results:
            return "URLの処理中にエラーが発生しました。別のURLで試してください。"

        SP_4_RAG = """
あなたは検索機能を備えた世界レベルのchatエージェントです。以下のルールに乗っ取りユーザーの質問に対応してください。

## ルール
- できる限りユーザーには親切に接する
- 数学的問題を解く必要がある場合、すべての作業を明示的に示し、正式な表記にはLaTeXを使用し、詳細な証明を提供すること。各ステップを論理的に説明し、使用する定理や法則の根拠を明確にすること。
- 論理的に回答をする必要がある場合にはステップバイステップで考えて下さい。
- 情報どうしのつながりを考えて出力してください。
        """

        RAG_PROMPT = f"""
あなたの仕事はユーザーの質問にweb検索をした情報を元に回答をすることです。

## ユーザーの質問

{user_input}
        """

        for i in search_results:
            RAG_PROMPT += f"""
\n\n
ソース元URL:{i["url"]}
ソースページのタイトル:{i["title"]}

ページ内容:
```markdown
{i["search_result_markdown"]}
```
            """

        return RAG_PROMPT

    except Exception as e:
        print(f"予期せぬエラー: {str(e)}")
        print(traceback.format_exc())
        return f"エラーが発生しました: {str(e)}"