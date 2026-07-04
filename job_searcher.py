import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import date
from openai import OpenAI

# 读取 GitHub Secrets 中的密钥
SERPER_API_KEY = os.environ["SERPER_API_KEY"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

def search_jobs():
    """用 Serper 搜索当天生物医药招聘信息"""
    url = "https://google.serper.dev/search"
    # 这里搜索中英文关键词，时间限制为过去一天
    query = "生物医药 招聘 after:2024-01-01"  # 后面动态加今天日期
    today = date.today().isoformat()
    full_query = f"生物医药 招聘 OR biotech hiring OR biopharma job after:{today}"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": full_query,
        "gl": "us",       # 可根据需要改为 cn
        "hl": "zh-cn",    # 中文结果为主
        "num": 10         # 返回前10个结果
    }

    response = requests.post(url, headers=headers, json=payload)
    result_data = response.json()
    # 只提取标题、链接、摘要
    if "organic" in result_data:
        items = []
        for r in result_data["organic"]:
            items.append({
                "title": r.get("title", ""),
                "link": r.get("link", ""),
                "snippet": r.get("snippet", "")
            })
        return items[:10]
    else:
        return []

def summarize_with_deepseek(jobs):
    """把招聘结果发给 DeepSeek，让它整理成易读摘要"""
    if not jobs:
        return "今天没有找到新的招聘信息。"

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )

    # 准备发送给模型的文本
    job_list_text = ""
    for idx, job in enumerate(jobs, 1):
        job_list_text += f"{idx}. {job['title']}\n   {job['link']}\n   {job['snippet']}\n\n"

    prompt = f"""你是一个专业的招聘信息整理助手。以下是今天从网上收集到的生物医药行业招聘相关信息，请用中文为我总结：
1. 按「公司/机构 - 职位」整理出清晰列表（每项一行）
2. 为每个职位生成一句简短介绍
3. 最后附上完整链接
4. 如果多条结果，尽量不要遗漏关键机会

招聘原始信息：
{job_list_text}
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个专业的生物医药招聘信息摘要助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1500
    )
    return response.choices[0].message.content

def send_email(content):
    """通过邮件发送整理好的信息"""
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"今日生物医药招聘信息 ({date.today()})"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS   # 发给自己

    # 使用 Gmail SMTP 发送
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, [EMAIL_ADDRESS], msg.as_string())
    print("邮件发送成功！")

def main():
    print("开始搜索今天的生物医药招聘信息...")
    jobs = search_jobs()
    print(f"搜索到 {len(jobs)} 条原始结果")
    summary = summarize_with_deepseek(jobs)
    print("摘要生成完毕，正在发送邮件...")
    send_email(summary)
    print("全部完成！")

if __name__ == "__main__":
    main()
