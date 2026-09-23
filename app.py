import asyncio
import streamlit as st
import kachaka_api
import layout_logic as logic

# --------------------------------------------------
# カチャカ非同期通信関数
# --------------------------------------------------
async def run_kachaka_tasks(tasks):
    # カチャカへ接続
    client = kachaka_api.aio.KachakaApiClient("192.168.100.177:26400")

    # 1. 接続 & 現在地取得
    robot_pose = await client.get_robot_pose()
    st.info(f"🤖 カチャカ接続完了！ 現在位置: ({robot_pose.x:.2f}, {robot_pose.y:.2f})")

    # 2. 搬送タスクの実行（動作テストとして20cm前進 ➔ 90度回転）
    progress_bar = st.progress(0)
    total_tasks = len(tasks)

    for i, t in enumerate(tasks):
        st.write(f"🔄 **Step {t['step']} 実行中:** {t['chair']} を {t['origin']} から {t['target']} へ搬送中...")

        # 実機テスト動作（前進 & 回転）
        await client.move_forward(0.2)
        await asyncio.sleep(0.5)
        await client.rotate_in_place(1.57)
        await asyncio.sleep(0.5)

        # 進捗バー更新
        progress_bar.progress((i + 1) / total_tasks)

    st.success("🎉 すべての搬送タスクが完了しました！")

# --------------------------------------------------
# Streamlit UIメイン処理
# --------------------------------------------------
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

    # 実機動作ボタン（ここからカチャカの非同期処理を呼ぶ）
    if st.button('🚀 カチャカへタスク送信（実機動作）', type='primary'):
        with st.spinner('カチャカと通信中...'):
            try:
                asyncio.run(run_kachaka_tasks(tasks))
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
