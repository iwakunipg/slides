---
marp: true
theme: default
paginate: true
---

# LAS → Minecraft コード生成<br>チュートリアル（最新版）

---

## 📦 LASファイルとは？

**LAS (LASer file format)** は、3DスキャンやLiDAR（ライダー）で取得した**点群データ**を保存する標準的なファイル形式です。

### 点群データとは？
- 3D空間に散らばった**無数の点**の集合
- 各点には**座標（X, Y, Z）**と**色情報（RGB）**が含まれる
- レーザースキャナーや3Dスキャナーで取得

### 使用例
- 🏗️ 建築物の3Dモデリング
- 🗺️ 地形の測量
- 🎨 彫刻やオブジェクトのデジタル化

---

## このチュートリアルの目的 🎯

**LASファイルから、Minecraft Education Editionで再現できるコードを生成します！**

### 処理の流れ（最新版）

```
1. LASファイルを読み込む
2. 座標をMinecraft用に正規化
3. 色情報を処理
4. 重複座標を除去
5. ブロック配置コードを生成
```

---

### 最新版の主な機能
- ✅ 16bit色データ対応
- ✅ 地面フィルタリング（ノイズ除去）
- ✅ 明度調整
- ✅ 閾値処理（明るい点を白ブロックに統一）
- ✅ 重複座標の除去
- ✅ 詳細なデバッグ情報出力
- ✅ Minecraft用の関数ラッパー生成

---

## 必要なライブラリ

### 📚 使用するPythonライブラリ

```python
import pylas
import numpy as np
import pandas as pd
```

### インストール方法

```bash
pip install pylas numpy pandas
```

### 各ライブラリの役割
- **pylas**: LASファイルの読み込み
- **numpy**: 配列操作、地面フィルタリング
- **pandas**: 重複座標の除去

---

## 設定と定数（1/2）

### ⚙️ 基本設定

```python
INPUT_FILE = "iwakunizushi.las"
SCALE = 200.0
LINES_PER_FILE = 20000
BRIGHTNESS_FACTOR = 1.1
THRESHOLDS = (250*256, 250*256, 250*256)
```

### 設定項目の説明
- **INPUT_FILE**: 変換したいLASファイルのパス
- **SCALE**: スケール倍率（大きいほど拡大）
- **LINES_PER_FILE**: 1ファイルあたりの最大行数
- **BRIGHTNESS_FACTOR**: 明度調整（1.1 = 10%明るく）
- **THRESHOLDS**: 明るい点を白ブロックに統一する閾値

---

## 設定と定数（2/2）

### 🎨 ブロックカラー定義

Minecraftのブロックと色の対応表を定義します。

```python
BLOCK_COLOR_MAP = [
    ("WOOL", (0.95, 0.95, 0.95)),
    ("RED_WOOL", (0.65, 0.17, 0.16)),
    # ... 他にも多数
]
```

### 仕組み
- 各ブロックにはRGB値（0.0〜1.0）が定義されている
- LASファイルの色情報と比較して、**最も近い色のブロック**を選ぶ
- ユークリッド距離（色の差）で判定

---

## 関数の概要

### 🔧 主要な関数（最新版）

1. **`debug_las_structure`**: LASファイルの構造を調べる
2. **`rgb_to_block`**: 色から最も近いブロックを決定（16bit対応）
3. **`process_las_to_minecraft`**: 座標をMinecraft用に正規化（地面フィルタリング含む）
4. **`create_minecraft_code`**: コード生成・分割出力

### 処理の流れ

```
LASファイル → pylas.read() → process_las_to_minecraft() → create_minecraft_code()
```

---

## 関数詳細（1/5） - デバッグ関数

### 🔍 `debug_las_structure` 関数

```python
def debug_las_structure(las):
    """LASファイルの構造を詳しく調べる"""
    print("=== LASファイル構造詳細 ===")
    print(f"X範囲: {las.x.min():.6f} ~ {las.x.max():.6f}")
    print(f"Red範囲: {las.red.min()} ~ {las.red.max()}")
```

### 用途
- LASファイルの内容を確認
- 色データが8bit（0-255）か16bit（0-65535）かを判定
- 座標の範囲を確認してスケール設定の参考にする

---

## 関数詳細（2/5） - 色からブロック選択

### 🎨 `rgb_to_block` 関数（16bit対応）

```python
def rgb_to_block(r, g, b):
    if r > 255 or g > 255 or b > 255:
        # 16bit値を8bitに変換
        r, g, b = r/65535*255, g/65535*255, b/65535*255
    r, g, b = r/255, g/255, b/255
    # ユークリッド距離で最も近いブロックを選択
    return best_block
```

### 改善点
- **16bit色データ対応**: 0-65535の範囲の色データを自動検出・変換
- 8bit（0-255）と16bit（0-65535）の両方に対応

---

