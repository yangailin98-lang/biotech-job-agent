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
    """重点搜索外企医药大厂官网招聘页及主流招聘网站"""
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    all_jobs = []
    
    # ──────────────────────────────────────
    # 第一轮：直接搜外企大厂官网招聘页面（site:搜索）
    # ──────────────────────────────────────
    # 列出你关注的外企医药大厂
    big_pharma_sites = [
        "pfizer.com.cn",        # 辉瑞
        "roche.com.cn",         # 罗氏
        "novartis.com.cn",      # 诺华
        "astrazeneca.com.cn",   # 阿斯利康
        "msdchina.com.cn",      # 默沙东
        "bayer.com.cn",         # 拜耳
        "boehringer-ingelheim.cn", # 勃林格殷格翰
        "sanofi.cn",            # 赛诺菲
        "gsk-china.com",        # 葛兰素史克
        "lillychina.com",       # 礼来
        "abbvie.com.cn",        # 艾伯维
        "jnjchina.com.cn",      # 强生
        "novonordisk.com.cn",   # 诺和诺德
        "takeda.com.cn",        # 武田
        "bms.com.cn",           # 百时美施贵宝
    ]
    
    roles = ["商务拓展", "BD", "战略", "业务发展", "战略合作", 
             "business development", "strategy", "corporate strategy"]
    
    for site in big_pharma_sites:
        # 搜官网招聘页面的BD/战略岗
        query = f'site:{site} ("商务拓展" OR "BD" OR "战略" OR "business development") (招聘 OR 校招 OR 实习 OR careers OR jobs)'
        
        payload = {
            "q": query,
            "gl": "cn",
            "hl": "zh-cn",
            "num": 5
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            result_data = response.json()
            if "organic" in result_data:
                for r in result_data["organic"]:
                    link = r.get("link", "")
                    if link not in [j.get("link") for j in all_jobs]:
                        all_jobs.append({
                            "title": r.get("title", ""),
                            "link": link,
                            "snippet": r.get("snippet", ""),
                            "date": r.get("date", ""),
                            "source": "官网招聘页"
                        })
        except Exception as e:
            print(f"搜索 {site} 出错: {e}")
    
    # ──────────────────────────────────────
    # 第二轮：在主流招聘网站搜外企医药大厂
    # ──────────────────────────────────────
    # 猎聘、LinkedIn、前程无忧等站内搜索
    job_platforms = [
        "site:linkedin.com",
        "site:liepin.com",      # 猎聘
        "site:51job.com",       # 前程无忧
        "site:zhaopin.com",     # 智联招聘
    ]
    
    # 外企大厂名称（用于招聘网站搜）
    pharma_names = [
        "辉瑞", "罗氏", "诺华", "阿斯利康", "默沙东", "拜耳",
        "赛诺菲", "葛兰素史克", "礼来", "艾伯维", "强生",
        "诺和诺德", "武田", "百时美施贵宝", "安进", "吉利德",
        "辉瑞", "默克", "雅培", "丹纳赫", "赛默飞", "碧迪"
    ]
    
    cities = ["广州", "深圳", "香港", "上海", "北京", "杭州"]
    
    for platform in job_platforms:
        for company in pharma_names[:6]:  # 先搜6家控制额度，可去掉[:6]搜全部
            for city in cities[:3]:       # 先搜3个核心城市
                query = f'{platform} {company} {city} ("商务拓展" OR "BD" OR "战略" OR "业务发展")'
                
                payload = {
                    "q": query,
                    "gl": "cn",
                    "hl": "zh-cn",
                    "num": 5
                }
                try:
                    response = requests.post(url, headers=headers, json=payload)
                    result_data = response.json()
                    if "organic" in result_data:
                        for r in result_data["organic"]:
                            link = r.get("link", "")
                            if link not in [j.get("link") for j in all_jobs]:
                                all_jobs.append({
                                    "title": r.get("title", ""),
                                    "link": link,
                                    "snippet": r.get("snippet", ""),
                                    "date": r.get("date", ""),
                                    "source": "招聘平台"
                                })
                except Exception as e:
                    print(f"搜索 {platform} {company} {city} 出错: {e}")
    
    # ──────────────────────────────────────
    # 第三轮：通用补充搜索（中国区外企+BD）
    # ──────────────────────────────────────
    broad_queries = [
        '外资药企 商务拓展 BD 招聘 2026',
        '跨国药企 战略 校招 OR 实习 2026',
        'multinational pharma business development strategy China hiring 2026',
        '外企 生物医药 战略合作 招聘 截止时间',
    ]
    
    for query in broad_queries:
        payload = {
            "q": query,
            "gl": "cn",
            "hl": "zh-cn",
            "num": 10
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            result_data = response.json()
            if "organic" in result_data:
                for r in result_data["organic"]:
                    link = r.get("link", "")
                    if link not in [j.get("link") for j in all_jobs]:
                        all_jobs.append({
                            "title": r.get("title", ""),
                            "link": link,
                            "snippet": r.get("snippet", ""),
                            "date": r.get("date", ""),
                            "source": "综合搜索"
                        })
        except Exception as e:
            print(f"综合搜索出错: {e}")

    print(f"初步搜索到 {len(all_jobs)} 条不重复结果，等待DeepSeek精选...")
    return all_jobs[:50]
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

    prompt = f"""你是一个顶尖的生物医药行业招聘专家和猎头顾问。请根据下面提供的原始招聘信息，为我整理一份高度结构化、精准的招聘日报。

    **我的核心需求：**
    1.  **目标岗位：** 重点关注 **商务拓展 (BD)**、**战略合作/战略规划** 相关职位。
    2.  **目标城市：** 广州、深圳、香港、上海、北京、杭州。
    3.  **企业类型标记：** 必须根据公司名称和你的知识，推断并标记企业类型：
        - 🏢 **外企**（外资/合资，如辉瑞、罗氏、阿斯利康、默沙东等）
        - 🇨🇳 **国企/央企**（如国药、华润医药、中国医药集团等）
        - 🏠 **民企/上市公司**（如百济神州、药明康德、恒瑞、信达等）
        - 🔬 **初创/成长型公司**（知名度较低但信息中出现的新锐公司）
        - 🏛️ **事业单位/高校**（如科研院所、医院、大学）
    4.  **时间线抓取：** 
        - 如果在任何信息中发现了招聘开始/截止日期，请务必标注：📅 **投递时间：YYYY-MM-DD 至 YYYY-MM-DD**
        - 如果只提到"截止日期"，标注：📅 **截止日期：YYYY-MM-DD**
        - 如果完全没有时间信息，标注：📅 **投递时间：请点击链接查看详情**
    5.  **特殊标记：** 必须明确标注 **【校招】**、**【实习】** 或 **【全职/社招】**。
    6.  **信息入口：** 附上可直接点击的链接。

    **输出格式要求（请严格遵守）：**
    按城市分类，每个职位占据一个条目。如果某个城市没有相关职位，写"今日暂无"。

    ---
    ### 【城市名称】
    - **公司名称** 🏢企业类型 - 职位名称 **【校招/实习/全职】**
      > 一句话简介工作内容或核心要求。
      > 📅 投递时间：XXXX-XX-XX 至 XXXX-XX-XX（或"请点击链接查看详情"）
      > 👉 [点击查看/投递](职位链接)
    ---

    **示例（请严格模仿这个格式）：**

    ### 【上海】
    - **辉瑞制药** 🏢外企 - 肿瘤业务商务拓展经理 **【全职】**
      > 负责华东区域肿瘤创新药的license-in谈判及战略合作拓展，要求5年以上药企BD经验。
      > 📅 投递时间：请点击链接查看详情
      > 👉 [点击查看/投递](https://example.com/1)

    - **药明康德** 🏠民企/上市公司 - 战略分析实习生 **【实习】**
      > 协助行业研究及战略报告撰写，生物/药学背景优先，每周到岗3天以上。
      > 📅 截止日期：2026-08-15
      > 👉 [点击查看/投递](https://example.com/2)

    ### 【北京】
    - **国药集团** 🇨🇳国企/央企 - 校招-国际业务拓展专员 **【校招】**
      > 面向2026届硕士，负责海外市场商务拓展及政府事务协调，需海外经历。
      > 📅 投递时间：2026-07-01 至 2026-10-31
      > 👉 [点击查看/投递](https://example.com/3)

    ### 【杭州】
    今日暂无符合要求的职位。

    **原始招聘信息如下：**
    {job_list_text}
    
    **重要提醒：**
    - 请根据公司名称推断企业类型，这非常重要。如果不确定，标注 🏢类型待确认。
    - 仔细阅读摘要(snippet)中是否包含日期信息（如"7月15日截止"、"截止日期"等），并据此填写📅栏。
    - 只保留目标城市（广州/深圳/香港/上海/北京/杭州）且符合目标岗位（BD/战略相关）的信息。
    - 严格检查所有职位是否都准确标记了【校招】/【实习】/【全职】。
    - 去掉任何无关信息、广告、以及明显过时的招聘（如2025年之前的）。
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
    msg["Subject"] = f"[医药招聘] 今日生物医药招聘信息 ({date.today()})"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS   # 发给自己

    # 使用 Gmail SMTP 发送
    with smtplib.SMTP_SSL("smtp.163.com", 465) as server:
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
