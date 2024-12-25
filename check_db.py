from app import db, ModelName, SystemPrompt, User, Chat, Message
import json

def check_database():
    print("\n=== ModelName テーブルの内容 ===")
    models = ModelName.query.all()
    for model in models:
        print(f"ID: {model.id}, Name: {model.name}, Display Name: {model.display_name}")

    print("\n=== SystemPrompt テーブルの内容 ===")
    prompts = SystemPrompt.query.all()
    for prompt in prompts:
        print(f"Model Name: {prompt.model_name}")
        print(f"Prompt: {prompt.prompt[:100]}...")  # 最初の100文字のみ表示
        print("-" * 50)

def clean_model_names():
    print("\n=== ModelNameテーブルのクリーンアップを開始 ===")
    
    # 削除する古い名前のリスト
    old_names = [
        "ビジネス向け要件定義書",
        "金額提示相談AI",
        "要件定義書のヒアリングAI"
    ]
    
    # 古いエントリを削除
    for name in old_names:
        model = ModelName.query.filter_by(name=name).first()
        if model:
            print(f"重複したModelNameエントリを削除: ID={model.id}, Name={model.name}")
            db.session.delete(model)
    
    db.session.commit()
    print("重複したModelNameエントリの削除完了")

def update_system_prompts():
    print("\n=== SystemPromptの名称を更新 ===")
    
    # 名称の変更マッピング
    name_updates = {
        "要件定義書のヒアリングAI": "1.要件定義書のヒアリングAI",
        "ビジネス向け要件定義書": "2.ビジネス向け要件定義書",
        "エンジニア向け要件定義書": "3.エンジニア向け要件定義書",
        "金額提示相談AI": "4.金額提示相談AI"
    }
    
    # 現在のプロンプトを取得
    prompts = SystemPrompt.query.all()
    prompts_dict = {}
    
    # プロンプトの内容を保存し、必要に応じて名称を更新
    for prompt in prompts:
        new_name = name_updates.get(prompt.model_name, prompt.model_name)
        prompts_dict[new_name] = prompt.prompt
    
    # 一旦すべてのプロンプトを削除
    for prompt in prompts:
        db.session.delete(prompt)
    db.session.commit()
    print("既存のSystemPromptをすべて削除しました")
    
    # 希望の順序でプロンプトを再作成
    desired_order = [
        "VOLTMIND AI",
        "税務GPT",
        "薬科GPT",
        "敬語の鬼",
        "節税商品説明AI",
        "IT用語説明AI",
        "1.要件定義書のヒアリングAI",
        "2.ビジネス向け要件定義書",
        "3.エンジニア向け要件定義書",
        "4.金額提示相談AI"
    ]
    
    for model_name in desired_order:
        if model_name in prompts_dict:
            new_prompt = SystemPrompt(
                model_name=model_name,
                prompt=prompts_dict[model_name]
            )
            db.session.add(new_prompt)
    
    db.session.commit()
    print("SystemPromptを新しい名称で再作成しました")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        print("=== 変更前のデータベースの状態 ===")
        check_database()
        clean_model_names()
        update_system_prompts()
        print("\n=== 変更後のデータベースの状態 ===")
        check_database()
