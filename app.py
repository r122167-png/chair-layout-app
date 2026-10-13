
import asyncio
import math

import streamlit as st
import kachaka_api
import layout_logic as logic


# ==========================================
# カチャカの設定
# ==========================================
KACHAKA_IP = "192.168.100.177:26400"

# 動画撮影用の動作
MOVE_DISTANCE = 0.2       # 20cm前進
ROTATE_ANGLE = math.pi / 2  # 90度旋回


# ==========================================
# カチャカの動作テスト
# ==========================================
async def run_kachaka_demo():
    client = kachaka_api.aio.KachakaApiClient(KACHAKA_IP)

    # 現在位置を取得
    robot_pose = await client.get_robot_pose()

    st.success(
        f"カチャカ接続完了！ "
        f"現在位置: ({robot_pose.x:.2f}, {robot_pose.y:.2f})"
    )

    progress_bar = st.progress(0)

    # ① 20cm前進
    st.info("① 20cm前進しています...")

    result = await client.move_forward(
        MOVE_DISTANCE,
        wait_for_completion=True
    )

    if hasattr(result, "success") and not result.success:
        raise RuntimeError("前進に失敗しました")

    progress_bar.progress(50)
    st.success("前進完了！")

    # ② 90度旋回
    st.info("② 90度旋回しています...")

    result = await client.rotate_in_place(
        ROTATE_ANGLE,
        wait_for_completion=True
    )

    if hasattr(result, "success") and not result.success:
        raise RuntimeError("旋回に失敗しました")

    progress_bar.progress(100)

    st.success("カチャカの動作テストが完了しました！")
    st.caption("※ 今回はカチャカ単体の移動テストです。椅子の搬送は行っていません。")


# ==========================================
# Streamlitの画面設定
# ==========================================
st.set_page_config(
    page_title="座席レイアウト＆カチャカ動作テスト",
    layout="wide"
)

if "top3" not in st.session_state:
    st.session_state.top3 = None

if "selected" not in st.session_state:
    st.session_state.selected = None

if "demo_done" not in st.session_state:
    st.session_state.demo_done = False


st.title("🪑 会議室座席レイアウト＆カチャカ動作テスト")
st.write("人数と希望条件を入力してください。")


# ==========================================
# ① 利用人数と条件の入力
# ==========================================
st.header("① 利用人数と配置条件の入力")

n = st.number_input(
    "人数",
    min_value=2,
    max_value=36,
    value=12,
    step=1
)

col1, col2 = st.columns(2)

with col1:
    wide = st.checkbox("横長")
    tall = st.checkbox("縦長")

with col2:
    spacious = st.checkbox("広め")
    compact = st.checkbox("コンパクト")


# ==========================================
# ② レイアウト候補の生成
# ==========================================
if st.button("配置を提案する", type="primary"):

    layouts = logic.remove_duplicates(
        logic.generate_perfect_shapes(n)
        + logic.generate_extra_shapes(n)
    )

    # 6×6グリッドに収まる候補だけを使用
    layouts = [
        layout for layout in layouts
        if len(layout) <= 6 and max(layout) <= 6
    ]

    results = sorted(
        [
            (
                layout,
                logic.calc_score(
                    layout,
                    wide,
                    tall,
                    spacious,
                    compact
                )
            )
            for layout in layouts
        ],
        key=lambda x: x[1],
        reverse=True
    )

    st.session_state.top3 = results[:3]
    st.session_state.selected = None
    st.session_state.demo_done = False


# ==========================================
# ③ 上位3候補の表示
# ==========================================
if st.session_state.top3 is not None:

    if not st.session_state.top3:
        st.warning("配置候補がありません。人数を変更してください。")

    else:
        st.divider()
        st.header("② おすすめの座席レイアウト")

        cols = st.columns(len(st.session_state.top3))

        for i, (layout, score) in enumerate(st.session_state.top3):

            with cols[i]:
                st.subheader(f"候補{i + 1}")

                st.write(f"配置：{layout}")
                st.write(f"スコア：{score:.2f}点")

                buf = logic.make_layout_image(
                    layout,
                    f"候補{i + 1}"
                )

                st.image(
                    buf,
                    use_container_width=True
                )

        st.divider()
        st.subheader("配置を選んでください")

        choice = st.radio(
            "採用するレイアウト",
            options=list(
                range(1, len(st.session_state.top3) + 1)
            ),
            format_func=lambda x:
                f"候補{x}：{st.session_state.top3[x-1][0]}",
            horizontal=True
        )

        if st.button("この配置に決定！", type="primary"):

            st.session_state.selected = (
                st.session_state.top3[choice - 1][0]
            )

            st.session_state.demo_done = False


# ==========================================
# ④ 搬送タスクの生成
# ==========================================
if st.session_state.selected is not None:

    st.divider()
    st.header("③ 選択されたレイアウト")

    selected_layout = st.session_state.selected

    st.write(f"選択された配置：{selected_layout}")

    buf = logic.make_layout_image(
        selected_layout,
        f"選択配置：{selected_layout}"
    )

    st.image(buf, width=420)

    # 搬送タスクを生成
    tasks = logic.generate_movement_tasks(
        selected_layout,
        max_rows=6,
        max_cols=6
    )

    st.subheader("椅子の搬送タスク（計画）")

    st.write(
        f"全{len(tasks)}脚分の搬送タスクを生成しました。"
    )

    task_table = [
        {
            "手順": f"Step {t['step']}",
            "対象": t["chair"],
            "出発地": t["origin"],
            "目的地": t["target"]
        }
        for t in tasks
    ]

    # 動画撮影時は折りたためる
    with st.expander("搬送タスク一覧を表示"):
        st.table(task_table)

    st.caption(
        "※ ここでは搬送計画を生成しています。"
        "実際の椅子の搬送はまだ行いません。"
    )

    # ==========================================
    # ⑤ カチャカの実機動作テスト
    # ==========================================
    st.divider()
    st.header("④ カチャカの実機動作テスト")

    st.info(
        "Pythonからkachaka-apiを使って、"
        "カチャカを20cm前進 → 90度旋回させます。"
    )

    st.warning(
        "実行前に周囲の安全を確認してください。"
        "実機が動くため、すぐ停止できる状態で実行してください。"
    )

    if st.session_state.demo_done:

        st.success("動作テストは実行済みです。")

        if st.button("もう一度テストする"):
            st.session_state.demo_done = False
            st.rerun()

    else:
        safety_check = st.checkbox(
            "周囲の安全を確認しました"
        )

        if st.button(
            "🚀 カチャカ動作テスト開始",
            type="primary",
            disabled=not safety_check
        ):

            with st.spinner("カチャカ動作中..."):

                try:
                    asyncio.run(run_kachaka_demo())

                except Exception as e:
                    st.error(f"エラー：{e}")
                    st.info(
                        "カチャカを停止・確認してから"
                        "再実行してください。"
                    )

                else:
                    st.session_state.demo_done = True
