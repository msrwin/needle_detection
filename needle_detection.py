import cv2
import numpy as np
import csv
import time
import os
from datetime import datetime
import math
import winsound
import keyboard
import tkinter as tk
from tkinter import messagebox
import pygetwindow as gw  # ウィンドウ操作のためのライブラリ

# カメラのキャプチャ開始と解像度の設定
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# カメラが接続されていない場合の警告ウィンドウ
if not cap.isOpened():
    root = tk.Tk()
    root.withdraw()  # ウィンドウを非表示にする
    messagebox.showwarning("警告", "カメラが接続されていません。接続後に再度起動してください。")
    root.destroy()
    exit()
    
# テキスト領域のぼかし関数
def blur_text_region(image):
    # ぼかしたい領域の座標とサイズを指定
    regions = [
        (266, 151, 97, 22),  # 最初の領域 (x, y, w, h)
        (234, 173, 172, 22)   # 二つ目の領域 (x, y, w, h)
    ]
    
    for (x, y, w, h) in regions:
        # 文字領域を切り抜いてぼかす
        text_region = image[y:y+h, x:x+w]
        blurred_text_region = cv2.GaussianBlur(text_region, (25, 25), 0)
        
        # ぼかした文字領域を元の画像に重ねる
        image[y:y+h, x:x+w] = blurred_text_region
    
    return image

# 入力値の表示用変数
input_value = ""

# ファイルパスを設定
file_directory = "C:/Users/hinsyo/Desktop/ショア硬度計_データ取得/CSV"

# 現在の日付と時間を取得
current_datetime = datetime.now().strftime("%Y%m%d_%H-%M")

# 新しいCSVファイルを作成
new_file_name = f"SH_{current_datetime}.csv"
new_file_path = os.path.join(file_directory, new_file_name)

# CSVファイルへの書き込み回数を初期化
write_count = 0
paragraph_count = 1
last_time = time.time()  # 処理を開始する現在の時刻を記録

# Tkinterの設定
root = tk.Tk()
root.withdraw()  # 初期状態では非表示

# 警告メッセージを表示し、OKを押したかを確認する関数
def show_warning():
    return messagebox.askokcancel("警告", "ひとつ前のFrame番号に戻しますか？")

