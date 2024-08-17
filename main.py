# -*- coding: utf-8 -*-
import requests
import os
import time
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter


def scrape_momo(keyword):
    url = f"https://m.momoshop.com.tw/search.momo?searchKeyword={keyword}"
    headers = {"User-Agent": UserAgent().chrome}

    while True:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            time.sleep(5)  # 遇到錯誤後等待5秒再重試


def momopro_url(driver, product_id, keyword):
    url = f"https://m.momoshop.com.tw/goods.momo?i_code={product_id}&mdiv=searchEngine&oid=1_3&kw={keyword}"
    driver.get(url)
    return driver.page_source


def momoComment(driver, product_id):
    url = f"https://m.momoshop.com.tw/goodsComment.momo?i_code={product_id}&goodsCanReviews=1&isSwitchGoodsReviews=1&isSwitchGoodsTotalSales=1&isSwitchGoodsComment=1"
    driver.get(url)
    return driver.page_source


def main():
    WORDS_PATH = "./font/dict.txt.big.txt"  # 繁體中文詞庫檔名
    font_path = os.path.join("font", "NotoSansTC-VariableFont_wght.otf")
    if not os.path.isfile(font_path):
        raise FileNotFoundError(f"字體檔案未找到：{font_path}")

    # 先設置字典
    jieba.set_dictionary(WORDS_PATH)

    keyword = input("請輸入想要搜尋的商品:")
    html_content = scrape_momo(keyword)
    soup = BeautifulSoup(html_content, "lxml")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    product_items = soup.select(".goodsItemLi.goodsItemLiSeo")
    Compath = "商品評論連結.txt"

    with open(Compath, "a", encoding="utf-8") as f:
        for item in product_items:
            product_name = item.select_one(".prdName").text.strip()
            product_id = (
                item.select_one("a input")["value"]
                if item.select_one("a input")
                else "N/A"
            )

            f.write(f"商品名稱:{product_name}\n")
            f.write(
                f"商品url:https://m.momoshop.com.tw/goods.momo?i_code={product_id}&mdiv=searchEngine&oid=1_3&kw={keyword}\n"
            )
            if product_id != "N/A":
                try:
                    html_content02 = momopro_url(driver, product_id, keyword)
                    soup02 = BeautifulSoup(html_content02, "lxml")
                    Comment = soup02.select(".productRatingTitle")
                    if Comment and Comment[0].text.strip() != "尚無商品評價":
                        html_content01 = momoComment(driver, product_id)
                        soup01 = BeautifulSoup(html_content01, "lxml")
                        Comment_items = soup01.select(".Comment")
                        comments_text = " ".join(
                            [item.text.strip() for item in Comment_items]
                        )

                        word_list = jieba.cut(comments_text, cut_all=False)
                        dictionary = Counter(word_list)
                        STOP_WORDS = [
                            " ",
                            "，",
                            "(",
                            ")",
                            "...",
                            "。",
                            "「",
                            "」",
                            "[",
                            "]",
                        ]
                        dictionary = {
                            k: v for k, v in dictionary.items() if k not in STOP_WORDS
                        }

                        if dictionary:
                            wc = WordCloud(
                                width=800,
                                height=400,
                                background_color="white",
                                font_path=font_path,  # 使用自定義字體
                            ).generate_from_frequencies(dictionary)
                            os.makedirs("data", exist_ok=True)  # 確保資料夾存在
                            image_path = os.path.join(
                                "data", f"wordcloud_{product_id}.png"
                            )
                            plt.figure(figsize=(10, 5))
                            plt.imshow(wc, interpolation="bilinear")
                            plt.axis("off")
                            plt.savefig(image_path)
                            plt.close()
                            f.write(f"文字雲圖片已保存到: {image_path}\n")
                        else:
                            f.write(f"評論不足以生成文字雲。\n")
                    else:
                        f.write("尚無評價\n")
                except Exception as e:
                    f.write(f"抓取評論或生成文字雲時出錯: {e}\n")
            else:
                f.write("無法抓取商品 ID\n")

            f.write("---\n")

    driver.quit()


if __name__ == "__main__":
    main()
