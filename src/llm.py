import os
import json
from openai import OpenAI  # 导入OpenAI库用于访问GPT模型
from logger import LOG  # 导入日志模块
import openai
import tiktoken

class LLM:
    def __init__(self):
        # 创建一个OpenAI客户端实例
        self.client = OpenAI()
        # 从TXT文件加载提示信息
        with open("prompts/report_prompt.txt", "r", encoding='utf-8') as file:
            self.system_prompt = file.read()
        max_tpm = 200000

    def generate_daily_report(self, markdown_content, dry_run=False):
        # 使用从TXT文件加载的提示信息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": markdown_content},
        ]

        if dry_run:
            # 如果启用了dry_run模式，将不会调用模型，而是将提示信息保存到文件中
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/prompt.txt", "w+") as f:
                # 格式化JSON字符串的保存
                json.dump(messages, f, indent=4, ensure_ascii=False)
            LOG.debug("Prompt已保存到 daily_progress/prompt.txt")

            return "DRY RUN"

        # 日志记录开始生成报告
        LOG.info("使用 GPT 模型开始生成报告。")
        
        try:
            # 调用OpenAI GPT模型生成报告
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 指定使用的模型版本
                messages=messages
            )
            LOG.debug("GPT response: {}", response)
            # 返回模型生成的内容
            return response.choices[0].message.content
        except Exception as e:
            # 如果在请求过程中出现异常，记录错误并抛出
            LOG.error(f"生成报告时发生错误：{e}")
            raise

    def split_text_by_tokens(self, text, max_tokens=100000, model="gpt-4o-mini"): # Max tokens per call for ChatGPT-4o
        # 初始化 tiktoken 的編碼器
        encoding = tiktoken.encoding_for_model(model)
        sentences = text.split('. ')
        segments = []
        current_segment = []
        current_tokens = 0

        for sentence in sentences:
            token_count = len(encoding.encode(sentence))
            if current_tokens + token_count > max_tokens:
                segments.append('. '.join(current_segment) + '.')
                current_segment = [sentence]
                LOG.debug(f"Token count of this segment: {current_tokens}")
                current_tokens = token_count
            else:
                current_segment.append(sentence)
                current_tokens += token_count

        if current_segment:
            segments.append('. '.join(current_segment) + '.')

        return segments

    def generate_report_by_prompt(self, markdown_content, prompt):
         # 日志记录开始生成报告
        LOG.info("使用 GPT 模型开始生成报告。")
        
        try:
            content_segments = self.split_text_by_tokens(markdown_content)
            results = []
            total_segments = len(content_segments)
            # 调用OpenAI GPT模型生成报告
            for i, segment in enumerate(content_segments):
                LOG.debug(f"Shot {i+1}\n")                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"This is part {i + 1} of {total_segments} of a larger document. Please continue processing this text.\n\n{segment}"}
                    ]
                )
                results.append(response.choices[0].message.content)
            
            return " ".join(results)

        except Exception as e:
            # 如果在请求过程中出现异常，记录错误并抛出
            LOG.error(f"生成报告时发生错误：{e}")
            raise
