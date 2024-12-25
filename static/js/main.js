document.addEventListener('DOMContentLoaded', function() {
    const elements = {
        sidebar: document.getElementById('sidebar'),
        toggleSidebar: document.getElementById('toggle-sidebar'),
        mainContent: document.getElementById('main-content'),
        newChatBtn: document.getElementById('new-chat-btn'),
        chatBox: document.getElementById('chat-box'),
        messageInput: document.getElementById('message'),
        sendBtn: document.getElementById('send-btn'),
        themeToggle: document.getElementById('theme-toggle'),
        imageUploadBtn: document.getElementById('image-upload-btn'),
        imageInput: document.getElementById('image-input'),
        imagePreview: document.getElementById('image-preview'),
        imagePreviewContainer: document.getElementById('image-preview-container'),
        removeImageBtn: document.getElementById('remove-image-btn'),
        loading: document.querySelector('.loading'),
        modelSelector: document.getElementById('model-selector'),
        logoutBtn: document.querySelector('.logout-btn'),
        chatHeader: document.getElementById('chat-header'),
        headerToggle: document.getElementById('header-toggle'),
        chatHistory: document.getElementById('chat-history')
    };

    // スクロールボタンの機能を追加（ここに新しいコードを追加）
    const scrollLeftBtn = document.getElementById('scroll-left');
    const scrollRightBtn = document.getElementById('scroll-right');
    const modelSelector = document.getElementById('model-selector');

    // スクロール量を設定（必要に応じて調整）
    const scrollAmount = 200;

    scrollLeftBtn.addEventListener('click', () => {
        modelSelector.scrollLeft -= scrollAmount;
        updateScrollButtons();
    });

    scrollRightBtn.addEventListener('click', () => {
        modelSelector.scrollLeft += scrollAmount;
        updateScrollButtons();
    });

    // スクロールボタンの有効/無効を更新
    function updateScrollButtons() {
        scrollLeftBtn.disabled = modelSelector.scrollLeft <= 0;
        scrollRightBtn.disabled = 
            modelSelector.scrollLeft >= 
            modelSelector.scrollWidth - modelSelector.clientWidth;
    }

    // スクロール時にボタンの状態を更新
    modelSelector.addEventListener('scroll', updateScrollButtons);

    // 初期状態でボタンの状態を設定
    updateScrollButtons();

    // ウィンドウリサイズ時にもボタンの状態を更新
    window.addEventListener('resize', updateScrollButtons);

    // ビューポートの高さを設定する関数
    function setVH() {
        let vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }

    // プレースホルダーを更新する関数
    function updatePlaceholder() {
        const messageTextarea = document.getElementById('message');
        if (window.innerWidth <= 768) {
            messageTextarea.placeholder = messageTextarea.getAttribute('data-mobile-placeholder');
        } else {
            messageTextarea.placeholder = "メッセージを入力...【Ctrl(Command)+Enterで送信】";  // ここを変更
        }
    }

    // 初期化時とリサイズ時にビューポートの高さとプレースホルダーを設定
    window.addEventListener('DOMContentLoaded', () => {
        setVH();
        updatePlaceholder();
    });
    window.addEventListener('resize', () => {
        setVH();
        updatePlaceholder();
    });
    window.addEventListener('orientationchange', setVH);

    // キーボード表示時のスクロール防止
    document.addEventListener('focusin', (e) => {
        if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') {
            document.body.style.position = 'fixed';
            document.body.style.width = '100%';
        }
    });

    document.addEventListener('focusout', (e) => {
        if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') {
            document.body.style.position = '';
            document.body.style.width = '';
        }
    });

    // 複数選択モードの状態管理
    let isMultiSelectMode = false;
    let selectedChats = new Set();
    let longPressTimer;
    const LONG_PRESS_DURATION = 500; // 長押しの時間（ミリ秒）

    // 複数選択モードのUI要素
    const multiSelectUI = document.createElement('div');
    multiSelectUI.className = 'multi-select-ui';
    multiSelectUI.innerHTML = `
        <div class="multi-select-controls">
            <span class="selected-count">0 件選択中</span>
            <button class="cancel-select-btn">キャンセル</button>
            <button class="delete-selected-btn">削除</button>
        </div>
    `;
    multiSelectUI.style.display = 'none';
    elements.sidebar.insertBefore(multiSelectUI, elements.chatHistory);

    // 複数選択モードの切り替え
    function toggleMultiSelectMode(enabled) {
        isMultiSelectMode = enabled;
        multiSelectUI.style.display = enabled ? 'block' : 'none';
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.toggle('multi-select-mode', enabled);
        });
        if (!enabled) {
            selectedChats.clear();
            updateSelectedCount();
        }
    }

    // 選択数の更新
    function updateSelectedCount() {
        const count = selectedChats.size;
        multiSelectUI.querySelector('.selected-count').textContent = `${count} 件選択中`;
        multiSelectUI.querySelector('.delete-selected-btn').disabled = count === 0;
    }

    // チャットアイテムの選択状態を切り替え
    function toggleChatSelection(chatItem) {
        const chatId = chatItem.dataset.chatId;
        if (selectedChats.has(chatId)) {
            selectedChats.delete(chatId);
            chatItem.classList.remove('selected');
        } else {
            selectedChats.add(chatId);
            chatItem.classList.add('selected');
        }
        updateSelectedCount();
    }

    // 選択したチャットの削除
    async function deleteSelectedChats() {
        if (!confirm(`選択した ${selectedChats.size} 件のチャットを削除してもよろしいですか？`)) {
            return;
        }

        const deletePromises = Array.from(selectedChats).map(async chatId => {
            try {
                const response = await fetch(`/delete_chat/${chatId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) throw new Error('チャットの削除に失敗しました');

                const chatItem = document.querySelector(`.chat-item[data-chat-id="${chatId}"]`);
                if (chatItem) {
                    chatItem.remove();
                }

                if (currentChatId === chatId) {
                    currentChatId = null;
                    elements.chatBox.innerHTML = '';
                }
            } catch (error) {
                console.error('エラー:', error);
                showError('チャットの削除に失敗しました');
            }
        });

        await Promise.all(deletePromises);
        toggleMultiSelectMode(false);
    }

    // キャンセルボタンのイベントリスナー
    multiSelectUI.querySelector('.cancel-select-btn').addEventListener('click', () => {
        toggleMultiSelectMode(false);
    });

    // 削除ボタンのイベントリスナー
    multiSelectUI.querySelector('.delete-selected-btn').addEventListener('click', deleteSelectedChats);

    // 画像アップロード関連のイベントリスナーを追加
    elements.imageUploadBtn.addEventListener('click', () => {
        elements.imageInput.click();
    });

    // 画像が選択された時の処理
    elements.imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                elements.imagePreview.src = e.target.result;
                elements.imagePreviewContainer.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });

    // 画像削除ボタンの処理
    elements.removeImageBtn.addEventListener('click', () => {
        elements.imageInput.value = '';
        elements.imagePreview.src = '';
        elements.imagePreviewContainer.style.display = 'none';
    });

    // ヘッダーの表示状態を管理する関数を追加
    function toggleHeader() {
        const isHidden = elements.chatHeader.classList.toggle('header-hidden');
        elements.headerToggle.classList.toggle('active', isHidden);
        // 山形アイコンの向きを変更
        const chevronIcon = elements.headerToggle.querySelector('i');
        if (isHidden) {
            chevronIcon.className = 'fas fa-chevron-down'; // ヘッダーが隠れている時は下向き
        } else {
            chevronIcon.className = 'fas fa-chevron-up'; // ヘッダーが表示されている時は上向き
        }
        localStorage.setItem('headerHidden', isHidden);
    }

    // 保存されたヘッダーの状態を復元
    const savedHeaderState = localStorage.getItem('headerHidden');
    if (savedHeaderState === 'true') {
        elements.chatHeader.classList.add('header-hidden');
        elements.headerToggle.classList.add('active');
        // 初期状態の山形アイコンの向きを設定
        const chevronIcon = elements.headerToggle.querySelector('i');
        chevronIcon.className = 'fas fa-chevron-down';
    }

    // ヘッダートグルボタンのイベントリスナーを追加
    elements.headerToggle.addEventListener('click', toggleHeader);

    // 設定モーダルの要素
    const settingsModal = document.getElementById('settings-modal');
    const settingsBtn = document.getElementById('settings-btn');
    const closeModal = document.querySelector('.close-modal');
    const accentColorInput = document.getElementById('accent-color');
    const colorValue = document.querySelector('.color-value');
    const resetColorBtn = document.getElementById('reset-color');

    const DEFAULT_COLOR = '#FFD700';

    // 保存された色を読み込む
    const savedColor = localStorage.getItem('accentColor') || DEFAULT_COLOR;
    accentColorInput.value = savedColor;
    colorValue.textContent = savedColor;
    updateThemeColor(savedColor);

    // 設定モーダルのモデル順序管理機能
    function initializeModelOrderSettings() {
        const modelOrderList = document.querySelector('.model-order-list');
        if (!modelOrderList) return;

        // 現在のモデル順序を取得
        const models = Array.from(document.querySelectorAll('#model-selector .model-option')).map(radio => ({
            value: radio.value,
            label: radio.nextElementSibling.textContent.trim()
        }));

        // モデル順序リストを生成
        models.forEach(model => {
            const item = document.createElement('div');
            item.className = 'model-order-item';
            item.setAttribute('data-model', model.value);
            item.innerHTML = `
                <i class="fas fa-grip-vertical"></i>
                ${model.label}
            `;
            modelOrderList.appendChild(item);
        });

        // ドラッグ&ドロップの設定
        let draggedItem = null;
        let initialY = 0;
        let initialScroll = 0;

        modelOrderList.addEventListener('touchstart', handleTouchStart, { passive: false });
        modelOrderList.addEventListener('touchmove', handleTouchMove, { passive: false });
        modelOrderList.addEventListener('touchend', handleTouchEnd);

        function handleTouchStart(e) {
            const item = e.target.closest('.model-order-item');
            if (!item) return;

            draggedItem = item;
            item.classList.add('dragging');
            
            const touch = e.touches[0];
            initialY = touch.clientY - item.getBoundingClientRect().top;
            initialScroll = modelOrderList.scrollTop;

            // タッチイベントのデフォルト動作を防止
            e.preventDefault();
        }

        function handleTouchMove(e) {
            if (!draggedItem) return;
            e.preventDefault();
        
            const touch = e.touches[0];
            const containerRect = modelOrderList.getBoundingClientRect();
            
            // スクロール位置を考慮した位置計算の修正
            const y = touch.clientY - containerRect.top + modelOrderList.scrollTop;
            
            // ドラッグ要素の位置を更新
            draggedItem.style.position = 'absolute';
            draggedItem.style.top = `${y - draggedItem.offsetHeight / 2}px`; // 中央に配置されるように調整
            draggedItem.style.width = `${containerRect.width - 20}px`;
            draggedItem.style.zIndex = '1000'; // 他の要素の上に表示されるように
        
            // スクロール処理
            const scrollThreshold = 50;
            if (touch.clientY < containerRect.top + scrollThreshold) {
                modelOrderList.scrollTop -= 5;
            } else if (touch.clientY > containerRect.bottom - scrollThreshold) {
                modelOrderList.scrollTop += 5;
            }
        
            // 他のアイテムの位置を更新
            const items = Array.from(modelOrderList.querySelectorAll('.model-order-item:not(.dragging)'));
            const insertBefore = items.find(item => {
                const rect = item.getBoundingClientRect();
                return touch.clientY < rect.top + rect.height / 2;
            });
        
            if (insertBefore) {
                modelOrderList.insertBefore(draggedItem, insertBefore);
            } else {
                modelOrderList.appendChild(draggedItem);
            }
        }

        function handleTouchEnd() {
            if (!draggedItem) return;
            
            // スタイルをリセット
            draggedItem.style.position = '';
            draggedItem.style.top = '';
            draggedItem.style.width = '';
            draggedItem.classList.remove('dragging');
            
            // モデルセレクターの順序を更新
            const newOrder = Array.from(modelOrderList.children).map(item => item.dataset.model);
            updateModelSelectorOrder(newOrder);
            
            // ローカルストレージに保存
            localStorage.setItem('modelOrder', JSON.stringify(newOrder));
            
            draggedItem = null;
        }
    }

    // モデルセレクターの順序を更新
    function updateModelSelectorOrder(newOrder) {
        const modelSelector = document.getElementById('model-selector');
        const fragment = document.createDocumentFragment();

        newOrder.forEach(modelValue => {
            const modelOption = document.querySelector(`#${modelValue}`);
            const modelLabel = document.querySelector(`label[for="${modelValue}"]`);
            if (modelOption && modelLabel) {
                fragment.appendChild(modelOption);
                fragment.appendChild(modelLabel);
            }
        });

        modelSelector.innerHTML = '';
        modelSelector.appendChild(fragment);
    }

    // 保存された順序を読み込んで適用
    const savedOrder = localStorage.getItem('modelOrder');
    if (savedOrder) {
        try {
            const order = JSON.parse(savedOrder);
            updateModelSelectorOrder(order);
        } catch (e) {
            console.error('モデル順序の読み込みに失敗しました:', e);
        }
    }

    // 設定モーダルのモデル順序管理を初期化
    initializeModelOrderSettings();

    // 設定ボタンクリックでモーダルを開く
    settingsBtn.addEventListener('click', () => {
        settingsModal.style.display = 'block';
    });

    // 設定ボタンクリックでモーダルを開く
    settingsBtn.addEventListener('click', () => {
        settingsModal.style.display = 'block';
    });

    // モーダルを閉じる
    closeModal.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });

    // モーダル外クリックで閉じる
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    // カラーピッカーの値が変更されたときの処理
    accentColorInput.addEventListener('input', (e) => {
        const color = e.target.value;
        colorValue.textContent = color;
        updateThemeColor(color);
    });

    // カラーピッカーの値が確定したときの処理
    accentColorInput.addEventListener('change', (e) => {
        const color = e.target.value;
        localStorage.setItem('accentColor', color);
    });

    // リセットボタンの処理
    resetColorBtn.addEventListener('click', () => {
        accentColorInput.value = DEFAULT_COLOR;
        colorValue.textContent = DEFAULT_COLOR;
        updateThemeColor(DEFAULT_COLOR);
        localStorage.setItem('accentColor', DEFAULT_COLOR);
    });

    // テーマカラーを更新する関数
    function updateThemeColor(color) {
        const root = document.documentElement;
        const darkerColor = adjustColor(color, -10); // 少し暗い色を生成
        const colorWithOpacity = color.replace(')', ', 0.2)').replace('rgb', 'rgba'); // 20%の透明度を持つ色

        root.style.setProperty('--primary-color', color);
        root.style.setProperty('--primary-gradient', `linear-gradient(135deg, ${color}, ${darkerColor})`);
        root.style.setProperty('--user-message-bg', `linear-gradient(135deg, ${color}, ${darkerColor})`);
        root.style.setProperty('--user-avatar-bg', color);
        
        // 枠線の色を設定したカラーに基づいて更新
        root.style.setProperty('--border-color', colorWithOpacity);
    }

    // 色を明るく/暗くする関数
    function adjustColor(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;

        return '#' + (
            0x1000000 +
            (R < 255 ? (R < 0 ? 0 : R) : 255) * 0x10000 +
            (G < 255 ? (G < 0 ? 0 : G) : 255) * 0x100 +
            (B < 255 ? (B < 0 ? 0 : B) : 255)
        ).toString(16).slice(1);
    }

    // ログアウトボタンのアニメーション
    if (elements.logoutBtn) {
        elements.logoutBtn.classList.add('pulse');
        
        elements.logoutBtn.addEventListener('mouseenter', function() {
            this.classList.remove('pulse');
        });
        
        elements.logoutBtn.addEventListener('mouseleave', function() {
            this.classList.add('pulse');
        });
    }

    let currentChatId = null;
    let selectedModel = 'groq';
    const imageCapableModels = ['gpt', 'claude', 'groq', 'ollama'];