## 関数詳細（3/5） - 座標正規化

### 📐 `process_las_to_minecraft` 関数

```python
def process_las_to_minecraft(las, scale):
    # 地面のピーク（Zの最頻値）を求める
    ground_z = 最頻値(las.z)
    valid_indices = las.z > ground_z - 5
    
    # 有効な点のみで座標変換
    mc_x = np.round((las.y - y_min) * scale).astype(int)
    mc_z = np.round((las.x - x_min) * scale).astype(int)
    mc_y = np.round((las.z - z_min) * scale - 1).astype(int)
```

### 重要なポイント
- **地面フィルタリング**: Z座標の最頻値から地面を検出し、ノイズを除去
- **軸の入れ替え**: LASのX/YをMinecraftのZ/Xに対応
- **四捨五入**: `np.round()`でより正確な整数化

---

## 関数詳細（4/5） - 色処理と重複除去

### 🎨 明度調整・閾値処理

```python
# 明度調整
if BRIGHTNESS_FACTOR != 1.0:
    red = np.clip(red * BRIGHTNESS_FACTOR, 0, 65535)

# 閾値処理：明るい点を白ブロックに統一
th_mask = (red > thresholds[0]) | (green > thresholds[1]) | (blue > thresholds[2])
red = np.where(th_mask, 255, red)
```

### 重複除去

```python
df = pd.DataFrame({'x': mc_x, 'y': mc_y, 'z': mc_z, 'R': red, 'G': green, 'B': blue})
grouped = df.groupby(['x', 'y', 'z'])[['R', 'G', 'B']].mean().reset_index()
```

---

## 関数詳細（5/5） - コード生成と出力

### 💻 コード生成

```python
grouped['block'] = grouped[['R', 'G', 'B']].apply(
    lambda row: rgb_to_block(row['R'], row['G'], row['B']), axis=1
)

for i in range(math.ceil(len(grouped) / lines_per_file)):
    code = (
        "def on_on_chat():\n"
        f"{code_body}\n"
        "player.on_chat(\"run\", on_on_chat)\n"
    )
```

### 生成されるコード例

```python
def on_on_chat():
    blocks.place(blocks.WOOL, world(10, 5, 20))
    blocks.place(blocks.RED_WOOL, world(11, 5, 20))
player.on_chat("run", on_on_chat)
```

---

## メイン処理の流れ

### 🚀 実行ステップ

```python
las = pylas.read(INPUT_FILE)
debug_las_structure(las)
mc_x, mc_y, mc_z, red, green, blue = process_las_to_minecraft(las, SCALE)
create_minecraft_code(mc_x, mc_y, mc_z, red, green, blue, ...)
```

### 処理の流れ図

```
LASファイル → pylas.read() → process_las_to_minecraft() → create_minecraft_code()
```

---

## 座標変換の詳細

### 🔄 座標系の変換

#### LAS座標系
- **X, Y, Z**: 実世界の座標（メートル単位）
- 例: `(123.456, 789.012, 45.678)`

#### Minecraft座標系
- **X, Y, Z**: ブロック単位の整数座標
- 例: `(1234, 456, 7890)`

### 変換式

```python
# 地面フィルタリング
ground_z = 最頻値(las.z)
valid_indices = las.z > ground_z - 5

# 座標変換
mc_x = np.round((las.y - y_min) * SCALE).astype(int)
```

---

## 色処理の詳細

### 🎨 色処理の3ステップ

#### ステップ1: 16bit対応
```python
if r > 255 or g > 255 or b > 255:
    r, g, b = r/65535*255, g/65535*255, b/65535*255
```

#### ステップ2: 明度調整
```python
if BRIGHTNESS_FACTOR != 1.0:
    red = np.clip(red * BRIGHTNESS_FACTOR, 0, 65535)
```

#### ステップ3: 閾値処理
```python
th_mask = (red > 61440) | (green > 61440) | (blue > 61440)
red = np.where(th_mask, 255, red)
```

---

## 重複座標の除去

### 🔄 重複除去の仕組み

#### 問題
- 同じ座標に複数の点が存在することがある
- スケール変換で複数の点が同じ整数座標になる

#### 解決方法
```python
df = pd.DataFrame({'x': mc_x, 'y': mc_y, 'z': mc_z, 'R': red, 'G': green, 'B': blue})
grouped = df.groupby(['x', 'y', 'z'])[['R', 'G', 'B']].mean().reset_index()
```

#### 結果
- 同じ座標の点は1つに統合
- 色は平均値を使用
- 重複率を表示（例: "重複率: 15.3%"）

---

## 色マッチングの仕組み

### 🎨 色からブロックを選ぶ方法

#### ステップ1: RGB値を正規化
```python
r, g, b = 255, 128, 64
r, g, b = r/255, g/255, b/255  # → (1.0, 0.5, 0.25)
```

