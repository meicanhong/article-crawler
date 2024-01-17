from flask import Flask, jsonify, request

from article_crawler import ArticleCrawler

app = Flask(__name__)


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

    crawler = ArticleCrawler(url=url, max_sites=max_sites, max_links_per_page=max_links_per_page,
                             timeout=timeout, crawler_only_internal=crawler_only_internal)
    crawler.run()

    return jsonify({'message': 'Crawling initiated successfully'}), 200


if __name__ == '__main__':
    app.run(port=5000)
