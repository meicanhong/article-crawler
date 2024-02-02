# ArticleCrawler

ArticleCrawler is a scalable, automated crawler designed to extract and parse articles from websites. It uses the Playwright library for web scraping, BeautifulSoup for HTML parsing, and stores data in a MongoDB collection.

## Features

- Multithreaded crawling with customizable concurrency level.
- Configurable maximum number of pages to crawl.
- Configurable request timeout.
- Option to only crawl pages from the same domain as the start URL.
- Ability to include or exclude URLs based on regex patterns.
- Configurable maximum recursion depth for the crawler.
- Configurable minimum length of a URL to be considered for crawling.
- Stores raw HTML data and parse data in a MongoDB collection.

## Dependencies

- Python
- Playwright
- BeautifulSoup
- courlan
- MongoDB

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright

```bash 
playwright install
```

### 3. Start MongoDB

```bash
docker-compose up -d
```

### 4. Run the Crawler

```python
from article_crawler import ArticleCrawler

url = 'https://followin.io/en'
crawler = ArticleCrawler(start_url=url, max_pages=5)
crawler.run()
```
In the above example, the crawler starts from the URL 'https://followin.io/en' and crawls a maximum of 5 pages. 

## Configuration

The `ArticleCrawler` class constructor takes the following arguments:

- `start_url` (str): The starting URL for the crawler.
- `max_pages` (int, optional): The maximum number of pages to crawl. Defaults to 1.
- `request_timeout` (int, optional): The maximum time to wait for a page to load, in seconds. Defaults to 60.
- `concurrency` (int, optional): The number of concurrent threads to use for crawling. Defaults to 1.
- `crypto_only_same_domain` (bool, optional): If True, only crawl pages from the same domain as the start_url. Defaults to False.
- `include_urls` (str, optional): A regex pattern of URLs to include in the crawl. Defaults to None.
- `exclude_urls` (str, optional): A regex pattern of URLs to exclude from the crawl. Defaults to None.
- `max_recursion_depth` (int, optional): The maximum depth of recursion for the crawler. Defaults to 2.
- `url_min_length` (int, optional): The minimum length of a URL to be considered for crawling. Defaults to 15.