# CSVに入力する値を生成
with open(new_file_path, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Frame', 'Value1', 'Value2', 'Value3', 'Value4', 'Value5'])

    # 1つのテストピースごとに値を保持するリストを初期化
    values_per_piece = []
    last_value = None

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("カメラからフレームを読み取れませんでした。")
                break

            current_time = time.time()
            
            if current_time - last_time >= 0.017:  # 0.017秒毎に値の更新
                blurred = cv2.GaussianBlur(frame, (5, 5), 0)
                gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
                
                # 文字領域をぼかす
                frame = blur_text_region(frame)

                edges = cv2.Canny(gray, 100, 150, apertureSize=3)
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

                if lines is not None:
                    max_line_length = 0
                    selected_line = None

                    for line in lines:
                        x1, y1, x2, y2 = line[0]
                        line_length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                        
                        # 線の長さと角度に基づく条件を追加して不要な線を除外
                        if line_length > 100 and (80 <= abs(y2 - y1) <= 400 or 80 <= abs(x2 - x1) <= 400):
                            if line_length > max_line_length:
                                max_line_length = line_length
                                selected_line = line[0]

                    if selected_line is not None:
                        x1, y1, x2, y2 = selected_line
                        line_theta = np.arctan2(y2 - y1, x2 - x1)
                        theta_deg = (np.degrees(line_theta) + 360) % 360  # 0～360度に正規化

                        if 0 <= theta_deg <= 155:
                            calculated_value = 70 + (theta_deg / 155) * 70 - 0.5  # 左半分の出力値調整
                        elif 305 <= theta_deg <= 320:
                            calculated_value = 70 - ((360 - theta_deg) / 155) * 70                    
                        elif 205 <= theta_deg <= 360:
                            calculated_value = 70 - ((360 - theta_deg) / 155) * 70
                        else:
                            calculated_value = 70  # デフォルト値として70を使用

                        if x1 < frame.shape[1] / 2:  # 左半分の場合
                            calculated_value = (calculated_value + 100) % 140  # 反時計回りに100度回転
                        else:  # 右半分の場合
                            if 155 <= theta_deg <= 360:
                                calculated_value = 70 - ((360 - theta_deg) / 155) * 70 + 40.5  # 出力値微調整
                            elif 80 <= theta_deg <= 205:
                                calculated_value = 70 + (theta_deg / 100) * 70
                            elif 0 <= theta_deg < 36:
                                calculated_value = 110 + (theta_deg / 100) * 50
                            elif 36 <= theta_deg < 80:
                                calculated_value = 129 + (theta_deg / 100) * 50 + 38  # 出力値微調整

                        if calculated_value >= 128:
                            calculated_value = calculated_value - 60
                        else:
                            last_value = calculated_value

                        if theta_deg > 270 and calculated_value < 30:  # 30以下の処理
                            last_value = calculated_value
                        else:
                            last_value = calculated_value

                        if theta_deg < 90 and calculated_value > 110:  # 110以上の処理
                            last_value = calculated_value
                        else:
                            last_value = calculated_value

                last_time = current_time  # 最終処理時間を更新する

            if last_value is not None:
                if selected_line is not None:
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 4)

                # カメラ画面に小数点以下1桁まで表示
                cv2.putText(frame, f"Value: {last_value:.1f}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Frame番号の表示
                frame_number = f"{paragraph_count} - {write_count % 5 + 1}"
                cv2.putText(frame, f"Frame: {frame_number}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 255, 0), 2)
                # 直接入力した値を表示
                cv2.putText(frame, f"Input: {input_value}", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
 
            # 画面中央から上、左、右の端に青い点を描画
            center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
            cv2.circle(frame, (center_x, 50), 3, (255, 100, 100), -1)
            cv2.circle(frame, (center_x - 200, center_y), 3, (255, 100, 100), -1)
            cv2.circle(frame, (center_x + 200, center_y), 3, (255, 100, 100), -1)
            cv2.imshow('frame', frame)
           
            key = cv2.waitKey(1)

            # ESCキーが押されたら処理を終了
            if key == 27:
                break

            # ウィンドウが閉じられたら処理を終了
            if cv2.getWindowProperty('frame', cv2.WND_PROP_VISIBLE) < 1:
                break

            elif key == 32:  # スペースキーが押された場合の処理
                winsound.Beep(1000, 100)  # ビープ音を鳴らす

                # テストピースごとに値をリストに追加（四捨五入して小数点1桁にする）
                values_per_piece.append(round(last_value, 1))
                write_count += 1

                # 5回の計測ごとに値を書き込み、リストを初期化
                if len(values_per_piece) == 5:
                    mean_value = np.mean(values_per_piece)
                    max_value = max(values_per_piece)
                    
                    # 平均から10以上離れている値、または最大値より15以上低い値がある場合
                    if any(abs(value - mean_value) > 10 for value in values_per_piece) or any(max_value - value > 15 for value in values_per_piece):
                        print("異常値を検出しました。再測定を行います。")
                        winsound.Beep(500, 500)  # 異常値検出時のビープ音
                        values_per_piece = []  # リストを初期化して再測定
                    else:
                        print(f"Number {paragraph_count}: {values_per_piece}")
                        csv_writer.writerow([paragraph_count] + [round(value, 1) for value in values_per_piece])
                        values_per_piece = []
                        
                        # Frame番号を更新
                        if write_count % 5 == 0:
                            winsound.Beep(1500, 500)  # ビープ音を鳴らす
                            paragraph_count += 1 
                            
            # テンキーのキーが押された場合の処理
            if 48 <= key <= 57:  # 0-9
                if len(input_value) < 3:  # 最大3文字までの入力制限
                    input_value += chr(key)

            # バックスペースキーが押された場合の処理
            elif key == 8:  # Backspace key
                input_value = input_value[:-1]  # 最後の文字を削除

            # スペースキーが押された場合の処理
            elif key == 32:  # Space key
                input_value = ""

            # エンターキーが押された場合の処理
            elif key == 13:  # Enter key
                winsound.Beep(1000, 100)  # ビープ音を鳴らす
                if input_value:
                    
                    try:
                        float_value = float(input_value)
                        values_per_piece.append(round(float_value, 1))
                        write_count += 1

                        # 5回の計測ごとに値を書き込み、リストを初期化
                        if len(values_per_piece) == 5:
                            mean_value = np.mean(values_per_piece)
                            max_value = max(values_per_piece)
                            
                            # 平均から10以上離れている値、または最大値より15以上低い値がある場合
                            if any(abs(value - mean_value) > 10 for value in values_per_piece) or any(max_value - value > 15 for value in values_per_piece):
                                print("異常値を検出しました。再測定を行います。")
                                winsound.Beep(500, 500)  # 異常値検出時のビープ音
                                values_per_piece = []  # リストを初期化して再測定
                            else:
                                print(f"Number {paragraph_count}: {values_per_piece}")
                                csv_writer.writerow([paragraph_count] + [round(value, 1) for value in values_per_piece])
                                values_per_piece = []
                                
                                # Frame番号を更新
                                if write_count % 5 == 0:
                                    winsound.Beep(1500, 500)  # ビープ音を鳴らす
                                    paragraph_count += 1
                                    
                    except ValueError:
                        print("無効な入力値です。")
                        
                input_value = ""  # 入力値をリセット

            # デリートキーが押された場合の処理
            elif keyboard.is_pressed("Delete"):  # Delete key
                if show_warning():  # 警告メッセージを表示し、OKが押された場合                   
                    if paragraph_count <= 1:
                        print("これ以上戻せません。")  
                    else:
                        write_count = 0  # write_countを1にリセット
                        paragraph_count -= 1  # Frameをひとつ前に戻す
                        values_per_piece = []  # リストを初期化して再測定
                        print(f"Frame番号をひとつ前に戻しました: {paragraph_count} - {write_count % 5 + 1}") 
                                       
                else:
                    print("キャンセルされました。")

                # 警告表示後、カメラウィンドウをアクティブにする
                window = gw.getWindowsWithTitle('frame')[0]
                window.activate()

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sub_file_name = f"SH_{current_datetime}_sub.csv"
        sub_file_path = os.path.join(file_directory, sub_file_name)
        print(f"データを書き込む新しいファイルを作成します: {sub_file_path}")

        with open(sub_file_path, 'w', newline='') as sub_csv_file:
            sub_csv_writer = csv.writer(sub_csv_file)
            sub_csv_writer.writerow(['Frame', 'Value1', 'Value2', 'Value3', 'Value4', 'Value5'])
            
            for row in values_per_piece:
                if all(row):  # すべての要素が存在するかどうかを確認
                    sub_csv_writer.writerow(row)

cap.release()
cv2.destroyAllWindows()
