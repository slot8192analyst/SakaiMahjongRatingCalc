import csv
from statistics import mean
from datetime import datetime, date
import os

def normalize_date(d):
    """日付を統一フォーマットに変換"""
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d
    elif isinstance(d, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y/%-m/%-d"):
            try:
                return datetime.strptime(d, fmt).date()
            except ValueError:
                continue
        return d
    return d

def format_date(d):
    """日付をYYYY/M/D形式に変換"""
    if isinstance(d, date):
        return f"{d.year}/{d.month}/{d.day}"
    elif isinstance(d, str):
        return d
    return str(d)

def clean_value(val):
    """値をクリーニング（カンマ削除など）"""
    if val is None or val == '':
        return None
    if isinstance(val, str):
        val = val.strip().replace(',', '')
    try:
        return int(val) if val.isdigit() else float(val)
    except (ValueError, AttributeError):
        return None

# ファイルパス設定
rank_file = input("入力ファイル（半荘順位.csv）のパスを入力してください（空欄でデフォルト）: ").strip().strip('"').strip("'")
if not rank_file:
    rank_file = "半荘順位.csv"

if not os.path.exists(rank_file):
    print("❌ 入力ファイルが見つかりません。")
    input("何かキーを押して終了してください...")
    exit(1)

change_file = "Rt.変動値.csv"
rating_file = "Rt.算出.csv"

players_all = ["坂井", "中江", "福原", "遥平", "大前", "高木", "志村", "池谷", "米森", "浜島", "犬塚", "目黒", "梶田", "磯", "杉崎", "横塚","安達"]

# =======================
# 入力ファイルの読み込み
# =======================
rank_data = []
try:
    with open(rank_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rank_data = list(reader)
        print(f"✅ 半荘順位.csvを読み込み: {len(rank_data)}行")
except Exception as e:
    print(f"❌ 半荘順位.csvの読み込みに失敗: {e}")
    input("何かキーを押して終了してください...")
    exit(1)

# =======================
# プレイヤーごとの参加対局数を事前計算
# =======================
games_played_by_player = {player: 0 for player in players_all}

if os.path.exists(change_file):
    try:
        with open(change_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for player in players_all:
                    # このプレイヤーの変動値を取得
                    delta_val = row.get(player)
                    if delta_val:
                        try:
                            delta = float(delta_val)
                            # 0でない変動値がある = 参加している
                            if delta != 0:
                                games_played_by_player[player] += 1
                        except (ValueError, TypeError):
                            pass
        print(f"✅ 既存の参加対局数を計算: {games_played_by_player}")
    except Exception as e:
        print(f"⚠️  参加対局数の計算に失敗: {e}")

# =======================
# 既存の出力ファイルを読み込み（フォーマット変換対応）
# =======================
existing_date_game = set()
if os.path.exists(change_file):
    try:
        with open(change_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 新旧フォーマットに対応
                date_val = row.get('日付') or row.get('Date.')
                game_val = row.get('半荘') or row.get('game')
                if date_val and game_val and date_val != '1999/1/1':
                    date_normalized = normalize_date(date_val)
                    existing_date_game.add((date_normalized, str(game_val)))
        print(f"✅ Rt.変動値.csvから既処理データを確認: {len(existing_date_game)}件")
    except Exception as e:
        print(f"⚠️  Rt.変動値.csvの読み込みに失敗: {e}")

# 現在のレーティングを取得（フォーマット変換対応）
current_rating = {}
if os.path.exists(rating_file):
    try:
        with open(rating_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                # 最後の有効な行から現在のレーティングを取得
                for row in reversed(rows):
                    date_val = row.get('日付') or row.get('Date.')
                    if date_val and date_val != '1999/01/01' and date_val != '1999/1/1':
                        for player in players_all:
                            val = row.get(player)
                            if val:
                                cleaned = clean_value(val)
                                if cleaned:
                                    current_rating[player] = cleaned
                        break
        print(f"✅ Rt.算出.csvから現在のレーティングを取得: {len(current_rating)}名")
    except Exception as e:
        print(f"⚠️  Rt.算出.csvの読み込みに失敗: {e}")

# 初期値を1500に設定（データがない場合）
for player in players_all:
    if player not in current_rating:
        current_rating[player] = 1500.0

print(f"📊 現在のレーティング: {current_rating}")

# =======================
# 新規対局データの抽出
# =======================
output_rows = []
for row in rank_data:
    date_val = row.get('日付') or row.get('Date') or row.get('Date.')
    game_val = row.get('半荘') or row.get('game') or row.get('game ')
    
    if not date_val or not game_val:
        print(f"⚠️  スキップ: 日付={date_val}, 半荘={game_val}")
        continue
    
    match_date = normalize_date(date_val)
    game = str(game_val).strip()
    
    if not match_date or not game:
        continue
    
    # 既に処理済みかチェック
    if (match_date, game) in existing_date_game:
        print(f"⏭️  スキップ（既処理）: {match_date} game {game}")
        continue
    
    # 参加プレイヤーを抽出（順位が入っている）
    players = []
    for player in players_all:
        val = row.get(player)
        rank = clean_value(val)
        if rank and isinstance(rank, (int, float)) and 1 <= rank <= 4:
            players.append(player)
    
    if players:
        output_rows.append((match_date, game, players))
        print(f"✅ 新規対局: {match_date} game {game} - プレイヤー: {players}")

if not output_rows:
    print("❌ 処理対象の新規対局データがありません。")
    input("何かキーを押して終了してください...")
    exit(0)

print(f"🎯 処理対象: {len(output_rows)}件の新規対局")

# =======================
# レーティング計算
# =======================
rank_points = {1: 30, 2: 10, 3: -10, 4: -30}

# Rt.変動値用のデータ準備
change_output = []
# Rt.算出用のデータ準備
rating_output = []

for match_date, game, players in output_rows:
    # 平均レーティングを計算
    avg_list = [current_rating.get(p) for p in players if isinstance(current_rating.get(p), (int, float))]
    avg_rt = round(mean(avg_list), 2) if avg_list else 1500.0
    
    # Rt.変動値シート用の行を作成
    change_row = {
        '日付': format_date(match_date),
        '半荘': game,
        '平均Rt.': avg_rt
    }
    
    # Rt.算出シート用の行を作成
    rating_row = {
        '日付': format_date(match_date),
        '半荘': game
    }
    
    # 各プレイヤーのレーティング変動を計算
    for player in players_all:
        if player in players:
            current_rt = current_rating.get(player)
            if current_rt is None or avg_rt is None:
                rt_delta = 0
            else:
                # このプレイヤーの参加対局数を使用
                effective_games_played = min(games_played_by_player[player], 400)
                trial_factor = 1 - (effective_games_played * 0.002)
                correction = (avg_rt - current_rt) / 40
                
                # ランク情報を取得
                rank = None
                for rank_row in rank_data:
                    rank_date = rank_row.get('日付') or rank_row.get('Date') or rank_row.get('Date.')
                    rank_game = rank_row.get('半荘') or rank_row.get('game') or rank_row.get('game ')
                    if (normalize_date(rank_date) == match_date and 
                        str(rank_game).strip() == game):
                        rank_val = rank_row.get(player)
                        rank = clean_value(rank_val)
                        break
                
                point = rank_points.get(rank, 0) if rank else 0
                rt_delta = round(trial_factor * (point + correction), 2)
            
            change_row[player] = rt_delta
            
            # 新しいレーティングを計算
            if isinstance(current_rating.get(player), (int, float)) and isinstance(rt_delta, (int, float)):
                new_rt = round(current_rating[player] + rt_delta, 2)
                current_rating[player] = new_rt
                rating_row[player] = new_rt
            else:
                rating_row[player] = current_rating.get(player, 1500.0)
        else:
            change_row[player] = 0
            rating_row[player] = current_rating.get(player, 1500.0)
    
    change_output.append(change_row)
    rating_output.append(rating_row)
    
    # この対局を処理したので、参加プレイヤーの対局数をインクリメント
    for player in players:
        games_played_by_player[player] += 1

# =======================
# Rt.変動値.csvに追記（フォーマット統一）
# =======================
fieldnames_change = ['日付', '半荘', '平均Rt.'] + players_all

# 既存ファイルを読み込んで、新規行を追加（フォーマット統一）
existing_change_rows = []
if os.path.exists(change_file):
    try:
        with open(change_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 新しいフォーマットに統一
                new_row = {}
                new_row['日付'] = row.get('日付') or row.get('Date.')
                new_row['半荘'] = row.get('半荘') or row.get('game')
                new_row['平均Rt.'] = row.get('平均Rt.')
                
                # 全プレイヤーのデータをコピー
                for player in players_all:
                    new_row[player] = row.get(player, 0)
                
                existing_change_rows.append(new_row)
    except Exception as e:
        print(f"⚠️  既存ファイル読み込み時エラー: {e}")

all_change_rows = existing_change_rows + change_output

with open(change_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_change)
    writer.writeheader()
    writer.writerows(all_change_rows)

print(f"✅ Rt.変動値.csvに{len(change_output)}件の対局を追記")

# =======================
# Rt.算出.csvに追記（フォーマット統一）
# =======================
fieldnames_rating = ['日付', '半荘'] + players_all

# 既存ファイルを読み込んで、新規行を追加（フォーマット統一）
existing_rating_rows = []
if os.path.exists(rating_file):
    try:
        with open(rating_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 新しいフォーマットに統一
                new_row = {}
                new_row['日付'] = row.get('日付') or row.get('Date.')
                new_row['半荘'] = row.get('半荘') or row.get('game')
                
                # 全プレイヤーのデータをコピー
                for player in players_all:
                    val = row.get(player)
                    new_row[player] = val if val else 1500.0
                
                existing_rating_rows.append(new_row)
    except Exception as e:
        print(f"⚠️  既存ファイル読み込み時エラー: {e}")

all_rating_rows = existing_rating_rows + rating_output

with open(rating_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_rating)
    writer.writeheader()
    writer.writerows(all_rating_rows)

print(f"✅ Rt.算出.csvに{len(rating_output)}件の対局を追記")

print(f"\n✅ 完了！")
print(f"  - Rt.変動値: {change_file}")
print(f"  - Rt.算出: {rating_file}")
print(f"📊 最終参加対局数: {games_played_by_player}")

# プログラム終了時にキー入力待機
input("\n何かキーを押して終了してください...")
