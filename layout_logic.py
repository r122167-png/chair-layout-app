import io
import re
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

matplotlib.rcParams['font.family'] = 'MS Gothic'

GROUP_COLORS = [
    ('#F0997B', '#D85A30'),
    ('#5DCAA5', '#1D9E75'),
    ('#AFA9EC', '#7F77DD'),
    ('#FAC775', '#BA7517'),
    ('#85B7EB', '#378ADD'),
]

def draw_chair(ax, x, y, fill_color, edge_color, size=0.6):
    s = size
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), s, s * 0.7,
        boxstyle="round,pad=0.05",
        facecolor=fill_color, edgecolor=edge_color, linewidth=1.5
    ))
    ax.add_patch(patches.FancyBboxPatch(
        (x + s * 0.1, y + s * 0.7), s * 0.8, s * 0.35,
        boxstyle="round,pad=0.05",
        facecolor=fill_color, edgecolor=edge_color, linewidth=1.5
    ))
    ax.add_patch(patches.Rectangle(
        (x + s * 0.1, y - s * 0.25), s * 0.15, s * 0.25,
        facecolor=edge_color
    ))
    ax.add_patch(patches.Rectangle(
        (x + s * 0.75, y - s * 0.25), s * 0.15, s * 0.25,
        facecolor=edge_color
    ))

def make_layout_image(layout, title):
    cols = max(layout)
    rows = len(layout)
    chair_size = 0.6
    gap = 0.3
    step = chair_size + gap
    fig_w = max(6, cols * step + 2)
    fig_h = max(4, rows * step + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_aspect('equal')
    ax.axis('off')

    for row_i, group_size in enumerate(layout):
        color_fill, color_edge = GROUP_COLORS[row_i % len(GROUP_COLORS)]
        offset_x = (cols - group_size) * step / 2

        for col_i in range(group_size):
            x = offset_x + col_i * step
            y = (rows - row_i - 1) * step
            draw_chair(ax, x, y, color_fill, color_edge, size=chair_size)

        label_x = offset_x + group_size * step / 2 - chair_size / 2
        label_y = (rows - row_i - 1) * step - 0.4
        ax.text(label_x, label_y,
                f'グループ{row_i + 1}（{group_size}人）',
                ha='center', va='top', fontsize=9, color=color_edge)

    ax.set_xlim(-0.5, cols * step + 0.5)
    ax.set_ylim(-0.8, rows * step + 0.5)
    plt.title(title, fontsize=13, pad=12)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_perfect_shapes(n):
    perfect = []
    for i in range(n, 1, -1):
        if n % i == 0:
            layout = [i] * (n // i)
            if len(layout) >= 2:
                perfect.append(layout)
    return perfect

def generate_extra_shapes(n):
    shapes = []
    def dfs(rem, max_size, path):
        if rem == 0:
            if len(path) >= 2:
                shapes.append(path)
            return
        for i in range(min(rem, max_size), 1, -1):
            if rem - i == 1:
                continue
            dfs(rem - i, i, path + [i])
    dfs(n, n, [])
    return shapes

def remove_duplicates(layouts):
    unique = []
    seen = set()
    for s in layouts:
        key = tuple(sorted(s, reverse=True))
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique

def calc_score(layout, wide, tall, spacious, compact):
    width = max(layout)
    height = len(layout)
    score = 0
    if wide:
        if width > height:
            score += 4
        else:
            score -= 6
    if tall:
        if height > width:
            score += 4
        else:
            score -= 6
    if spacious:
        score += len(layout) * 2
    if compact:
        score -= len(layout) * 2
    if len(set(layout)) == 1:
        score += 5
    diff = max(layout) - min(layout)
    if diff <= 1:
        score += 4
    elif diff == 2:
        score -= 2
    elif diff >= 3:
        score -= diff * 2
    score -= abs(width - height) * 0.3
    return score

def generate_movement_tasks(layout, max_rows=6, max_cols=6):
    """6x6の全体エリアの中央に寄せた移動座標リストを生成"""
    selected_rows = len(layout)
    tasks = []
    chair_count = 1

    start_row_idx = (max_rows - selected_rows) // 2

    for r_idx, group_size in enumerate(layout):
        row_pos = start_row_idx + r_idx
        row_letter = chr(ord('A') + row_pos)

        start_col_idx = (max_cols - group_size) // 2

        for c_idx in range(group_size):
            col_pos = start_col_idx + c_idx + 1

            target_spot = f"Seat_{row_letter}{col_pos}"
            origin_spot = f"Chair_Origin_{chair_count}"

            tasks.append({
                "step": chair_count,
                "chair": f"椅子{chair_count}",
                "origin": origin_spot,
                "target": target_spot
            })
            chair_count += 1

    return tasks