## Example
### Clip Medium Article
```python
from article_crawler import ArticleCrawler

if __name__ == '__main__':
    url = 'https://doctorow.medium.com/three-ai-insights-for-hard-charging-future-oriented-smartypantses-3d97b2486b6e'
    crawler = ArticleCrawler(start_url=url, max_pages=1)
    crawler.run()
```
after crawling the article, the data will be stored in the MongoDB crawler_extract_data collection, like this
```json
{
	"_id" : ObjectId("65bd0d4223d242c621264e0c"),
	"website_url" : "https://doctorow.medium.com/three-ai-insights-for-hard-charging-future-oriented-smartypantses-3d97b2486b6e",
	"author" : "Cory",
	"contents" : [
		{
			"type" : "text",
			"content" : "Three AI insights for hard charging, future oriented smartypantses\nA little bit of nonsensewatching for a Wednesday.\n![A science fiction pulp illustration of a man with a swollen, bald head that has been cut away to reveal its contents. The man’s face has been cropped at the bridge of his nose, leaving just the swollen, hollow head, cheekbones, and staring eyes, the last of which have been covered with blue ovals. The hollow head has been filled with the trudging figures from Van Gogh’s ‘The Prisoners,’ marching over a grid of vacuum tubes from an early computer. The background of the image is the wiring from an](https://miro.medium.com/v2/resize:fit:700/1*bE7s_YlfYx1xn3TWeENnwA.jpeg)\nMERE HOURS REMAIN for the Kickstarter for the audiobook for The Bezzle, the sequel to Red Team Blues, narrated by\nLiving in the age of AI hype makes demands on all of us to come up with smartypants prognostications about how AI is about to change everything forever, and wow, it’s pretty amazing, huh?\nAI pitchmen don’t make it easy. They like to pile on the cognitive dissonance and demand that we all somehow resolve it. This is a thing cult leaders do, too — tell blatant and obvious lies to their followers. When a cult follower repeats the lie to others, they are demonstrating their loyalty, both to the leader and to themselves.\nOver and over, the claims of AI pitchmen turn out to be blatant lies. This has been the case since at least the age of the Mechanical Turk, the 18th chess playing automaton that was actually just a chess player crammed into the base of an elaborate puppet that was exhibited as an autonomous, intelligent robot.\nThe most prominent Mechanical Turk huckster is Elon Musk, who habitually, blatantly and repeatedly lies about AI. He’s been promising “full self driving” Telsas in “one to two years” for more than a decade. Periodically, he’ll “demonstrate” a car that’s in full self driving mode — which then turns out to be canned, recorded demo:\nhttps://www.reuters.com/technology/tesla video promoting self driving was staged engineer testifies 2023 01 17/\nMusk even trotted an autonomous, humanoid robot on stage at an investor presentation, failing to mention that this mechanical marvel was just a person in a robot suit:\nhttps://www.siliconrepublic.com/machines/elon musk tesla robot optimus ai\nNow, Musk has announced that his junk science neural interface company, Neuralink, has made the leap to implanting neural interface chips in a human brain. As Joan Westenberg writes, the press have repeated this claim as presumptively true, despite its wild implausibility:\nhttps://joanwestenberg.com/blog/elon musk lies\nNeuralink, after all, is a company notorious for mutilating primates in pursuit of showy, meaningless demos:\nhttps://www.wired.com/story/elon musk pcrm neuralink monkey deaths/\nI’m perfectly willing to believe that Musk would risk someone else’s life to help him with this nonsense, because he doesn’t see other people as real and deserving of compassion or empathy. But he’s also profoundly lazy and is accustomed to a world that unquestioningly swallows his most outlandish pronouncements, so Occam’s Razor dictates that the most likely explanation here is that he just made it up.\nThe odds that there’s a human being beta testing Musk’s neural interface with the only brain they will ever have aren’t zero. But I give it the same odds as the Raelians’ claim to have cloned a human being:\nhttps://edition.cnn.com/2003/ALLPOLITICS/01/03/cf.opinion.rael/\nThe human in a robot suit gambit is everywhere in AI hype. Cruise, GM’s disgraced “robot taxi” company, had 1.5 remote operators for every one of the cars on the road. They used AI to replace a single, low waged driver with 1.5 high waged, specialized technicians. Truly, it was a marvel.\nGlobalization is key to maintaining the guy in a robot suit phenomenon. Globalization gives AI pitchmen access to millions of low waged workers who can pretend to be software programs, allowing us to pretend to have transcended the capitalism’s exploitation trap. This is also a very old pattern — just a couple decades after the Mechanical Turk toured Europe, Thomas Jefferson returned from the continent with the dumbwaiter. Jefferson refined and installed these marvels, announcing to his dinner guests that they allowed him to replace his “servants” (that is, his slaves). Dumbwaiters don’t replace slaves, of course — they just keep them out of sight:\nhttps://www.stuartmcmillen.com/blog/behind the dumbwaiter/\nSo much AI turns out to be low waged people in a call center in the Global South pretending to be robots that Indian techies have a joke about it: “AI stands for ‘absent Indian’”:\nhttps://pluralistic.net/2024/01/29/pay no attention/#to the little man behind the curtain\nA reader wrote to me this week. They’re a multi decade veteran of Amazon who had a fascinating tale about the launch of Amazon Go, the “fully automated” Amazon retail outlets that let you wander around, pick up goods and walk out again, while AI enabled cameras totted up the goods in your basket and charged your card for them.\nAccording to this reader, the AI cameras didn’t work any better than Tesla’s full self driving mode, and had to be backstopped by a minimum of three camera operators in an Indian call center, “so that there could be a quorum system for deciding on a customer’s activity — three autopilots good, two autopilots bad.”\nAmazon got a ton of press from the launch of the Amazon Go stores. A lot of it was very favorable, of course: Mister Market is insatiably horny for firing human beings and replacing them with robots, so any announcement that you’ve got a human replacing robot is a surefire way to make Line Go Up. But there was also plenty of critical press about this — pieces that took Amazon to task for replacing human beings with robots.\nWhat was missing from the criticism? Articles that said that Amazon was probably lying about its robots, that it had replaced low waged clerks in the USA with even lower waged camera jockeys in India.\nWhich is a shame, because that criticism would have hit Amazon where it hurts, right there in the ole Line Go Up. Amazon’s stock price boost off the back of the Amazon Go announcements represented the market’s bet that Amazon would evert out of cyberspace and fill all of our physical retail corridors with monopolistic robot stores, moated with IP that prevented other retailers from similarly slashing their wage bills. That unbridgeable moat would guarantee Amazon generations of monopoly rents, which it would share with any shareholders who piled into the stock at that moment.\nSee the difference? Criticize Amazon for its devastatingly effective automation and you help Amazon sell stock to suckers, which makes Amazon executives richer. Criticize Amazon for lying about its automation, and you clobber the personal net worth of the executives who spun up this lie, because their portfolios are full of Amazon stock:\nhttps://sts news.medium.com/youre doing it wrong notes on criticism and technology hype 18b08b4307e5\nAmazon Go didn’t go. The hundreds of Amazon Go stores we were promised never materialized. There’s an embarrassing rump of 25 of these things still around, which will doubtless be quietly shuttered in the years to come. But Amazon Go wasn’t a failure. It allowed its architects to pocket massive capital gains on the way to building generational wealth and establishing a new permanent aristocracy of habitual bullshitters dressed up as high tech wizards.\n“Wizard” is the right word for it. The high tech sector pretends to be science fiction, but it’s usually fantasy. For a generation, America’s largest tech firms peddled the dream of imminently establishing colonies on distant worlds or even traveling to other solar systems, something that is still so far in our future that it might well never come to pass:\nhttps://pluralistic.net/2024/01/09/astrobezzle/#send robots instead\nDuring the Space Age, we got the same kind of performative bullshit. On The Well David Gans mentioned hearing a promo on SiriusXM for a radio show with “the first AI co host.” To this, Craig L Maudlin replied, “Reminds me of fins on automobiles.”\nYup, that’s exactly it. An AI radio co host is to artificial intelligence as a Cadillac Eldorado Biaritz tail fin is to interstellar rocketry.\nIf you’d like an essay formatted version of this post to read or share, here’s a link to it on pluralistic.net, my surveillance free, ad free, tracker free blog:\nhttps://pluralistic.net/2024/01/31/neural interface beta tester/#tailfins"
		}
	],
	"created_at" : ISODate("2024-02-02T23:41:54.009+08:00"),
	"description" : "A little bit of nonsensewatching for a Wednesday.",
	"headline" : "Three AI insights for hard-charging, future-oriented smartypantses",
	"language" : null,
	"name" : null,
	"published_at" : ISODate("2024-01-31T08:00:00.000+08:00"),
	"related" : [ ],
	"source" : null,
	"subheadline" : "",
	"subtype" : null,
	"tags" : [ ],
	"updated_at" : ISODate("2024-02-02T23:41:54.009+08:00"),
	"website" : "doctorow.medium.com"
}
```