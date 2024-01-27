import logging

from flask import Flask, jsonify, request

from article_crawler import ArticleCrawler

app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.get_json()

    if 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    url = data['url']
    max_sites = data.get('max_sites', 50)
    max_links_per_page = data.get('max_links_per_page', 10)
    timeout = data.get('timeout', 60)
    crawler_only_internal = data.get('crawler_only_internal', True)

    logging.info(f'Processing {url} with max_sites={max_sites}, max_links_per_page={max_links_per_page}, '
                     f'timeout={timeout}, crawler_only_internal={crawler_only_internal}')

    crawler = ArticleCrawler(start_url=url, max_pages=max_sites, max_links_per_page=max_links_per_page,
                             request_timeout=timeout, crypto_only_same_domain=crawler_only_internal)
    crawler.run()

    return jsonify({'message': 'Crawling initiated successfully'}), 200


if __name__ == '__main__':
    app.logger.setLevel(logging.INFO)
    app.run(host='0.0.0.0', port=5000)
