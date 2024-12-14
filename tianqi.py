import requests
import json
import time
import hmac
import hashlib
import base64
from urllib.parse import quote
from datetime import datetime

# 钉钉机器人的Webhook URL（不包含签名部分）和Secret
webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxxxxxxxxxxxxx"   # 请替换为你的实际webhook_url
secret = 'xxxxxxxxxxxxxxxxxxx'  # 请替换为你的实际Secret

# QWeather API配置
qweather_api_key = 'xxxxxxxxxxxxxxxxxxx'  # 替换为你的QWeather API Key
qweather_api_url = 'https://devapi.qweather.com/v7/weather/now'  # 使用免费订阅的API主机
location = '101010100'  # 北京市的location ID


def generate_sign(secret, timestamp):
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(
        secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    sign = quote(base64.b64encode(hmac_code))
    return sign


def get_weather(api_key, location):
    headers = {
        'X-QW-Api-Key': api_key  # 使用X-QW-Api-Key头部进行认证
    }
    params = {
        'location': location
    }

    try:
        response = requests.get(qweather_api_url, headers=headers, params=params)
        print(f"API Status Code: {response.status_code}")  # 调试：打印状态码
        print("Full API Response:", response.text)  # 调试：打印完整响应

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                now = data.get('now', {})
                temp = now.get('temp', '无法获取温度')
                feels_like = now.get('feelsLike', '无法获取体感温度')
                text = now.get('text', '无法获取天气描述')
                wind_dir = now.get('windDir', '无法获取风向')
                wind_scale = now.get('windScale', '无法获取风力等级')
                humidity = now.get('humidity', '无法获取湿度')
                precip = now.get('precip', '无法获取降水量')
                pressure = now.get('pressure', '无法获取气压')
                vis = now.get('vis', '无法获取能见度')
                cloud = now.get('cloud', '无法获取云量')
                dew = now.get('dew', '无法获取露点温度')
                fx_link = data.get('fxLink', '无法获取详情链接')

                return temp, feels_like, text, wind_dir, wind_scale, humidity, precip, pressure, vis, cloud, dew, fx_link
            else:
                error_msg = data.get('msg', '未知错误')
                print(f"API Error: {error_msg}")  # 调试：打印API错误信息
                return error_msg, '', '', '', '', '', '', '', '', '', '', ''
        else:
            print(f"API Request Failed with Status Code: {response.status_code}")
            print(f"API Error Response: {response.text}")
            return 'API请求失败', '', '', '', '', '', '', '', '', '', '', ''
    except requests.exceptions.RequestException as e:
        print(f"API Request Exception: {e}")
        return 'API请求失败', '', '', '', '', '', '', '', '', '', '', ''


def send_message():
    temperature, feels_like, weather_description, wind_direction, wind_scale, humidity, precip, pressure, vis, cloud, dew, fx_link = get_weather(
        qweather_api_key, location)

    timestamp = str(round(time.time() * 1000))  # 使用当前时间作为时间戳
    sign = generate_sign(secret, timestamp)

    complete_webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    # 判断现在是上午、下午还是晚上
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        period_of_day = "上午"
    elif 12 <= current_hour < 18:
        period_of_day = "下午"
    else:
        period_of_day = "晚上"

    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"当前天气 ({period_of_day})",
            "text": (
                f"### 当前天气 ({period_of_day})\n"
                f"- **城市:** 北京\n"
                f"- **温度:** {temperature}°C\n"
                f"- **体感温度:** {feels_like}°C\n"
                f"- **天气:** {weather_description}\n"
                f"- **风向:** {wind_direction}\n"
                f"- **风力等级:** {wind_scale}\n"
                f"- **湿度:** {humidity}%\n"
                f"- **降水量:** {precip}mm\n"
                f"- **气压:** {pressure}hPa\n"
                f"- **能见度:** {vis}km\n"
                f"- **云量:** {cloud}%\n"
                f"- **露点温度:** {dew}°C\n"
                f"- **详情:** [{fx_link}]({fx_link})"
            )
        }
    }

    print("Sending message to DingTalk:")
    print(json.dumps(message, indent=4, ensure_ascii=False))  # 打印要发送的消息内容

    try:
        response = requests.post(
            complete_webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(message)
        )
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        print("消息发送成功")
        print("DingTalk API Response:", response.json())  # 打印钉钉API的响应内容
    except requests.exceptions.RequestException as e:
        print(f"消息发送失败: {e}")
        print(f"服务器响应: {response.text if 'response' in locals() else '无响应'}")


if __name__ == "__main__":
    send_message()