#### ステップ2: 各ブロックとの距離を計算
```python
# ORANGE_WOOL の色: (0.92, 0.53, 0.25)
dist = (1.0-0.92)² + (0.5-0.53)² + (0.25-0.25)² = 0.0073
```

#### ステップ3: 最も距離が小さいブロックを選択
- 距離が小さい = 色が近い
- そのブロックを使用

---

## 出力ファイルの構造

### 📄 生成されるファイル

```
minecraft_code_output/
├── minecraft_code_part1.py
├── minecraft_code_part2.py
└── ...
```

### ファイル内容の例

```python
def on_on_chat():
    blocks.place(blocks.WOOL, world(10, 5, 20))
    blocks.place(blocks.RED_WOOL, world(11, 5, 20))
player.on_chat("run", on_on_chat)
```

### Minecraft Education Editionでの実行方法
1. 生成されたファイルをインポート
2. チャットで`run`と入力
3. ブロックが配置されていく様子を確認！

---

## 最新版の改善点まとめ

### ✨ 追加された機能

1. **16bit色データ対応** - 8bit（0-255）と16bit（0-65535）の両方に対応、自動検出・変換
2. **地面フィルタリング** - Z座標の最頻値から地面を検出、ノイズを自動除去
3. **明度調整** - `BRIGHTNESS_FACTOR`で全体の明度を調整可能
4. **閾値処理** - 明るすぎる点を白ブロックに統一、見た目を改善

---

### ✨ 追加された機能（続き）

5. **重複座標の除去** - pandasの`groupby`で重複を除去、色は平均値を使用
6. **詳細なデバッグ情報** - LASファイルの構造を確認、各処理ステップで詳細なログを出力
7. **Minecraft用関数ラッパー** - `on_on_chat`関数でラップ、チャットで`run`と入力すると実行

---

## まとめ

### 📝 このチュートリアルで学んだこと

1. **LASファイルとは**: 3Dスキャンの点群データを保存する形式
2. **座標変換**: 実世界の座標をMinecraft座標に変換（地面フィルタリング含む）
3. **色処理**: 16bit対応、明度調整、閾値処理
4. **重複除去**: 同じ座標の点を統合
5. **色マッチング**: RGB値から最も近い色のブロックを選択
6. **コード生成**: 点群データからMinecraftコードを自動生成
7. **ファイル分割**: 大きなデータを実行可能なサイズに分割

---

### 🎯 応用のヒント

- **SCALE**を調整してサイズを変更（例: 10.0 → 200.0）
- **BRIGHTNESS_FACTOR**で明度を調整（例: 1.0 → 1.2）
- **THRESHOLDS**で閾値を調整
- **BLOCK_COLOR_MAP**にブロックを追加して色の表現を豊かに
- 異なるLASファイルで様々なオブジェクトを再現

### 🚀 次のステップ

実際にLASファイルを用意して、Minecraftで3Dオブジェクトを再現してみましょう！

---

## 補足: よくある質問

### Q1: SCALEの値はどう決める？
**A**: 点群データのサイズと、Minecraftで再現したい大きさに応じて調整します。
- 小さい値（例: 10.0）→ 小さく再現
- 大きい値（例: 200.0）→ 大きく再現

### Q2: なぜファイルを分割するの？
**A**: Minecraft Education Editionには実行行数の制限があるため、大きな点群データをそのまま実行できません。分割することで、順番に実行できます。

---

### Q3: 16bit色データってなに？
**A**: 通常の色データは8bit（0-255）ですが、高精度なスキャナーでは16bit（0-65535）の色データが使われることがあります。最新版は自動的に検出・変換します。

### Q4: 地面フィルタリングは必要？
**A**: 3Dスキャンでは地面より下のノイズが含まれることがあります。地面フィルタリングで自動的に除去できます。

### Q5: 重複座標の除去は必要？
**A**: スケール変換で複数の点が同じ整数座標になることがあります。重複を除去することで、より正確な再現が可能になります。

---

## 参考資料

### 📚 関連リンク

- **LAS形式**: ASPRS LAS Specification
- **pylas**: pylas Documentation
- **Minecraft Education Edition**: 公式サイト
- **numpy**: NumPy Documentation
- **pandas**: Pandas Documentation

### 🔧 使用ライブラリ

- `pylas`: LASファイルの読み書き
- `numpy`: 数値計算、配列操作
- `pandas`: データ処理、重複除去

---

## おわりに

### 🎉 お疲れ様でした！

このチュートリアルでは、3Dスキャンデータ（LASファイル）をMinecraftで再現する方法を学びました。

最新版では、16bit色データ対応、地面フィルタリング、明度調整、重複除去など、より実用的な機能が追加されています。

実際にコードを実行して、自分の3DオブジェクトをMinecraftで再現してみてください！

**Happy Coding! 🍑**
