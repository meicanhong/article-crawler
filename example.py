from article_crawler import ArticleCrawler

if __name__ == '__main__':
    url = 'https://defillama.com/yields'
    crawler = ArticleCrawler(start_url=url, max_pages=1)
    crawler.run()