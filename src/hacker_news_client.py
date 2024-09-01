import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from logger import LOG
import json
import html2text
import pdfplumber
import io

class HackerNewsClient:
    def __init__(self):
        self.url = url = 'https://news.ycombinator.com/'
        self.json_data = {
            "title": "Hacker News Top Stories",
            "stories": []
        }
        with open("prompts/hackernews_prompt.txt", "r", encoding='utf-8') as file:
            self.system_prompt = file.read()

    def fetch_hackernews_top_stories(self):
        response = requests.get(self.url)
        response.raise_for_status()  # 检查请求是否成功

        soup = BeautifulSoup(response.text, 'html.parser')
        # 查找包含新闻的所有 <tr> 标签
        stories = soup.find_all('tr', class_='athing')

        top_stories = []
        for story in stories:
            title_tag = story.find('span', class_='titleline').find('a')
            if title_tag:
                title = title_tag.text
                link = title_tag['href']
                top_stories.append({'title': title, 'link': link})

        return top_stories

    def export_hacker_news(self):
        LOG.debug(f"準備導出Hacker News熱點新聞")
        today = datetime.now().date().isoformat()  # 获取今天的日期
        stories = self.fetch_hackernews_top_stories() # 获取今天的更新数据
        
        repo_dir = os.path.join('daily_progress/hacker_news')  # 构建存储路径
        os.makedirs(repo_dir, exist_ok=True)  # 确保目录存在
        
        file_path = os.path.join(repo_dir, f'{today}.md')  # 构建文件路径
        print(f"Path to news file:" + file_path)

        with open(file_path, 'w') as file:
            file.write("# Hacker News Top Stories:\n")
            for idx, story in enumerate(stories, start=1):
                LOG.debug(f"\n{idx}. {story['title']}\n{story['link']}")
                file.write(f"## {idx}. {story['title']}\n")
                news_url = story['link']
                if "http" not in news_url:
                    news_url = self.url + news_url
                response = requests.get(news_url)
                # Check if the request was successful
                if response.status_code == 200:
                    # Get the content type of the response
                    content_type = response.headers.get('Content-Type')
                    if 'application/pdf' in content_type:
                        # The content is a PDF file
                        pdf_content = response.content

                        # Extract text from the PDF
                        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                            content_str = ""
                            for page in pdf.pages:
                                content_str += page.extract_text()
                        
                        LOG.debug(f"Extracted Text from PDF:\n")

                    elif 'text/html' in content_type:
                        # If you want to decode it as a string
                        converter = html2text.HTML2Text()
                        content_str = converter.handle(response.text)
                    elif 'text/plain' in content_type:
                        # The content is plain text
                        content_str = response.text

                    elif 'application/json' in content_type:
                        # The content is JSON
                        content_str = response.json()
                        LOG.debug(f"Received JSON Data: {content_str}")

                    else:
                        print(f"Received content type: {content_type}. Not handled by this script.")

                else:
                    content_str = f"Failed to retrieve content. Status code: {response.status_code}"                
                file.write(f"### {content_str}\n")
        LOG.info(f"Hacker News每日熱點新聞文件生成： {file_path}")  # 记录日志
        return file_path


if __name__ == "__main__":
    hackernew_client = HackerNewsClient()
    news_file = hackernew_client.export_hacker_news()
