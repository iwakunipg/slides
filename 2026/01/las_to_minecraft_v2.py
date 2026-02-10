import pylas
import os
import math
import numpy as np
import pandas as pd

# === 設定 ===
INPUT_FILE = r"slides\2026\01\kudamaru.las"  # raw文字列でパスを指定
OUTPUT_DIR = r"slides\2026\01\output"
SCALE = 60.0  # スケール
LINES_PER_FILE = 20000
BRIGHTNESS_FACTOR = 1.1  # 明度調整（1.0=変更なし、1.2=20%明るく、0.8=20%暗く）
THRESHOLDS = (254*256, 254*256, 254*256)  # 16bit基準
START_X = 0  # Minecraft座標の開始X座標
START_Y = 0  # Minecraft座標の開始Y座標
START_Z = 0  # Minecraft座標の開始Z座標

# === ブロックカラー定義 ===
BLOCK_COLOR_MAP = [
    ("WOOL", (0.95, 0.95, 0.95)),
    ("ORANGE_WOOL", (0.92, 0.53, 0.25)),
    ("MAGENTA_WOOL", (0.73, 0.31, 0.77)),
    ("LIGHT_BLUE_WOOL", (0.43, 0.55, 0.81)),
    ("YELLOW_WOOL", (0.77, 0.71, 0.11)),
    ("LIME_WOOL", (0.23, 0.75, 0.18)),
    ("PINK_WOOL", (0.84, 0.54, 0.62)),
    ("GRAY_WOOL", (0.26, 0.26, 0.26)),
    ("LIGHT_GRAY_WOOL", (0.62, 0.65, 0.65)),
    ("CYAN_WOOL", (0.15, 0.46, 0.59)),
    ("PURPLE_WOOL", (0.53, 0.23, 0.80)),
    ("BLUE_WOOL", (0.15, 0.20, 0.60)),
    ("BROWN_WOOL", (0.22, 0.30, 0.09)),
    ("GREEN_WOOL", (0.22, 0.30, 0.09)),
    ("RED_WOOL", (0.65, 0.17, 0.16)),
    ("BLACK_WOOL", (0, 0, 0)),
    ("WOOL", (0.77, 0.65, 0.60)),
    ("ORANGE_TERRACOTTA", (0.60, 0.31, 0.14)),
    ("MAGENTA_TERRACOTTA", (0.56, 0.33, 0.40)),
    ("LIGHT_BLUE_TERRACOTTA", (0.44, 0.42, 0.54)),
    ("YELLOW_TERRACOTTA", (0.69, 0.49, 0.13)),
    ("LIME_TERRACOTTA", (0.38, 0.44, 0.20)),
    ("PINK_TERRACOTTA", (0.63, 0.30, 0.31)),
    ("GRAY_TERRACOTTA", (0.22, 0.16, 0.14)),
    ("LIGHT_GRAY_TERRACOTTA", (0.53, 0.42, 0.38)),
    ("CYAN_TERRACOTTA", (0.34, 0.35, 0.36)),
    ("PURPLE_TERRACOTTA", (0.44, 0.25, 0.31)),
    ("BLUE_TERRACOTTA", (0.27, 0.22, 0.33)),
    ("BROWN_TERRACOTTA", (0.28, 0.19, 0.13)),
    ("GREEN_TERRACOTTA", (0.29, 0.32, 0.16)),
    ("RED_TERRACOTTA", (0.56, 0.24, 0.18)),
    ("BLACK_TERRACOTTA", (0.13, 0.08, 0.06)),
    ("STONE", (0.47, 0.47, 0.47)),
    ("SANDSTONE", (0.88, 0.85, 0.64)),
    ("PLANKS_OAK", (0.66, 0.53, 0.34)),
]

def rgb_to_block(r, g, b):
    """RGB値から最も近い色のブロックを返す"""
    # 色の値の範囲をチェック
    if r > 255 or g > 255 or b > 255:
        # 16bit値の可能性があるので正規化
        r, g, b = r/65535*255, g/65535*255, b/65535*255
    
    r, g, b = r/255, g/255, b/255
    min_dist = float("inf")
    best_block = "STONE"
    for block, color in BLOCK_COLOR_MAP:
        dr, dg, db = r - color[0], g - color[1], b - color[2]
        dist = dr**2 + dg**2 + db**2
        if dist < min_dist:
            min_dist = dist
            best_block = block
    return best_block

