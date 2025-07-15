# 這是 Python Flask 框架的範例程式碼，您需要安裝 Flask (pip install Flask requests)
# 並將其部署到一個雲端伺服器環境中才能運行。

from flask import Flask, jsonify, request
from flask_cors import CORS # 用於允許前端網頁存取
import requests # 用於發送 HTTP 請求
import json # 導入 json 模組用於解析錯誤
import xml.etree.ElementTree as ET # 用於解析 XML

app = Flask(__name__)
CORS(app) # 允許所有來源的跨域請求，在實際部署時應限制特定來源以增加安全性

# 中央氣象署開放資料平台 API Key (請替換為您的真實 Key)
CWA_API_KEY = 'CWA-DA27CC49-2356-447C-BDB3-D5AA4071E24B'
# 中央氣象署颱風警報 API 端點
# **重要：目前使用 W-C0034-005 (熱帶氣旋路徑) 獲取颱風資訊**
CWA_TYPHOON_API_URL = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0034-005'
# 中央氣象署 RSS 警報特報服務
CWA_RSS_WARNING_URL = 'https://www.cwa.gov.tw/rss/Data/cwa_warning.xml'

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

        # 嘗試解析 JSON，如果不是 JSON 格式，會拋出 ValueError
        data = api_response.json()
        return jsonify(data) # 將從氣象署獲取的資料直接返回給前端

    except requests.exceptions.RequestException as e:
        # 處理網路請求錯誤（例如連線失敗、超時等）
        print(f"向中央氣象署 API 請求失敗: {e}")
        # 嘗試獲取 CWA API 的回應內容，以便偵錯
        cwa_response_status = api_response.status_code if 'api_response' in locals() and api_response else None
        cwa_response_text = api_response.text if 'api_response' in locals() and api_response else None
        
        return jsonify({
            "error": "無法從中央氣象署獲取資料",
            "details": str(e),
            "cwa_response_status": cwa_response_status,
            "cwa_response_text": cwa_response_text
        }), 500
    except json.JSONDecodeError as e: # 捕獲 JSON 解析錯誤
        print(f"解析中央氣象署 API 回應失敗 (非 JSON 格式): {e}")
        cwa_response_status = api_response.status_code if 'api_response' in locals() and api_response else None
        cwa_response_text = api_response.text if 'api_response' in locals() and api_response else None
        return jsonify({
            "error": "解析 API 回應失敗 (非 JSON 格式)",
            "details": str(e),
            "cwa_response_status": cwa_response_status,
            "cwa_response_text": cwa_response_text
        }), 500
    except Exception as e:
        # 處理其他未知錯誤
        print(f"伺服器代理發生未知錯誤: {e}")
        return jsonify({"error": "伺服器內部錯誤", "details": str(e)}), 500

@app.route('/get-cwa-warnings', methods=['GET'])
def get_cwa_warnings():
    """
    這個路由會作為前端網頁的代理，去中央氣象署 RSS 服務獲取警報特報資料。
    """
    print("Received request for /get-cwa-warnings") # 新增：確認請求是否到達代理伺服器
    try:
        rss_response = requests.get(CWA_RSS_WARNING_URL)
        rss_response.raise_for_status() # 如果響應狀態碼不是 200，則拋出 HTTPError

        # 解析 XML
        root = ET.fromstring(rss_response.content)
        warnings = []
        
        # 定義要篩選的關鍵字
        keywords_to_filter = ["警報", "特報", "豪(大)雨特報", "低溫特報", "濃霧特報"]

        # 遍歷 RSS feed 中的每個 item
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            description = item.find('description').text if item.find('description') is not None else ''
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ''

            # 檢查標題或描述是否包含任何關鍵字
            is_relevant = False
            for keyword in keywords_to_filter:
                if keyword in title or keyword in description:
                    is_relevant = True
                    break
            
            if is_relevant:
                warnings.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "pubDate": pubDate
                })
        
        return jsonify({"success": True, "warnings": warnings})

    except requests.exceptions.RequestException as e:
        print(f"向中央氣象署 RSS 請求失敗: {e}")
        return jsonify({"error": "無法從中央氣象署 RSS 獲取資料", "details": str(e)}), 500
    except ET.ParseError as e:
        print(f"解析 RSS XML 失敗: {e}")
        return jsonify({"error": "解析 RSS XML 失敗", "details": str(e)}), 500
    except Exception as e:
        print(f"伺服器代理獲取警報發生未知錯誤: {e}")
        return jsonify({"error": "伺服器內部錯誤", "details": str(e)}), 500
