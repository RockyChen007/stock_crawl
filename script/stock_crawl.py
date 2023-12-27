import sys
import time
import urllib.request as url_request
from typing import Any
from urllib.request import urlopen

import pandas as pd
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

sina_stock_url = "https://hq.sinajs.cn/list="


# # =====直接通过网址获取数据
# import sys
# import requests
# url = 'https://27.push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.688052&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=0&end=20500101&lmt=120'
# r = requests.get(url).json()['data']['klines']
# l = [i.split(',') for i in r]
# df = pd.DataFrame(l)
# df = df[[0, 1, 2, 3, 4, 5, 6]]
# df.columns = ['交易日期', '开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额']
# print(df)
# sys.exit()
# # 该网址用法具体可以看目录里的神奇的网址图文攻略。

def get_stock_info_from_sina(url: str, max_retry_num: int = 10, sleep_time: int = 5):
    headers = {
        "Referer": "http://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62",
    }
    request = url_request.Request(url=url, headers=headers)
    print("Start fetching stock info...")
    for i in range(max_retry_num):
        print(f"Stock fetch count:{i + 1}")
        response = urlopen(request)
        if response.code == 200:
            print(f"[Successed] url:{url}")
            return response.read().decode("gbk")
        else:
            print(f"[Error] url:{url} response:{response}")
            time.sleep(sleep_time)


def assemble_url_param(stock_codes: list[str]) -> str:
    stock_code_list = []
    for code in stock_codes:
        if code.startswith("30") or code.startswith("00"):
            stock_code_list.append("sz" + code)
        else:
            stock_code_list.append("sh" + code)
    return ",".join(stock_code_list)


def handle_and_save_stock_info(content: Any):
    data_line = content.strip().split("\n")  # 去掉文本前后的空格、回车等。每行是一个股票的数据
    data_line = [i.replace("var hq_str_", "").split(",") for i in data_line]
    df = pd.DataFrame(data_line)
    # =====对DataFrame进行整理
    df[0] = df[0].str.split('="')
    df["stock_code"] = df[0].str[0].str.strip()
    df["stock_name"] = df[0].str[-1].str.strip()
    df["candle_end_time"] = pd.to_datetime(
        df[30] + " " + df[31]
    )  # 股票市场的K线，是普遍以当跟K线结束时间来命名的

    rename_dict = {
        1: "open",
        2: "pre_close",
        3: "close",
        4: "high",
        5: "low",
        6: "buy1",
        7: "sell1",
        8: "amount",
        9: "volume",
        32: "status",
    }  
    df.rename(columns=rename_dict, inplace=True)
    df["status"] = df["status"].str.strip('";')
    df = df[[
        "stock_code",
        "stock_name",
        "candle_end_time",
        "open",
        "high",
        "low",
        "close",
        "pre_close",
        "amount",
        "volume",
        "buy1",
        "sell1",
        "status",
    ]]
    print(df)

    
    df.to_csv(get_csv_save_path(), index=False)

def get_csv_save_path()->str:
    time_str = time.strftime("%Y-%m-%d %H:%M:%S")
    return f'../output/{time_str}_stock_data.csv'

def run_stock_crawl(stock_codes: list[str]) -> None:
    print(f"Input stock_codes:{stock_codes}")
    param = assemble_url_param(stock_codes=stock_codes)
    request_url = sina_stock_url + param
    stock_contents = get_stock_info_from_sina(url=request_url)
    handle_and_save_stock_info(content=stock_contents)
    print("[Fin]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"[Error] You must input at least one stock code")
    else:   
        run_stock_crawl(stock_codes=sys.argv[1:])
