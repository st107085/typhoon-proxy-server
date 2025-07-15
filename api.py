# 這是 Python Flask 框架的範例程式碼，您需要安裝 Flask (pip install Flask requests)
# 並將其部署到一個雲端伺服器環境中才能運行。

from flask import Flask, jsonify, request
from flask_cors import CORS # 用於允許前端網頁存取
import requests # 用於發送 HTTP 請求

app = Flask(__name__)
CORS(app) # 允許所有來源的跨域請求，在實際部署時應限制特定來源以增加安全性

# 中央氣象署開放資料平台 API Key (請替換為您的真實 Key)
CWA_API_KEY = 'CWA-DA27CC49-2356-447C-BDB3-D5AA4071E24B'
# 中央氣象署颱風警報 API 端點
CWA_TYPHOON_API_URL = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0058-001'

@app.route('/get-typhoon-data', methods=['GET'])
def get_typhoon_data():
    """
    這個路由會作為前端網頁的代理，去中央氣象署 API 獲取颱風資料。
    """
    try:
        # 向中央氣象署 API 發送請求
        # 這裡直接在 URL 中包含 Authorization 參數
        api_response = requests.get(f"{CWA_TYPHOON_API_URL}?Authorization={CWA_API_KEY}")
        api_response.raise_for_status() # 如果響應狀態碼不是 200，則拋出 HTTPError

        data = api_response.json()
        return jsonify(data) # 將從氣象署獲取的資料直接返回給前端

    except requests.exceptions.RequestException as e:
        # 處理網路請求錯誤（例如連線失敗、超時等）
        print(f"向中央氣象署 API 請求失敗: {e}")
        return jsonify({"error": "無法從中央氣象署獲取資料", "details": str(e)}), 500
    except ValueError as e:
        # 處理 JSON 解析錯誤
        print(f"解析中央氣象署 API 回應失敗: {e}")
        return jsonify({"error": "解析 API 回應失敗", "details": str(e)}), 500
    except Exception as e:
        # 處理其他未知錯誤
        print(f"伺服器代理發生未知錯誤: {e}")
        return jsonify({"error": "伺服器內部錯誤", "details": str(e)}), 500

if __name__ == '__main__':
    # 在本地運行伺服器，僅供開發測試使用
    # 在實際部署到雲端服務時，通常不需要這段，雲端服務會有自己的啟動方式
    app.run(host='0.0.0.0', port=5000)