// モデルセレクターの初期化
    function initializeModelSelector() {
        const modelSelector = elements.modelSelector;
        const labels = Array.from(modelSelector.querySelectorAll('.model-label'));
        const radios = Array.from(modelSelector.querySelectorAll('.model-option'));
        const isMobile = window.innerWidth <= 768;

        // モバイル時の処理
        if (isMobile) {
            // シンプルなクリックハンドラーのみ設定
            labels.forEach((label, index) => {
                const radio = radios[index];
                
                label.addEventListener('click', () => {
                    radio.checked = true;
                    selectedModel = radio.value;
                    elements.imageUploadBtn.style.display = 
                        imageCapableModels.includes(selectedModel) ? 'block' : 'none';
                });
            });

            // シンプルな横スクロール処理
            let startX = null;
            let scrollLeft = 0;

            modelSelector.addEventListener('touchstart', (e) => {
                startX = e.touches[0].pageX;
                scrollLeft = modelSelector.scrollLeft;
            }, { passive: true });

            modelSelector.addEventListener('touchmove', (e) => {
                if (startX === null) return;
                
                const x = e.touches[0].pageX;
                const walk = (startX - x);  // 乗数（2）を削除
                modelSelector.scrollLeft = scrollLeft + walk;
                
                // スクロールの即時性を高めるために追加
                requestAnimationFrame(() => {
                    modelSelector.style.scrollBehavior = 'auto';
                    modelSelector.scrollLeft = scrollLeft + walk;
                });
            }, { passive: true });
            
            // スクロール終了時の慣性スクロールを滑らかにする
            modelSelector.addEventListener('touchend', () => {
                startX = null;
                modelSelector.style.scrollBehavior = 'smooth';
            }, { passive: true });
        } 
        // PC時の処理
        else {
            labels.forEach((label, index) => {
                const radio = radios[index];
                const wrapper = document.createElement('div');
                wrapper.className = 'model-wrapper';
                wrapper.draggable = true;
                
                label.parentNode.insertBefore(wrapper, label);
                wrapper.appendChild(radio);
                wrapper.appendChild(label);
                
                setupDragAndDrop(wrapper);
                
                label.addEventListener('click', () => {
                    radio.checked = true;
                    selectedModel = radio.value;
                    elements.imageUploadBtn.style.display = 
                        imageCapableModels.includes(selectedModel) ? 'block' : 'none';
                });
            });
        }
    }

    // PC専用のドラッグ＆ドロップ処理
    let draggedElement = null;
    
    function setupDragAndDrop(element) {
        element.addEventListener('dragstart', (e) => {
            draggedElement = element;
            element.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });

        element.addEventListener('dragend', () => {
            element.classList.remove('dragging');
            draggedElement = null;
        });

        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (!draggedElement || draggedElement === element) return;

            const rect = element.getBoundingClientRect();
            const midPoint = rect.x + rect.width / 2;
            
            if (e.clientX < midPoint) {
                element.parentNode.insertBefore(draggedElement, element);
            } else {
                element.parentNode.insertBefore(draggedElement, element.nextSibling);
            }
        });
    }

    // タッチイベントの処理
    let touchStartX = 0;
    let touchStartY = 0;
    let touchedElement = null;
    let touchStartTime = 0;

    elements.modelSelector.addEventListener('touchstart', (e) => {
        const touch = e.touches[0];
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
        touchedElement = e.target.closest('.model-wrapper');
        touchStartTime = Date.now();
        isDragging = false;

        if (touchedElement) {
            touchedElement.classList.add('dragging');
        }
    }, { passive: true });

    elements.modelSelector.addEventListener('touchmove', (e) => {
        if (!touchedElement) return;
        
        const touch = e.touches[0];
        const diffX = Math.abs(touch.clientX - touchStartX);
        const diffY = Math.abs(touch.clientY - touchStartY);

        if (!isDragging && diffX > 5) {
            isDragging = true;
        }

        if (isDragging) {
            e.preventDefault();
            const elements = Array.from(document.querySelectorAll('.model-wrapper'));
            const touchX = touch.clientX;

            elements.forEach(element => {
                if (element === touchedElement) return;

                const rect = element.getBoundingClientRect();
                const midPoint = rect.x + rect.width / 2;

                if (touchX < midPoint) {
                    element.parentNode.insertBefore(touchedElement, element);
                } else {
                    element.parentNode.insertBefore(touchedElement, element.nextSibling);
                }
            });
        }
    });

    elements.modelSelector.addEventListener('touchend', (e) => {
        const touchEndTime = Date.now();
        const touchDuration = touchEndTime - touchStartTime;

        if (touchedElement) {
            touchedElement.classList.remove('dragging');
            if (!isDragging && touchDuration < 200) {
                const radio = touchedElement.querySelector('.model-option');
                if (radio) {
                    radio.checked = true;
                    selectedModel = radio.value;
                    elements.imageUploadBtn.style.display = 
                        imageCapableModels.includes(selectedModel) ? 'block' : 'none';
                }
            }
        }
        isDragging = false;
        touchedElement = null;
    });

