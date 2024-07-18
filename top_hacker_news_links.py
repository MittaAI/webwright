import requests

def get_top_hacker_news_links(limit=10):
    # API endpoint for top stories
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    story_url_template = "https://hacker-news.firebaseio.com/v0/item/{}.json"
    
    # Fetch top stories IDs
    top_stories_ids = requests.get(top_stories_url).json()
    
    top_stories_links = []
    for story_id in top_stories_ids[:limit]:
        # Fetch story details
        story_details = requests.get(story_url_template.format(story_id)).json()
        if 'url' in story_details:
            top_stories_links.append(story_details['url'])
    
    return top_stories_links

if __name__ == "__main__":
    links = get_top_hacker_news_links()
    for link in links:
        print(link)