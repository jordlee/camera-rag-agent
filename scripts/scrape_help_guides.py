"""
Camera Help Guide Web Scraper

This script scrapes help guide documentation from helpguide.sony.net for CrSDK-compatible cameras.
It discovers camera models, finds their help guide URLs, and downloads all documentation pages.

Usage:
    python scripts/scrape_help_guides.py [--camera MODEL] [--output-dir DIR]
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# CrSDK-compatible camera models (from Kando MCP server results)
CRSDK_CAMERAS = {
    # Alpha Series (ILCE)
    "ILCE-1M2", "ILCE-1", "ILCE-9M3", "ILCE-9M2",
    "ILCE-7RM5", "ILCE-7RM4A", "ILCE-7RM4", "ILCE-7CR",
    "ILCE-7SM3", "ILCE-7M4", "ILCE-7CM2", "ILCE-7C",
    "ILCE-6700",
    # Cinema Line (ILME)
    "ILME-FX6", "ILME-FX2", "ILME-FX3A", "ILME-FX3", "ILME-FX30", "ILME-FR7",
    # ZV Series
    "ZV-E1", "ZV-E10M2",
    # Other Models
    "ILX-LR1", "MPC-2610", "PXW-Z200", "HXR-NX800", "DSC-RX0M2", "BRC-AM7"
}

# Known help guide URL patterns (can be expanded as we discover more)
KNOWN_HELP_GUIDES = {
    "ILCE-1M2": "https://helpguide.sony.net/ilc/2440/v1/en/index.html",
    # Add more as discovered
}


class HelpGuideScraper:
    """Scraper for Sony camera help guides"""

    def __init__(self, output_dir: str = "data/help-guides", delay: float = 1.0):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.visited_urls: Set[str] = set()

    def scrape_camera(self, model: str, help_guide_url: str) -> Dict:
        """
        Scrape all help guide pages for a specific camera model.

        Args:
            model: Camera model name (e.g., "ILCE-1M2")
            help_guide_url: Base URL of the help guide (e.g., ".../index.html")

        Returns:
            Dictionary with scraping statistics
        """
        print(f"\n{'='*60}")
        print(f"Scraping help guide for {model}")
        print(f"URL: {help_guide_url}")
        print(f"{'='*60}\n")

        # Create output directory for this camera
        camera_dir = self.output_dir / model
        camera_dir.mkdir(parents=True, exist_ok=True)

        # Parse the base URL to extract the guide path
        parsed_url = urlparse(help_guide_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"

        # Start with the index page
        pages_to_scrape = [help_guide_url]
        scraped_pages = []

        stats = {
            "model": model,
            "base_url": base_url,
            "pages_scraped": 0,
            "pages_failed": 0,
            "total_size_bytes": 0
        }

        while pages_to_scrape:
            url = pages_to_scrape.pop(0)

            # Skip if already visited
            if url in self.visited_urls:
                continue

            try:
                page_data = self._scrape_page(url, base_url)
                if page_data:
                    # Save page data
                    page_filename = self._url_to_filename(url)
                    output_path = camera_dir / f"{page_filename}.json"

                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(page_data, f, indent=2, ensure_ascii=False)

                    scraped_pages.append(page_data)
                    stats["pages_scraped"] += 1
                    stats["total_size_bytes"] += len(json.dumps(page_data))

                    # Add newly discovered links to the queue
                    for link in page_data.get("internal_links", []):
                        full_link = urljoin(base_url, link)
                        if full_link not in self.visited_urls and full_link.startswith(base_url):
                            pages_to_scrape.append(full_link)

                    print(f"  ✓ Scraped: {page_data['title'][:60]}")
                else:
                    stats["pages_failed"] += 1
                    print(f"  ✗ Failed: {url}")

                self.visited_urls.add(url)
                time.sleep(self.delay)

            except Exception as e:
                print(f"  ✗ Error scraping {url}: {e}")
                stats["pages_failed"] += 1
                self.visited_urls.add(url)

        # Save scraping summary
        summary_path = camera_dir / "scraping_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        print(f"\n✓ Completed: {stats['pages_scraped']} pages scraped for {model}")
        print(f"  Output: {camera_dir}")

        return stats

    def _scrape_page(self, url: str, base_url: str) -> Optional[Dict]:
        """
        Scrape a single help guide page.

        Returns:
            Dictionary with page content and metadata, or None if failed
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"

            # Extract model name and manual number from meta tags
            model_meta = soup.find('meta', {'name': 'keywords'})
            manual_number = soup.get('data-manual-number', '')

            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.extract()

            # Extract main content
            main_content = soup.find(role="main") or soup.find('body')

            if not main_content:
                return None

            # Extract text content
            content_parts = []
            for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div', 'td', 'th']):
                text = element.get_text(strip=True)
                if text and len(text) > 1:
                    content_parts.append(text)

            content = "\n".join(content_parts)

            # Extract internal links (for discovering other pages)
            internal_links = []
            for link in main_content.find_all('a', href=True):
                href = link['href']
                # Filter for documentation links (not external or navigation)
                if href.endswith('.html') and not href.startswith('http'):
                    # Normalize path separators to forward slashes
                    href = href.replace('\\', '/')
                    internal_links.append(href)

            # Extract images
            images = []
            for img in main_content.find_all('img', src=True):
                images.append({
                    'src': img['src'],
                    'alt': img.get('alt', '')
                })

            return {
                "url": url,
                "title": title,
                "manual_number": manual_number,
                "content": content,
                "internal_links": list(set(internal_links)),
                "images": images,
                "metadata": {
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "content_length": len(content),
                    "num_images": len(images),
                    "keywords": model_meta.get('content', '') if model_meta else ''
                }
            }

        except Exception as e:
            print(f"    Error parsing page {url}: {e}")
            return None

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to a safe filename"""
        parsed = urlparse(url)
        path = parsed.path

        # Remove /index.html or .html extension
        filename = path.replace('/', '_').replace('.html', '').strip('_')

        # Handle index pages
        if not filename or filename == 'index':
            filename = 'index'

        return filename


def discover_help_guide_url(model: str) -> Optional[str]:
    """
    Attempt to discover the help guide URL for a camera model.

    This is a placeholder - in practice, we'd need to:
    1. Check Sony support pages
    2. Use a known URL pattern database
    3. Manual discovery and configuration

    Args:
        model: Camera model name

    Returns:
        Help guide URL if found, None otherwise
    """
    # Check known URLs first
    if model in KNOWN_HELP_GUIDES:
        return KNOWN_HELP_GUIDES[model]

    # TODO: Implement discovery logic
    # For now, return None - URLs need to be manually added to KNOWN_HELP_GUIDES
    return None


def main():
    parser = argparse.ArgumentParser(description='Scrape Sony camera help guides')
    parser.add_argument('--camera', type=str, help='Specific camera model to scrape')
    parser.add_argument('--output-dir', type=str, default='data/help-guides',
                        help='Output directory for scraped data')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds')
    parser.add_argument('--list-cameras', action='store_true',
                        help='List all CrSDK-compatible cameras')

    args = parser.parse_args()

    if args.list_cameras:
        print("\nCrSDK-Compatible Cameras:")
        print("=" * 60)
        for i, camera in enumerate(sorted(CRSDK_CAMERAS), 1):
            status = "✓ URL known" if camera in KNOWN_HELP_GUIDES else "✗ URL unknown"
            print(f"{i:2d}. {camera:15s} {status}")
        print(f"\nTotal: {len(CRSDK_CAMERAS)} cameras")
        print(f"With known URLs: {len(KNOWN_HELP_GUIDES)} cameras")
        return

    scraper = HelpGuideScraper(output_dir=args.output_dir, delay=args.delay)

    # Scrape specific camera or all known cameras
    if args.camera:
        camera = args.camera.upper()
        if camera not in CRSDK_CAMERAS:
            print(f"Error: {camera} is not a CrSDK-compatible camera")
            print("Use --list-cameras to see all compatible cameras")
            return

        url = discover_help_guide_url(camera)
        if not url:
            print(f"Error: Help guide URL not known for {camera}")
            print("Please add the URL to KNOWN_HELP_GUIDES in the script")
            return

        scraper.scrape_camera(camera, url)
    else:
        # Scrape all cameras with known URLs
        print(f"Scraping help guides for {len(KNOWN_HELP_GUIDES)} cameras...\n")

        all_stats = []
        for camera, url in KNOWN_HELP_GUIDES.items():
            stats = scraper.scrape_camera(camera, url)
            all_stats.append(stats)

        # Print summary
        print("\n" + "=" * 60)
        print("SCRAPING SUMMARY")
        print("=" * 60)
        total_pages = sum(s["pages_scraped"] for s in all_stats)
        total_failed = sum(s["pages_failed"] for s in all_stats)
        total_size = sum(s["total_size_bytes"] for s in all_stats)

        print(f"Cameras scraped: {len(all_stats)}")
        print(f"Total pages: {total_pages}")
        print(f"Failed pages: {total_failed}")
        print(f"Total data: {total_size / 1024 / 1024:.2f} MB")
        print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
