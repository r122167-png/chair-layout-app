import streamlit as st
import layout_logic as logic

# session_state初期化
if 'top3' not in st.session_state:
    st.session_state.top3 = None
if 'selected' not in st.session_state:
    st.session_state.selected = None

st.title('🪑 会議室座席レイアウト & カチャカ自動搬送')
st.write('人数と希望条件を入力してください。')

n = st.number_input('人数', min_value=2, max_value=36, value=12, step=1)

col1, col2 = st.columns(2)
with col1:
    wide = st.checkbox('横長')
    tall = st.checkbox('縦長')
with col2:
    spacious = st.checkbox('広め')
    compact = st.checkbox('コンパクト')

if st.button('配置を提案する', type='primary'):
    layouts = logic.remove_duplicates(
        logic.generate_perfect_shapes(n) + logic.generate_extra_shapes(n)
    )
    results = sorted(
        [(layout, logic.calc_score(layout, wide, tall, spacious, compact)) for layout in layouts],
        key=lambda x: x[1],
        reverse=True
    )
    st.session_state.top3 = results[:3]
    st.session_state.selected = None  # リセット

# 候補表示
if st.session_state.top3:
    st.subheader('おすすめ候補')
    cols = st.columns(3)
    for i, (layout, score) in enumerate(st.session_state.top3):
        with cols[i]:
            st.markdown(f'**候補{i+1}**')
            st.write(f'配置: {layout}')
            st.write(f'スコア: {round(score, 2)}')
            buf = logic.make_layout_image(layout, f'候補{i+1}')
            st.image(buf, use_container_width=True)

    st.divider()
    st.subheader('配置を選んでください')

    choice = st.radio(
        '番号を選んでや',
        options=[1, 2, 3],
        format_func=lambda x: f'候補{x}：{st.session_state.top3[x-1][0]}'
    )

    if st.button('この配置に決定！', type='primary'):
        st.session_state.selected = st.session_state.top3[choice - 1][0]

# 選択結果 & 移動タスク表示
if st.session_state.selected:
    st.divider()
    st.subheader('✅ 選択された配置')
    buf = logic.make_layout_image(st.session_state.selected, f'選択配置：{st.session_state.selected}')
    st.image(buf, use_container_width=True)
    
    st.divider()
    st.subheader('🤖 カチャカ自動搬送タスク一覧')
    
    # 6×6グリッドの中央寄せ座標を計算
    tasks = logic.generate_movement_tasks(st.session_state.selected, max_rows=6, max_cols=6)
    
    st.write(f"部屋（6×6エリア）の中央に寄せた全 {len(tasks)} 脚の自動移動手順です：")
    
    task_table = [
        {
            "手順": f"Step {t['step']}",
            "対象": t['chair'],
            "初期位置 (Pickup)": t['origin'],
            "配置座標 (Drop)": t['target']
        } for t in tasks
    ]
    st.table(task_table)

    if st.button('🚀 カチャカへタスク送信（実機動作）', type='primary'):
        st.success('タスクを生成しました。実機接続モジュール呼び出し準備完了です！')