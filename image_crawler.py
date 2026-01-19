#!/usr/bin/env python3
"""
色弱测试图片爬虫
从 seruoxiangji.com 抓取色弱测试图片和答案
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.seruoxiangji.com"

# 要抓取的页面列表
PAGES = [
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=1", "name": "yuziping6"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=4", "name": "yuziping5"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=5", "name": "set_id5"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=6", "name": "set_id6"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=7", "name": "set_id7"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=8", "name": "set_id8"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=9", "name": "set_id9"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=10", "name": "set_id10"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=11", "name": "set_id11"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=12", "name": "set_id12"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=13", "name": "set_id13"},
    {"url": "index.php?g=Home&m=Index&a=pinfo&id=14", "name": "set_id14"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": BASE_URL,
}


def fetch_page(url):
    """获取页面内容"""
    full_url = urljoin(BASE_URL, url)
    print(f"正在获取页面: {full_url}")
    
    response = requests.get(full_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = 'utf-8'
    return response.text


def parse_images_and_answers(html_content):
    """
    解析页面中的图片和答案
    返回: [(图片URL, 答案), ...]
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # 查找所有图片容器
    # 页面结构: 图片后面跟着答案文字
    content_div = soup.find('div', class_='content') or soup.find('div', class_='article')
    
    if not content_div:
        # 尝试查找主体内容
        content_div = soup.find('body')
    
    # 查找所有图片
    images = soup.find_all('img')
    
    for img in images:
        src = img.get('src', '')
        if not src or 'book' not in src:
            continue
        
        # 构建完整URL
        if src.startswith('/'):
            img_url = BASE_URL + src
        elif not src.startswith('http'):
            img_url = BASE_URL + '/' + src
        else:
            img_url = src
        
        # 尝试获取答案 - 查找图片后面的文字
        answer = ""
        
        # 方法1: 查找同级或父级的文字
        parent = img.parent
        if parent:
            # 获取父元素的文本
            text = parent.get_text(strip=True)
            # 提取答案 (通常格式为 "答案：XXX" 或直接是数字/文字)
            answer_match = re.search(r'答案[：:]\s*([^\s<]+)', text)
            if answer_match:
                answer = answer_match.group(1)
            else:
                # 尝试提取纯数字或简短文字
                next_sibling = img.next_sibling
                if next_sibling:
                    sibling_text = str(next_sibling).strip()
                    if sibling_text and len(sibling_text) < 20:
                        answer = sibling_text
        
        results.append({
            'url': img_url,
            'answer': answer
        })
    
    return results


def download_image(url, save_path):
    """下载图片"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"下载失败 {url}: {e}")
        return False


def crawl_all(output_dir):
    """
    抓取所有页面的图片
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_data = {}
    
    for page_info in PAGES:
        page_name = page_info['name']
        page_dir = output_dir / page_name
        page_dir.mkdir(exist_ok=True)
        
        print(f"\n=== 正在处理: {page_name} ===")
        
        try:
            html = fetch_page(page_info['url'])
            items = parse_images_and_answers(html)
            
            page_data = []
            
            for i, item in enumerate(items, 1):
                img_url = item['url']
                answer = item['answer']
                
                # 生成文件名
                ext = Path(img_url).suffix or '.jpg'
                filename = f"{i:03d}{ext}"
                save_path = page_dir / filename
                
                print(f"  下载 {i}/{len(items)}: {img_url}")
                
                if download_image(img_url, save_path):
                    page_data.append({
                        'filename': filename,
                        'original_url': img_url,
                        'answer': answer
                    })
                
                # 礼貌延迟
                time.sleep(0.5)
            
            all_data[page_name] = page_data
            
            # 保存该页面的答案
            answers_file = page_dir / 'answers.json'
            with open(answers_file, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False, indent=2)
            
            print(f"  已保存 {len(page_data)} 张图片到 {page_dir}")
            
        except Exception as e:
            print(f"处理页面 {page_name} 出错: {e}")
    
    # 保存总索引
    index_file = output_dir / 'index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成! 索引已保存到 {index_file}")
    return all_data


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="色弱测试图片爬虫")
    parser.add_argument(
        "-o", "--output",
        default="./downloaded_images",
        help="输出目录 (默认: ./downloaded_images)"
    )
    
    args = parser.parse_args()
    
    print("色弱测试图片爬虫")
    print("=" * 40)
    print(f"输出目录: {args.output}")
    print("注意: 请确保您有权使用下载的图片")
    print("=" * 40)
    
    crawl_all(args.output)


if __name__ == "__main__":
    main()
