# Article-Crawler
一个可批量化，规模化的文章类自动化爬虫，自动爬取网站内的文章内容，包括标题、作者、发布时间、正文等，保存到 Mongo。用于支撑 AI 项目的数据需求。

## 功能
- 利用Playwright库实现无头浏览器爬取网站文章，对网页进行滑动滚动条操作，等待元素加载
- 利用 newspaper3k/trafilatura/htmldate 等库实现网页正文提取、发布时间提取、作者提取，数据质量有保证
- 保存网页的原始数据和ETL后的数据
- 实现并发爬取，8c16g机器上可实现每分钟爬取50篇文章
- 实施反爬虫技术，如使用代理和添加隐身脚本（stealth.min.js）以防止检测。实测已通过 https://bot.sannysoft.com/ 检测
- 实现网状爬虫，自动将网页内的链接加入待爬取队列
- 实现有限深度爬虫，可设置爬取深度，避免无限爬取

## 快速开始
### 1. 安装依赖
```bash
pip install -r requirements.txt
```
### 2. 安装无头浏览器
```bash
playwright install
```
### 3. 运行
```bash
python article_crawler.py
```