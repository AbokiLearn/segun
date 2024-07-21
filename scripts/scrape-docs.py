from bs4 import BeautifulSoup
from tqdm import tqdm
import httpx
import logfire

from urllib.parse import urljoin, urlparse
from typing import Set, Tuple, List
from pathlib import Path
import time
import os

data_path = Path("/mnt/arrakis/AbokiLearn/aboki-segun/data/raw")
logfire.configure(token=os.getenv("LOGFIRE_TOKEN", ""), console=False)


class RateLimiter:
    def __init__(self, rate_limit: int):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.updated_at = time.time()

    def acquire(self):
        now = time.time()
        time_passed = now - self.updated_at
        self.tokens += time_passed * (self.rate_limit / 60)
        if self.tokens > self.rate_limit:
            self.tokens = self.rate_limit
        self.updated_at = now

        if self.tokens < 1:
            wait_time = (1 - self.tokens) / (self.rate_limit / 60)
            time.sleep(wait_time)
            return self.acquire()
        else:
            self.tokens -= 1
            return True


def extract_links(client: httpx.Client, base_url: str, doc_url: str) -> Set[str]:
    response = client.get(doc_url)
    time.sleep(1)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(doc_url, href)  # Use doc_url instead of base_url
            if full_url.startswith(base_url):
                links.add(full_url)
        return links
    return set()


def fetch_markdown(
    client: httpx.Client,
    url: str,
    output_dir: Path,
    rate_limiter: RateLimiter,
    visited: Set[str],
    max_retries: int = 3,
) -> Tuple[str, str]:
    if url in visited:
        return url, "already visited"

    visited.add(url)
    for attempt in range(max_retries):
        rate_limiter.acquire()
        jina_url = f"https://r.jina.ai/{url}"
        try:
            response = client.get(
                jina_url,
                headers={"Authorization": f"Bearer {os.environ['JINAAI_API_KEY']}"},
            )
            if response.status_code == 200:
                content = response.text
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path) or "index.md"
                filename = filename.replace(".html", ".md")
                file_path = output_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logfire.info(f"Processed: {url}")
                return url, "success"
            else:
                if attempt < max_retries - 1:
                    logfire.warn(
                        f"Failed to fetch {url}: Status code {response.status_code}. Retrying..."
                    )
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logfire.error(
                        f"Failed to fetch {url}: Status code {response.status_code} after {max_retries} attempts"
                    )
                    return url, "failed"
        except Exception as e:
            if attempt < max_retries - 1:
                logfire.warn(f"Error processing {url}: {str(e)}. Retrying...")
                time.sleep(2**attempt)  # Exponential backoff
            else:
                logfire.error(
                    f"Error processing {url}: {str(e)} after {max_retries} attempts"
                )
                return url, "error: " + str(e)


def process_documentation(
    base_url: str, start_url: str, output_dir: Path, dry_run: bool = False
):
    output_dir.mkdir(parents=True, exist_ok=True)

    rate_limiter = RateLimiter(60)  # Reduced to 60 requests per minute
    visited: Set[str] = set()

    with httpx.Client() as client:
        links = extract_links(client, base_url, start_url)
        for link in tqdm(links, desc=f"Fetching {base_url}"):
            if not dry_run:
                url, status = fetch_markdown(
                    client, link, output_dir, rate_limiter, visited
                )
                logfire.info(f"URL: {url}, Status: {status}")


def main(dry_run: bool = False):
    sites: List[Tuple[str, str, str]] = [
        ("https://react.dev", "https://react.dev/learn", "react_docs"),
        ("https://react.dev", "https://react.dev/reference/react", "react_docs"),
        (
            "https://expressjs.com",
            "https://expressjs.com/en/starter/installing.html",
            "express_docs",
        ),
    ]

    with logfire.span("Scraping documentation: react.js, express.js"):
        for base, start, output in sites:
            with logfire.span("Scraping site: {baseurl=}", baseurl=base):
                process_documentation(base, start, data_path / output, dry_run)
        logfire.info("Finished scraping documentation")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape documentation websites")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without downloading files",
    )
    args = parser.parse_args()

    main(dry_run=args.dry_run)