def debug_las_structure(las):
    """LASファイルの構造を詳しく調べる"""
    print("=== LASファイル構造詳細 ===")
    print(f"LASオブジェクト型: {type(las)}")
    print(f"利用可能な属性: {dir(las)}")
    
    # 基本情報
    print(f"\n基本情報:")
    print(f"  点数: {len(las.points) if hasattr(las, 'points') else 'N/A'}")
    print(f"  ヘッダー: {las.header if hasattr(las, 'header') else 'N/A'}")
    
    # 座標データの確認
    print(f"\n座標データ:")
    if hasattr(las, 'x') and hasattr(las, 'y') and hasattr(las, 'z'):
        print(f"  X: 型={type(las.x)}, 形状={las.x.shape if hasattr(las.x, 'shape') else 'N/A'}")
        print(f"  Y: 型={type(las.y)}, 形状={las.y.shape if hasattr(las.y, 'shape') else 'N/A'}")
        print(f"  Z: 型={type(las.z)}, 形状={las.z.shape if hasattr(las.z, 'shape') else 'N/A'}")
        
        # 実際の値を確認
        print(f"  X範囲: {las.x.min():.6f} ~ {las.x.max():.6f}")
        print(f"  Y範囲: {las.y.min():.6f} ~ {las.y.max():.6f}")
        print(f"  Z範囲: {las.z.min():.6f} ~ {las.z.max():.6f}")
        
        # 最初の5点の生データ
        print(f"  最初の5点の生データ:")
        for i in range(min(5, len(las.x))):
            print(f"    点{i}: X={las.x[i]:.6f}, Y={las.y[i]:.6f}, Z={las.z[i]:.6f}")
    
    # 色データの確認
    print(f"\n色データ:")
    if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
        print(f"  Red: 型={type(las.red)}, 形状={las.red.shape if hasattr(las.red, 'shape') else 'N/A'}")
        print(f"  Green: 型={type(las.green)}, 形状={las.green.shape if hasattr(las.green, 'shape') else 'N/A'}")
        print(f"  Blue: 型={type(las.blue)}, 形状={las.blue.shape if hasattr(las.blue, 'shape') else 'N/A'}")
        
        # 色の値の範囲確認
        print(f"  Red範囲: {las.red.min()} ~ {las.red.max()}")
        print(f"  Green範囲: {las.green.min()} ~ {las.green.max()}")
        print(f"  Blue範囲: {las.blue.min()} ~ {las.blue.max()}")
        
        # 最初の5点の色データ
        print(f"  最初の5点の色データ:")
        for i in range(min(5, len(las.red))):
            print(f"    点{i}: R={las.red[i]}, G={las.green[i]}, B={las.blue[i]}")
    else:
        print("  色データが見つかりません")

