import os
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, abort, send_from_directory
from functions import funs  # funs.pyをインポート
from functions import agent
from functions import web_search_rag
import base64
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import uuid
from flask_cors import CORS  # 追加

app = Flask(__name__)
CORS(app)  # 追加：CORSの設定
app.config['SECRET_KEY'] = 'your-secret-key'  # セッション管理用の秘密鍵
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ユーザーモデルの定義
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # 管理者フラグを追加
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')  # カスケード削除を追加

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# チャット履歴モデルの定義
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')
    images = db.relationship('ChatImage', backref='chat', lazy=True, cascade='all, delete-orphan')

# モデル名管理用のモデル
class ModelName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 内部で使用する名前
    display_name = db.Column(db.String(50), nullable=False)  # 表示用の名前
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

# メッセージモデルの定義
class SystemPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), unique=True, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    model = db.Column(db.String(20))  # モデル名を保存するカラムを追加
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_id = db.Column(db.Integer, db.ForeignKey('chat_image.id'), nullable=True)  # 画像との関連付け

# 画像モデルの定義
class ChatImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # 保存されたファイル名
    original_filename = db.Column(db.String(255), nullable=False)  # オリジナルのファイル名
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    messages = db.relationship('Message', backref='image', lazy=True)

# 管理者権限の確認デコレータ
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# アップロードされた画像を保存するディレクトリ
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# funs.pyのSYSTEM_PROMPTを使用
SYSTEM_PROMPT = funs.SYSTEM_PROMPT

def get_system_prompt(model_name):
    try:
        # データベースからプロンプトを取得
        system_prompt = SystemPrompt.query.filter_by(model_name=model_name).first()
        if system_prompt:
            print(f"Found system prompt for {model_name} in database")
            return system_prompt.prompt
        else:
            print(f"No system prompt found for {model_name} in database")
            return "システムプロンプトが設定されていません。"
    except Exception as e:
        print(f"Error getting system prompt: {str(e)}")
        return "システムプロンプトの取得中にエラーが発生しました。"

# モデルに対応する関数の辞書
model_functions = {
    "ollama": funs.ollama_chat,
    "llamacpp": funs.llamacpp_chat,
    "pplx": funs.pplx_chat,
    "claude": funs.claude_chat,
    "groq": funs.groq_chat,
    "gpt": funs.gpt_chat,
    "gemini": funs.gemini_chat,
    "xai": funs.xai_chat,
    "VOLTMIND AI": agent.VOLTMINDBOT,
    "税務GPT": agent.税務GPT,
    "薬科GPT": agent.薬科GPT,
    "敬語の鬼": agent.敬語の鬼,
    "節税商品説明AI": agent.節税商品説明AI,
    "IT用語説明AI": agent.IT用語説明AI,
    "1.要件定義書のヒアリングAI": agent.要件定義書のヒアリングAI,
    "2.ビジネス向け要件定義書": agent.ビジネス向け要件定義書,
    "3.エンジニア向け要件定義書": agent.エンジニア向け要件定義書,
    "4.金額提示相談AI": agent.金額提示相談AI,
}

# 画像処理用の関数辞書
image_model_functions = {
    "ollama": funs.img_inf_ollama,
    "claude": funs.img_inf_claude,
    "groq": funs.img_inf_groq,
    "gpt": funs.img_inf_gpt,
}

# 管理画面
@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.all()
    return render_template('admin.html', users=users)