// サイドバーの状態を管理
    function toggleSidebar() {
        const isActive = elements.sidebar.classList.toggle('active');
        elements.mainContent.classList.toggle('sidebar-active', isActive);
        
        // トグルボタンの位置を制御
        if (isActive) {
            elements.toggleSidebar.style.left = '320px'; // サイドバーが開いているとき
        } else {
            elements.toggleSidebar.style.left = '20px';  // サイドバーが閉じているとき
        }
        
        localStorage.setItem('sidebarOpen', isActive);
    }
    
    // 初期状態の設定
    const savedSidebarState = localStorage.getItem('sidebarOpen');
    if (savedSidebarState === 'true') {
        elements.sidebar.classList.add('active');
        elements.mainContent.classList.add('sidebar-active');
        elements.toggleSidebar.style.left = '320px';
    } else {
        elements.toggleSidebar.style.left = '20px';
    }

    // チャット履歴の削除機能
    function setupChatItemEvents(chatItem) {
        const deleteBtn = chatItem.querySelector('.delete-chat-btn');
        const chatId = chatItem.dataset.chatId;
        const titleSpan = chatItem.querySelector('.chat-item-title');

        // タッチイベントのハンドラー
        let touchStartTime;
        let isTouchMoved = false;

        chatItem.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
            isTouchMoved = false;

            // 長押しタイマーの設定
            longPressTimer = setTimeout(() => {
                if (!isTouchMoved && !isMultiSelectMode) {
                    toggleMultiSelectMode(true);
                    toggleChatSelection(chatItem);
                }
            }, LONG_PRESS_DURATION);
        });

        chatItem.addEventListener('touchmove', () => {
            isTouchMoved = true;
            clearTimeout(longPressTimer);
        });

        chatItem.addEventListener('touchend', (e) => {
            clearTimeout(longPressTimer);
            const touchDuration = Date.now() - touchStartTime;

            if (!isTouchMoved) {
                if (isMultiSelectMode) {
                    toggleChatSelection(chatItem);
                } else if (touchDuration < LONG_PRESS_DURATION) {
                    handleChatItemClick(chatItem, chatId);
                }
            }
        });

        // マウスイベントのハンドラー
        let mouseStartTime;
        let isMouseMoved = false;

        chatItem.addEventListener('mousedown', (e) => {
            mouseStartTime = Date.now();
            isMouseMoved = false;

            longPressTimer = setTimeout(() => {
                if (!isMouseMoved && !isMultiSelectMode) {
                    toggleMultiSelectMode(true);
                    toggleChatSelection(chatItem);
                }
            }, LONG_PRESS_DURATION);
        });

        chatItem.addEventListener('mousemove', () => {
            isMouseMoved = true;
            clearTimeout(longPressTimer);
        });

        chatItem.addEventListener('mouseup', (e) => {
            clearTimeout(longPressTimer);
            const mouseDuration = Date.now() - mouseStartTime;

            if (!isMouseMoved) {
                if (isMultiSelectMode) {
                    toggleChatSelection(chatItem);
                } else if (mouseDuration < LONG_PRESS_DURATION) {
                    handleChatItemClick(chatItem, chatId);
                }
            }
        });

        // タイトルをダブルクリックで編集可能にする
        titleSpan.addEventListener('dblclick', function() {
            if (!isMultiSelectMode) {
                const currentTitle = this.textContent;
                const input = document.createElement('input');
                input.type = 'text';
                input.value = currentTitle;
                input.className = 'chat-title-input';
                
                // 入力中はチャット選択を防ぐ
                input.addEventListener('click', (e) => e.stopPropagation());
                
                // エンターキーまたはフォーカスを失った時に保存
                const saveTitle = async () => {
                    const newTitle = input.value.trim();
                    if (newTitle && newTitle !== currentTitle) {
                        try {
                            const response = await fetch(`/update_chat_title/${chatId}`, {
                                method: 'PUT',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ title: newTitle })
                            });

                            if (!response.ok) throw new Error('タイトルの更新に失敗しました');
                            
                            titleSpan.textContent = newTitle;
                        } catch (error) {
                            console.error('エラー:', error);
                            showError('タイトルの更新に失敗しました');
                            titleSpan.textContent = currentTitle;
                        }
                    } else {
                        titleSpan.textContent = currentTitle;
                    }
                };

                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        input.blur();
                    }
                });

                input.addEventListener('blur', saveTitle);
                
                this.textContent = '';
                this.appendChild(input);
                input.focus();
                input.select();
            }
        });

        // 削除ボタンのクリックイベント
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            
            if (!confirm('このチャット履歴を削除してもよろしいですか？')) {
                return;
            }

            try {
                const response = await fetch(`/delete_chat/${chatId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) throw new Error('チャットの削除に失敗しました');

                chatItem.remove();
                if (currentChatId === chatId) {
                    currentChatId = null;
                    elements.chatBox.innerHTML = '';
                }
            } catch (error) {
                console.error('エラー:', error);
                showError('チャットの削除に失敗しました');
            }
        });
    }

    // チャットアイテムのクリックハンドラー
    async function handleChatItemClick(chatItem, chatId) {
        currentChatId = chatId;
        
        document.querySelectorAll('.chat-item').forEach(i => {
            i.classList.remove('active');
        });
        chatItem.classList.add('active');
        
        try {
            const response = await fetch(`/get_chat/${chatId}`);
            if (!response.ok) throw new Error('チャット履歴の取得に失敗しました');
            
            const data = await response.json();
            elements.chatBox.innerHTML = '';
            data.messages.forEach(msg => {
                displayMessage(msg.content, msg.role === 'user' ? 'user-message' : 'assistant-message', msg.model, msg.image);
            });
            
            if (window.innerWidth <= 768) {
                elements.sidebar.classList.remove('active');
                elements.mainContent.classList.remove('sidebar-active');
                elements.toggleSidebar.style.left = '20px';  // 追加:トグルボタンを元の位置に戻す
            }
        } catch (error) {
            console.error('エラー:', error);
            showError('チャット履歴の読み込みに失敗しました');
        }
    }

    // 既存のチャットアイテムにイベントを設定
    document.querySelectorAll('.chat-item').forEach(setupChatItemEvents);

    // テーマ切り替え
    elements.themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        elements.themeToggle.innerHTML = isDark ? 
            '<i class="fas fa-moon"></i>' : 
            '<i class="fas fa-sun"></i>';
    });

    // サイドバー切り替え
    elements.toggleSidebar.addEventListener('click', toggleSidebar);

    // 新規チャット
    elements.newChatBtn.addEventListener('click', () => {
        currentChatId = null;
        elements.chatBox.innerHTML = '';
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
    });

    // メッセージ送信
    async function sendMessage() {
        const message = elements.messageInput.value.trim();
        const imageFile = elements.imageInput.files[0];
        
        if (message === '' && !imageFile) return;
        
        if (imageFile && !imageCapableModels.includes(selectedModel)) {
            showError('選択したモデルは画像処理に対応していません');
            return;
        }
        
        // 画像プレビューを含むメッセージを表示
        displayMessage(message, 'user-message', null, imageFile ? {
            filename: imageFile.name,
            url: URL.createObjectURL(imageFile)
        } : null);

        elements.messageInput.value = '';
        elements.messageInput.style.height = '';
        elements.loading.style.display = 'block';

        const formData = new FormData();
        formData.append('message', message);
        formData.append('model', selectedModel);
        if (currentChatId) formData.append('chat_id', currentChatId);
        if (imageFile) formData.append('image', imageFile);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('ネットワークエラーが発生しました');

            const data = await response.json();
            
            if (!currentChatId && data.chat_id) {
                currentChatId = data.chat_id;
                const chatHistory = document.getElementById('chat-history');
                const newChatItem = document.createElement('div');
                newChatItem.className = 'chat-item active';
                newChatItem.dataset.chatId = currentChatId;
                newChatItem.innerHTML = `
                    <i class="fas fa-comment"></i>
                    <span class="chat-item-title">${message}</span>
                    <button class="delete-chat-btn" title="チャットを削除">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                chatHistory.insertBefore(newChatItem, chatHistory.firstChild);
                
                document.querySelectorAll('.chat-item').forEach(item => {
                    if (item !== newChatItem) item.classList.remove('active');
                });

                setupChatItemEvents(newChatItem);
            }
            
            displayMessage(data.message, 'assistant-message', data.model);
            
            if (imageFile) {
                elements.imageInput.value = '';
                elements.imagePreview.src = '';
                elements.imagePreviewContainer.style.display = 'none';
            }
        } catch (error) {
            console.error('エラー:', error);
            showError('メッセージの送信に失敗しました');
        } finally {
            elements.loading.style.display = 'none';
        }
    }

    // メッセージ表示
    function displayMessage(message, className, model = null, image = null) {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message ${className}`;
    
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        
        if (className === 'user-message') {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        } else {
            const logoImg = document.createElement('img');
            logoImg.src = '/static/logo.png';
            logoImg.alt = 'VOLTMIND Logo';
            logoImg.style.width = '100%';
            logoImg.style.height = '100%';
            logoImg.style.objectFit = 'contain';
            avatar.appendChild(logoImg);
        }
    
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // 画像の表示
        if (image) {
            const imageContainer = document.createElement('div');
            imageContainer.className = 'message-image-container';
            const img = document.createElement('img');
            img.src = image.url;
            img.alt = image.filename;
            img.className = 'message-image';
            imageContainer.appendChild(img);
            messageContent.appendChild(imageContainer);
        }

        if (className === 'assistant-message') {
            if (model) {
                const modelBadge = document.createElement('div');
                modelBadge.className = 'model-badge';
                // モデル名の表示を条件分岐で制御
                const modelNames = {
                    'groq': 'Groq',
                    'gpt': 'ChatGPT',
                    'gemini': 'Gemini',
                    'claude': 'Claude',
                    'xai': 'xAI',
                    'VOLTMIND AI': 'VOLTMIND AI',
                    '税務GPT': '税務GPT',
                    '薬科GPT': '薬科GPT',
                    '敬語の鬼': '敬語の鬼',
                    '節税商品説明AI': '節税商品説明AI',
                    'IT用語説明AI': 'IT用語説明AI',
                    '1.要件定義書のヒアリングAI': '1.要件定義書のヒアリングAI',
                    '2.ビジネス向け要件定義書': '2.ビジネス向け要件定義書',
                    '3.エンジニア向け要件定義書': '3.エンジニア向け要件定義書',
                    '4.金額提示相談AI': '4.金額提示相談AI'
                };
                modelBadge.textContent = modelNames[model] || model.toUpperCase();
                messageContent.appendChild(modelBadge);
            }

            if (typeof message === 'object' && message.search_results) {
                messageContent.innerHTML += marked.parse(message.message);
                const resultsContainer = document.createElement('div');
                resultsContainer.className = 'search-results';
                message.search_results.forEach(result => {
                    const resultDiv = document.createElement('div');
                    resultDiv.innerHTML = `
                        <div class="search-title">${result.title}</div>
                        <div class="search-url">${result.url}</div>
                        <div class="search-content">${marked.parse(result.search_result_markdown)}</div>
                    `;
                    resultsContainer.appendChild(resultDiv);
                });
                messageContent.appendChild(resultsContainer);
            } else {
                messageContent.innerHTML += marked.parse(message);
            }
            messageContent.classList.add('markdown-body');
            hljs.highlightAll();
            addCopyButtons(messageContent);

            // ここに新しいコピーボタンのコードを追加 ↓
            const copyMessageBtn = document.createElement('button');
            copyMessageBtn.className = 'copy-message-btn';
            copyMessageBtn.textContent = 'コピー';
            copyMessageBtn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(message);
                    copyMessageBtn.textContent = 'コピー済み';
                    setTimeout(() => copyMessageBtn.textContent = 'コピー', 2000);
                } catch (err) {
                    console.error('コピーに失敗しました:', err);
                }
            });
            messageContent.appendChild(copyMessageBtn);
        } else {
            if (message) {
                const textContent = document.createElement('div');
                textContent.className = 'message-text collapsed';
                textContent.textContent = message;

                // 50文字を超える場合のみ「...」と展開ボタンを表示
                if (message.length > 50 || message.includes('\n')) {
                    textContent.classList.add('long-text');

                    // 展開/折りたたみボタン
                    const toggleBtn = document.createElement('div');
                    toggleBtn.className = 'toggle-message';
                    toggleBtn.innerHTML = '<i class="fas fa-chevron-down"></i>';

                    // クリックイベントの設定
                    function toggleMessage() {
                        const isCollapsed = textContent.classList.contains('collapsed');
                        textContent.classList.toggle('collapsed');
                        textContent.classList.toggle('expanded');
                        toggleBtn.innerHTML = isCollapsed ? 
                            '<i class="fas fa-chevron-up"></i>' : 
                            '<i class="fas fa-chevron-down"></i>';
                    }

                    textContent.addEventListener('click', toggleMessage);
                    toggleBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        toggleMessage();
                    });

                    messageContent.appendChild(toggleBtn);
                }

                messageContent.appendChild(textContent);
            }
        }

        messageWrapper.appendChild(avatar);
        messageWrapper.appendChild(messageContent);
        elements.chatBox.appendChild(messageWrapper);
        elements.chatBox.scrollTop = elements.chatBox.scrollHeight;
    }

    // エラー表示
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message';
        errorDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message-content" style="color: #ef4444;">
                ${message}
            </div>
        `;
        elements.chatBox.appendChild(errorDiv);
        elements.chatBox.scrollTop = elements.chatBox.scrollHeight;
        setTimeout(() => errorDiv.remove(), 5000);
    }

    // コードブロックにコピーボタンを追加
    function addCopyButtons(container) {
        container.querySelectorAll('pre code').forEach(block => {
            const button = document.createElement('button');
            button.className = 'copy-btn';
            button.textContent = 'コピー';
            button.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(block.textContent);
                    button.textContent = 'コピー済み';
                    setTimeout(() => button.textContent = 'コピー', 2000);
                } catch (err) {
                    console.error('コピーに失敗しました:', err);
                }
            });
            block.parentNode.insertBefore(button, block);
        });
    }

    // 送信ボタンとEnterキーのイベント
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keydown', e => {
        // Ctrl + Enter (Windows) または Command + Enter (Mac) で送信
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    // テキストエリアの高さ自動調整
    elements.messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    // 初期表示時のテーマ設定
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
        elements.themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }

    // 新規チャットボタンのイベントリスナー（ここに追加）
    elements.newChatBtn.addEventListener('click', function() {
        currentChatId = null;
        elements.chatBox.innerHTML = '';
        
        // サイドバーを閉じる処理（PC・モバイル共通）
        elements.sidebar.classList.remove('active');
        elements.mainContent.classList.remove('sidebar-active');
        elements.toggleSidebar.style.left = '20px';  // 三本線を元の位置に戻す
        
        // チャットボックスとその他の要素を再表示（PC・モバイル共通）
        elements.chatBox.style.opacity = '1';
        elements.chatBox.style.visibility = 'visible';
        elements.messageInput.parentElement.style.opacity = '1';
        elements.messageInput.parentElement.style.visibility = 'visible';
        elements.modelSelector.style.opacity = '1';
        elements.modelSelector.style.visibility = 'visible';
    });

    // モデルセレクターの初期化
    initializeModelSelector();
});