def process_las_to_minecraft(las, scale, start_x=0, start_y=0, start_z=0):
    """LASデータをMinecraft座標に変換し、重複を除去"""
    print(f"\n=== 座標変換処理 ===")
    
    # 元の座標範囲
    x_min, x_max = las.x.min(), las.x.max()
    y_min, y_max = las.y.min(), las.y.max()
    z_min, z_max = las.z.min(), las.z.max()
    
    print(f"元の座標範囲:")
    print(f"  X: {x_min:.6f} ~ {x_max:.6f} (幅: {x_max - x_min:.6f})")
    print(f"  Y: {y_min:.6f} ~ {y_max:.6f} (幅: {y_max - y_min:.6f})")
    print(f"  Z: {z_min:.6f} ~ {z_max:.6f} (幅: {z_max - z_min:.6f})")
    
    print(f"使用するスケール: {scale}")
    print(f"Minecraft座標の開始点: X={start_x}, Y={start_y}, Z={start_z}")
    
    # 地面のピーク（Zの最頻値）を求める
    z_rounded = np.round(las.z)
    unique_values, counts = np.unique(z_rounded, return_counts=True)
    ground_z = unique_values[np.argmax(counts)]
    print(f"地面のピーク（Z最頻値）: {ground_z:.6f}")
    
    # その下を一定値カット（例：-5m）
    valid_indices = las.z > ground_z - 5
    print(f"有効な点数: {np.sum(valid_indices)} / {len(las.z)}")
    
    # 有効な点のみで座標変換（開始点を加算）
    mc_x_float = (las.y[valid_indices] - y_min) * scale + start_x
    mc_z_float = (las.x[valid_indices] - x_min) * scale + start_z
    mc_y_float = (las.z[valid_indices] - z_min) * scale - 1 + start_y  # Y=1から開始（-1オフセット）+ 開始点
    
    # 整数化（四捨五入を使用）
    mc_x = np.round(mc_x_float).astype(int)
    mc_z = np.round(mc_z_float).astype(int)
    mc_y = np.round(mc_y_float).astype(int)
    
    # フィルタリングされた色情報も取得
    filtered_red = las.red[valid_indices]
    filtered_green = las.green[valid_indices]
    filtered_blue = las.blue[valid_indices]
    
    # 変換後の範囲
    print(f"\nMinecraft座標変換後:")
    print(f"  mc_x: {mc_x.min()} ~ {mc_x.max()} (幅: {mc_x.max() - mc_x.min()})")
    print(f"  mc_y: {mc_y.min()} ~ {mc_y.max()} (幅: {mc_y.max() - mc_y.min()})")
    print(f"  mc_z: {mc_z.min()} ~ {mc_z.max()} (幅: {mc_z.max() - mc_z.min()})")
    
    # スケール効果の詳細表示
    print(f"\n=== スケール効果の詳細 ===")
    print(f"元のX幅: {x_max - x_min:.6f} → Minecraft幅: {mc_x.max() - mc_x.min()} (スケール: {scale})")
    print(f"元のY幅: {y_max - y_min:.6f} → Minecraft幅: {mc_y.max() - mc_y.min()} (スケール: {scale})")
    print(f"元のZ幅: {z_max - z_min:.6f} → Minecraft幅: {mc_z.max() - mc_z.min()} (スケール: {scale})")
    
    # 座標密度の変化
    original_density = np.sum(valid_indices) / ((x_max - x_min) * (y_max - y_min) * (z_max - z_min))
    mc_density = np.sum(valid_indices) / ((mc_x.max() - mc_x.min()) * (mc_y.max() - mc_y.min()) * (mc_z.max() - mc_z.min()))
    print(f"座標密度: 元={original_density:.6f} → Minecraft={mc_density:.6f} (変化率: {mc_density/original_density:.2f}x)")
    
    # ユニークな座標の数をチェック
    unique_coords = len(set(zip(mc_x, mc_y, mc_z)))
    total_points = len(mc_x)
    print(f"\nユニークな座標数: {unique_coords} / {total_points} ({unique_coords/total_points*100:.1f}%)")
    
    # 最初の10点の詳細
    print(f"\n最初の10点の変換詳細:")
    for i in range(min(10, len(mc_x))):
        print(f"  点{i}: ({las.x[valid_indices][i]:.3f},{las.y[valid_indices][i]:.3f},{las.z[valid_indices][i]:.3f}) → ({mc_x_float[i]:.2f},{mc_y_float[i]:.2f},{mc_z_float[i]:.2f}) → ({mc_x[i]},{mc_y[i]},{mc_z[i]})")
    
    return mc_x, mc_y, mc_z, filtered_red, filtered_green, filtered_blue