# 管理者用ユーザー追加API
@app.route('/admin/add_user', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "error": "ユーザー名とパスワードは必須です"}), 400
    
    if len(password) < 8:
        return jsonify({"success": False, "error": "パスワードは8文字以上で入力してください"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "error": "このユーザー名は既に使用されています"}), 400
    
    try:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({"success": True, "message": "ユーザーを追加しました"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# 管理者用ユーザー削除API
@app.route('/admin/delete_user/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # 管理者は削除できない
    if user.is_admin:
        return jsonify({"success": False, "error": "管理者ユーザーは削除できません"}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True, "message": "ユーザーを削除しました"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# 管理者用チャット削除API
@app.route('/admin/delete_chat/<int:chat_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    try:
        # チャットに関連する画像ファイルを削除
        for image in chat.images:
            image_path = os.path.join(UPLOAD_FOLDER, image.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(chat)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('ユーザー名またはパスワードが間違っています')
    return render_template('login.html')

# 新規登録ページ
@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if len(password) < 8:
            flash('パスワードは8文字以上で入力してください')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('パスワードが一致しません')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('このユーザー名は既に使用されています')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('ユーザーの登録が完了しました')
        return redirect(url_for('admin'))
    return render_template('register.html')

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    # ユーザーのチャット履歴を取得
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    # モデル名一覧を取得
    models = ModelName.query.all()
    model_names = [{
        "name": model.name,
        "display_name": model.display_name
    } for model in models] if models else [
        {"name": name, "display_name": display_name}
        for name, display_name in DEFAULT_MODEL_NAMES.items()
    ]
    return render_template("index.html", chats=chats, models=model_names)

@app.route("/get_chat/<int:chat_id>")
@login_required
def get_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    return jsonify({
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "model": msg.model,
                "image": {
                    "filename": msg.image.original_filename,
                    "url": url_for('uploaded_file', filename=msg.image.filename)
                } if msg.image_id else None
            } for msg in messages
        ]
    })

@app.route("/update_chat_title/<int:chat_id>", methods=["PUT"])
@login_required
def update_chat_title(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    new_title = data.get('title')
    if not new_title:
        return jsonify({"error": "Title is required"}), 400
    
    try:
        chat.title = new_title
        db.session.commit()
        return jsonify({"message": "Title updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/delete_chat/<int:chat_id>", methods=["DELETE"])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # チャットに関連する画像ファイルを削除
        for image in chat.images:
            image_path = os.path.join(UPLOAD_FOLDER, image.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(chat)
        db.session.commit()
        return jsonify({"message": "Chat deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# アップロードされたファイルを提供するルート
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# システムプロンプトの取得API
@app.route("/admin/system_prompts", methods=["GET"])
@login_required
@admin_required
def get_system_prompts():
    prompts = SystemPrompt.query.all()
    result = []
    for prompt in prompts:
        # モデル名の表示名を取得
        model = ModelName.query.filter_by(name=prompt.model_name).first()
        display_name = model.display_name if model else prompt.model_name
        
        result.append({
            "id": prompt.id,
            "model_name": prompt.model_name,
            "display_name": display_name,
            "prompt": prompt.prompt,
            "updated_at": prompt.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result)

# システムプロンプトの更新API
@app.route("/admin/system_prompts/<model_name>", methods=["PUT"])
@login_required
@admin_required
def update_system_prompt(model_name):
    data = request.get_json()
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "プロンプトは必須です"}), 400
    
    system_prompt = SystemPrompt.query.filter_by(model_name=model_name).first()
    if system_prompt:
        system_prompt.prompt = prompt
    else:
        system_prompt = SystemPrompt(model_name=model_name, prompt=prompt)
        db.session.add(system_prompt)
    
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "システムプロンプトを更新しました"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    chat_id = request.form.get('chat_id')
    user_input = request.form["message"]
    model = request.form.get('model', 'groq')
    
    # モデル名の表示名を取得
    model_name = ModelName.query.filter_by(name=model).first()
    display_model = model_name.display_name if model_name else model
    
    # 画像ファイルの処理
    image_file = request.files.get('image')
    has_image = image_file is not None and image_file.filename != ''

    try:
        # 新しいチャットの場合
        if not chat_id:
            new_chat = Chat(
                title=user_input[:50] + "..." if len(user_input) > 50 else user_input,
                user_id=current_user.id
            )
            db.session.add(new_chat)
            db.session.commit()
            chat_id = new_chat.id
        else:
            chat = Chat.query.get(chat_id)
            if not chat or chat.user_id != current_user.id:
                return jsonify({"error": "Unauthorized"}), 403

        # 画像の保存と処理
        chat_image = None
        if has_image:
            # ユニークなファイル名を生成
            file_extension = os.path.splitext(image_file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # 画像を保存
            image_file.save(image_path)
            
            # データベースに画像情報を保存
            chat_image = ChatImage(
                filename=unique_filename,
                original_filename=image_file.filename,
                chat_id=chat_id
            )
            db.session.add(chat_image)
            db.session.commit()

        # ユーザーメッセージを保存
        user_message = Message(
            content=user_input,
            role='user',
            chat_id=chat_id,
            image_id=chat_image.id if chat_image else None
        )
        db.session.add(user_message)
        db.session.commit()

        # 画像処理
        if has_image:
            if model in image_model_functions:
                try:
                    assistant_message_content = image_model_functions[model](user_input, image_path)
                except Exception as e:
                    assistant_message_content = f"画像処理中にエラーが発生しました: {str(e)}"
            else:
                model = "gpt"
                try:
                    assistant_message_content = image_model_functions[model](user_input, image_path)
                    assistant_message_content = "選択されたモデルは画像処理に対応していないため、GPT-4 Visionで処理しました。\n\n" + assistant_message_content
                except Exception as e:
                    assistant_message_content = f"画像処理中にエラーが発生しました: {str(e)}"
        else:
            # @webまたは@urlで始まる場合のRAG処理
            if user_input.startswith("@web"):
                rag_prompt = web_search_rag.process_web_search(user_input, model)
                print(rag_prompt)
                assistant_message_content = model_functions[model]([{"role": "user", "content": rag_prompt}])
            elif user_input.startswith("@url"):
                rag_prompt = web_search_rag.process_url_search(user_input, model)
                assistant_message_content = model_functions[model]([{"role": "user", "content": rag_prompt}])
            else:
                # 通常のテキストチャット
                messages_list = [
                    {"role": msg.role, "content": msg.content}
                    for msg in Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
                ]
                # システムプロンプトを取得
                system_prompt = get_system_prompt(model)
                # システムプロンプトを関数に渡す
                assistant_message_content = model_functions[model](messages_list, system_prompt)

        # アシスタントの応答を保存
        assistant_message = Message(
            content=assistant_message_content,
            role='assistant',
            model=model,
            chat_id=chat_id
        )
        db.session.add(assistant_message)
        db.session.commit()

        return jsonify({
            "message": assistant_message_content,
            "chat_id": chat_id,
            "model": display_model,
            "image": {
                "filename": chat_image.original_filename,
                "url": url_for('uploaded_file', filename=chat_image.filename)
            } if chat_image else None
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# モデル名一覧を取得するAPI
@app.route("/admin/model_names", methods=["GET"])
@login_required
@admin_required
def get_model_names():
    models = ModelName.query.all()
    return jsonify([{
        "id": model.id,
        "name": model.name,
        "display_name": model.display_name,
        "updated_at": model.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    } for model in models])

# モデル名を更新するAPI
@app.route("/admin/model_names/<name>", methods=["PUT"])
@login_required
@admin_required
def update_model_name(name):
    data = request.get_json()
    display_name = data.get('display_name')
    
    if not display_name:
        return jsonify({"success": False, "error": "表示名は必須です"}), 400
    
    model = ModelName.query.filter_by(name=name).first()
    if model:
        model.display_name = display_name
    else:
        model = ModelName(name=name, display_name=display_name)
        db.session.add(model)
    
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "モデル名を更新しました"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

from functions.default_prompts import DEFAULT_SYSTEM_PROMPTS

# デフォルトのモデル名マッピング
DEFAULT_MODEL_NAMES = {
    "groq": "Groq",
    "gpt": "ChatGPT",
    "gemini": "Gemini",
    "claude": "Claude",
    "xai": "xAI",
    "VOLTMIND AI": "VOLTMIND AI",
    "税務GPT": "税務GPT",
    "薬科GPT": "薬科GPT",
    "敬語の鬼": "敬語の鬼",
    "節税商品説明AI": "節税商品説明AI",
    "IT用語説明AI": "IT用語説明AI",
    "1.要件定義書のヒアリングAI": "1.要件定義書のヒアリングAI",
    "2.ビジネス向け要件定義書": "2.ビジネス向け要件定義書",
    "3.エンジニア向け要件定義書": "3.エンジニア向け要件定義書",
    "4.金額提示相談AI": "4.金額提示相談AI"
}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        # モデル名の初期化（データベースが空の場合のみ）
        try:
            existing_models_count = ModelName.query.count()
            if existing_models_count == 0:
                print("No model names found. Initializing with defaults...")
                for name, display_name in DEFAULT_MODEL_NAMES.items():
                    new_model = ModelName(name=name, display_name=display_name)
                    db.session.add(new_model)
                db.session.commit()
                print("Model names initialized successfully")
            else:
                print(f"Found {existing_models_count} existing model names. Skipping initialization.")
        except Exception as e:
            print(f"Error checking/initializing model names: {str(e)}")
            db.session.rollback()
        # 管理者ユーザーが存在しない場合は作成
        admin_user = User.query.filter_by(username='voltmind_admin').first()
        if not admin_user:
            admin_user = User(username='voltmind_admin', is_admin=True)
            admin_user.set_password('NK19931994616224')
            db.session.add(admin_user)
            db.session.commit()
        
        # システムプロンプトの初期化（データベースが空の場合のみ）
        try:
            # 既存のプロンプトを確認
            existing_prompts_count = SystemPrompt.query.count()
            
            # プロンプトが1つも存在しない場合のみ、デフォルト値を設定
            if existing_prompts_count == 0:
                print("No system prompts found. Initializing with defaults...")
                for model_name, prompt_text in DEFAULT_SYSTEM_PROMPTS.items():
                    new_prompt = SystemPrompt(model_name=model_name, prompt=prompt_text)
                    db.session.add(new_prompt)
                db.session.commit()
                print("System prompts initialized successfully")
            else:
                print(f"Found {existing_prompts_count} existing system prompts. Skipping initialization.")
        except Exception as e:
            print(f"Error checking/initializing system prompts: {str(e)}")
            db.session.rollback()
    
    app.run(debug=True, port=5001)
