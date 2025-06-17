import time
import json
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LinkedInScraper:
    def __init__(
        self,
        email: str,
        password: str,
        headless: bool = False,
        window_size: tuple = (1200, 900),
        num_scrolls: int = 12,
        scroll_pause: float = 2.5,
        max_comments: int = 15
    ):
        """
        Initialize the LinkedIn Scraper with configuration parameters.
        
        Args:
            email (str): LinkedIn login email
            password (str): LinkedIn login password
            headless (bool): Whether to run browser in headless mode
            window_size (tuple): Browser window size (width, height)
            num_scrolls (int): Number of times to scroll the page
            scroll_pause (float): Time to pause between scrolls
            max_comments (int): Maximum number of comments to extract per post
        """
        self.email = email
        self.password = password
        self.num_scrolls = num_scrolls
        self.scroll_pause = scroll_pause
        self.max_comments = max_comments
        self.browser = None
        
        # Configure Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        self.chrome_options = chrome_options

    def login(self) -> bool:
        """
        Log in to LinkedIn.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            self.browser = webdriver.Chrome(options=self.chrome_options)
            self.browser.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            email_input = self.browser.find_element(By.ID, "username")
            password_input = self.browser.find_element(By.ID, "password")
            
            email_input.send_keys(self.email)
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)
            
            # Wait for login to complete
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def scrape_company_posts(self, company_url: str, auto_save: bool = True) -> Dict:
        """
        Scrape posts from a company's LinkedIn page.
        
        Args:
            company_url (str): URL of the company's LinkedIn posts page
            auto_save (bool): Whether to automatically save the results to a file
            
        Returns:
            Dict: Dictionary containing company name, timestamp, and posts data
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Please call login() first.")
            
        # Extract company name from URL
        company_name = company_url.split('/company/')[1].split('/')[0]
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize result dictionary
        result = {
            "company_name": company_name,
            "timestamp": timestamp,
            "source_url": company_url,
            "posts": []
        }
            
        self.browser.get(company_url)
        time.sleep(4)

        for _ in range(self.num_scrolls):
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.scroll_pause)

        post_elements = self.browser.find_elements(By.CSS_SELECTOR, 'div.feed-shared-update-v2')
        if not post_elements:
            post_elements = self.browser.find_elements(By.CSS_SELECTOR, 'div.feed-shared-update')

        print(f"\nFound {len(post_elements)} posts for {company_name}.\n")
        
        for idx, post in enumerate(post_elements, 1):
            post_data = self._extract_post_data(post, idx)
            result["posts"].append(post_data)

        # Auto-save if enabled
        if auto_save:
            filename = f"{company_name}_posts_{timestamp}.json"
            self.save_posts(result, filename)
            
        return result

    def _extract_post_data(self, post, idx: int) -> Dict:
        """Helper method to extract data from a single post."""
        post_data = {}
        
        # Extract post text
        try:
            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", post)
            time.sleep(1)
            try:
                more_button = WebDriverWait(post, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button.feed-shared-inline-show-more-text__see-more-less-toggle'))
                )
                self.browser.execute_script("arguments[0].click();", more_button)
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                pass

            content_elem = post.find_element(By.CSS_SELECTOR, 'span.break-words, div.feed-shared-update-v2__description')
            post_data['post_text'] = content_elem.text.strip()
        except NoSuchElementException:
            post_data['post_text'] = "[Could not extract post content]"

        # Extract likes
        try:
            likes_elem = post.find_element(By.CSS_SELECTOR, 'span.social-details-social-counts__reactions-count')
            post_data['likes'] = likes_elem.text.strip()
        except NoSuchElementException:
            post_data['likes'] = "0"

        post_data['comments'] = "0"
        post_data['shares'] = "0"

        # Extract social counts
        try:
            dynamic_spans = post.find_elements(By.XPATH, './/span[@aria-hidden="true"]')
            for span in dynamic_spans:
                text = span.text.strip().lower()
                if "comment" in text:
                    post_data['comments'] = ''.join(filter(str.isdigit, text)) or "0"
                elif "share" in text or "repost" in text:
                    post_data['shares'] = ''.join(filter(str.isdigit, text)) or "0"
        except Exception as e:
            print(f"Error extracting dynamic social counts: {e}")

        # Extract media
        post_data['image_urls'] = self._extract_media_urls(post, 'img', ['feed-shared-image__image', 'feed-shared-image__img'])
        post_data['video_urls'] = self._extract_media_urls(post, 'video', ['feed-shared-video__video', 'feed-shared-video__player'])
        
        # Extract comments
        post_data['top_comments'] = self._extract_comments(post)

        self._print_post_summary(post_data, idx)
        return post_data

    def _extract_media_urls(self, post, element_type: str, class_names: List[str]) -> List[str]:
        """Helper method to extract media URLs."""
        urls = []
        try:
            for class_name in class_names:
                elements = post.find_elements(By.CSS_SELECTOR, f'{element_type}.{class_name}')
                for element in elements:
                    src = element.get_attribute('src')
                    if src and not src.endswith('data:image/gif;base64'):
                        urls.append(src)
        except NoSuchElementException:
            pass
        return urls

    def _extract_comments(self, post) -> List[Dict]:
        """Helper method to extract comments from a post."""
        try:
            comments_button = post.find_element(By.XPATH, './/button[contains(@aria-label, "comments")]')
            self.browser.execute_script("arguments[0].click();", comments_button)
            time.sleep(2)

            while True:
                try:
                    load_more = post.find_element(By.XPATH, './/button[contains(@class, "load-more-comments-button")]')
                    self.browser.execute_script("arguments[0].click();", load_more)
                    time.sleep(1)
                except NoSuchElementException:
                    break

            comment_blocks = post.find_elements(By.XPATH, './/div[contains(@class, "comments-comment-item")]')[:self.max_comments]
            extracted_comments = []
            
            for comment in comment_blocks:
                try:
                    comment_text = comment.find_element(By.CSS_SELECTOR, 'span.comments-comment-item__main-content').text.strip()
                    try:
                        like_span = comment.find_element(By.CSS_SELECTOR, 'button.comments-comment-social-bar__reactions-count span')
                        like_count = like_span.text.strip()
                    except NoSuchElementException:
                        like_count = "0"
                    extracted_comments.append({
                        'comment_text': comment_text,
                        'likes': like_count
                    })
                except NoSuchElementException:
                    continue
            return extracted_comments
        except NoSuchElementException:
            return []

    def _print_post_summary(self, post_data: Dict, idx: int):
        """Helper method to print post summary."""
        print(f"\nPost {idx} Details:")
        print(f"Text: {post_data['post_text'][:100]}...")
        print(f"Likes: {post_data['likes']}")
        print(f"Comments: {post_data['comments']}")
        print(f"Shares: {post_data['shares']}")
        print(f"Images: {len(post_data['image_urls'])}")
        print(f"Videos: {len(post_data['video_urls'])}")
        print(f"Top Comments: {len(post_data['top_comments'])}")
        print('-'*40)

    def save_posts(self, data: Dict, filename: str):
        """
        Save scraped posts to a JSON file.
        
        Args:
            data (Dict): Data to save
            filename (str): Name of the file to save to
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}.")

    def close(self):
        """Close the browser."""
        if self.browser:
            self.browser.quit()
            self.browser = None

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "email": "your_email@example.com",
        "password": "your_password",
        "headless": False,
        "window_size": (1200, 900),
        "num_scrolls": 12,
        "scroll_pause": 2.5,
        "max_comments": 15
    }
    
    company_url = "https://www.linkedin.com/company/company-name/posts/"
    
    scraper = LinkedInScraper(**config)
    
    try:
        # Login to LinkedIn
        if scraper.login():
            # Scrape posts from a company
            result = scraper.scrape_company_posts(company_url, auto_save=True)
            
            # The result contains:
            # - company_name: extracted from URL
            # - timestamp: when the scraping was done
            # - source_url: the original URL
            # - posts: list of all scraped posts
            
            # You can access the data like this:
            print(f"Scraped {len(result['posts'])} posts from {result['company_name']}")
            print(f"Data was saved to: {result['company_name']}_posts_{result['timestamp']}.json")
            
            # You can also process the posts data
            for post in result['posts']:
                # Process each post as needed
                pass
            
    except Exception as e:
        print(f"\n[Error] {e}")
    finally:
        # Always close the browser
        scraper.close()