def create_minecraft_code(mc_x, mc_y, mc_z, red, green, blue, lines_per_file, output_dir, thresholds: tuple[int, int, int]):
    """Minecraftコードを生成してファイルに保存"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 出力フォルダ内の既存ファイルを削除
    print(f"\n=== 出力フォルダのクリーンアップ ===")
    existing_files = [f for f in os.listdir(output_dir) if f.endswith('.py')]
    if existing_files:
        print(f"既存のPythonファイルを削除中: {len(existing_files)}個")
        for file in existing_files:
            file_path = os.path.join(output_dir, file)
            os.remove(file_path)
            print(f"  削除: {file}")
    else:
        print("既存のPythonファイルはありません")
    
    # 座標ごとにグループ化して重複を除去（代表色使用）
    print(f"\n=== 座標グループ化と重複除去 ===")
    
    # === 明度調整：全体を明るくする ===
    # 線形スケーリングで明度を調整（色の関係性を保持）
    if BRIGHTNESS_FACTOR != 1.0:
        print(f"明度調整: {BRIGHTNESS_FACTOR}倍（{BRIGHTNESS_FACTOR-1:.1%}明るく）")
        red = np.clip(red * BRIGHTNESS_FACTOR, 0, 65535).astype(np.uint16)
        green = np.clip(green * BRIGHTNESS_FACTOR, 0, 65535).astype(np.uint16)
        blue = np.clip(blue * BRIGHTNESS_FACTOR, 0, 65535).astype(np.uint16)
        
        # 調整後の範囲を表示
        print(f"調整後色範囲: R={red.min()}~{red.max()}, G={green.min()}~{green.max()}, B={blue.min()}~{blue.max()}")
    
    # === 閾値処理：明るい点を白ブロックに統一 ===
    # numpyの集合操作的な考え方：個別ループではなく配列全体を一括処理
    
    # 各色成分の閾値チェック（結果はTrue/Falseの配列）
    # いずれかの色成分が閾値を超えている点を特定（論理和で結合）
    # SQL的に書くなら: WHERE red > 61440 OR green > 61440 OR blue > 61440
    # 注意: LASファイルの色データは16bit（0-65535）なので、61440 = 240*256 で比較
    th_mask = (red > thresholds[0]) | (green > thresholds[1]) | (blue > thresholds[2])
    
    # 条件付き代入：閾値を超えている点のみを白(255,255,255)に設定
    # np.where(条件, 真の場合の値, 偽の場合の値)
    red = np.where(th_mask, 255, red)     # 条件がTrueなら255、そうでなければ元の値
    green = np.where(th_mask, 255, green) # 同上
    blue = np.where(th_mask, 255, blue)   # 同上

    # DataFrameを作成
    df = pd.DataFrame({
        'x': mc_x,
        'y': mc_y,
        'z': mc_z,
        'R': red,
        'G': green,
        'B': blue
    })
    
    print(f"元の点数: {len(df)}")
    
    # 座標ごとにグループ化して代表色を計算
    grouped = df.groupby(['x', 'y', 'z'])[['R', 'G', 'B']].mean().reset_index()
    print(f"重複除去後の座標数: {len(grouped)}")
    print(f"重複率: {(1 - len(grouped)/len(df))*100:.1f}%")
    
    # 各座標にブロックを割り当て
    grouped['block'] = grouped[['R', 'G', 'B']].apply(lambda row: rgb_to_block(row['R'], row['G'], row['B']), axis=1)
    
    # ファイル数計算の詳細表示
    print(f"\n=== ファイル分割の詳細 ===")
    print(f"実際の出力行数: {len(grouped)}")
    print(f"1ファイルあたりの行数: {lines_per_file}")
    print(f"計算されるファイル数: {math.ceil(len(grouped) / lines_per_file)}")
    print(f"最後のファイルの行数: {len(grouped) % lines_per_file if len(grouped) % lines_per_file != 0 else lines_per_file}")
    
    # コード分割出力
    def make_code(blocks_df, file_index):
        lines = []
        for _, row in blocks_df.iterrows():
            lines.append(f"    blocks.place({row['block']}, world({row['x']}, {row['y']}, {row['z']}))")
        return "\n".join(lines)
    
    for i in range(math.ceil(len(grouped) / lines_per_file)):
        start = i * lines_per_file
        end = min(start + lines_per_file, len(grouped))
        
        code_body = make_code(grouped.iloc[start:end], i)
        
        code = (
            "def on_on_chat():\n"
            f"{code_body}\n"
            "    player.tell(mobs.target(LOCAL_PLAYER), \"fin\")\n"
            "player.on_chat(\"run\", on_on_chat)\n"
        )
        
        file_path = f"{output_dir}/minecraft_code_part{i+1}.py"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        # 最初のファイルのみサンプル表示
        if i == 0:
            print(f"\n=== 出力サンプル ({file_path}) ===")
            lines = code.split('\n')
            for j, line in enumerate(lines[1:11]):  # 関数定義の次の10行
                print(f"{j+2:2}: {line}")
            print("...")
    
    print(f"\n=== 出力完了 ===")
    print(f"生成されたファイル数: {math.ceil(len(grouped) / lines_per_file)}個")
    print(f"出力フォルダ: {output_dir}")
    print(f"実際の出力行数: {len(grouped)}行")

# === メイン処理 ===
try:
    print(f"LASファイル読み込み中: {INPUT_FILE}")
    las = pylas.read(INPUT_FILE)
    
    # 構造の詳細調査
    debug_las_structure(las)
    
    # 座標変換
    mc_x, mc_y, mc_z, red, green, blue = process_las_to_minecraft(las, SCALE, START_X, START_Y, START_Z)
    
    # Minecraftコード生成
    create_minecraft_code(mc_x, mc_y, mc_z, red, green, blue, LINES_PER_FILE, OUTPUT_DIR, THRESHOLDS)
    print("\n処理完了!")
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
