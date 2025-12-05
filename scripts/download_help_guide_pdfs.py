"""
Download Help Guide PDFs for Camera Documentation

This script downloads PDF help guides for CrSDK-compatible cameras from Sony's helpguide.sony.net.
It reads camera models and URLs from data/html-source.md and downloads PDFs to organized directories.

Usage:
    python scripts/download_help_guide_pdfs.py [--camera MODEL] [--output-dir DIR]
"""

import os
import re
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


class HelpGuidePDFDownloader:
    """Downloads PDF help guides from Sony camera help guide websites"""

    def __init__(self, output_dir: str = "data/help-guides", delay: float = 1.5):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def load_camera_urls(self, source_file: str = "data/html-source.md") -> Dict[str, str]:
        """
        Load camera model to help guide URL mapping from html-source.md

        Returns:
            Dictionary mapping camera model to help guide URL
        """
        camera_urls = {}

        with open(source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_model = None
        for line in lines:
            line = line.strip()

            # Skip empty lines and instruction lines
            if not line or line.startswith('instructions:') or line.startswith('example'):
                continue

            # Check if line is a URL
            if line.startswith('http'):
                if current_model:
                    camera_urls[current_model] = line
                    current_model = None
            else:
                # This is a camera model name
                # Clean up version info in parentheses
                model = re.sub(r'\(.*?\)', '', line).strip()
                # Handle models with slashes (e.g., "ILME-FX6V/ILME-FX6T")
                if '/' in model:
                    # Take first model
                    model = model.split('/')[0].strip()
                current_model = model

        return camera_urls

    def find_pdf_link(self, help_guide_url: str) -> Optional[str]:
        """
        Find PDF download link on help guide page

        Args:
            help_guide_url: URL of the help guide index page

        Returns:
            URL of the PDF file, or None if not found
        """
        try:
            response = self.session.get(help_guide_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Common patterns for PDF links
            pdf_patterns = [
                # Direct PDF links
                lambda: soup.find('a', href=re.compile(r'\.pdf$', re.IGNORECASE)),
                # Links containing "download" and "pdf"
                lambda: soup.find('a', string=re.compile(r'download.*pdf|pdf.*download', re.IGNORECASE)),
                # Links with "Print" or "Download" text
                lambda: soup.find('a', string=re.compile(r'print|download', re.IGNORECASE)),
                # Links in common PDF download locations
                lambda: soup.find('div', class_=re.compile(r'download|pdf')).find('a') if soup.find('div', class_=re.compile(r'download|pdf')) else None,
            ]

            pdf_link = None
            for pattern_func in pdf_patterns:
                try:
                    link = pattern_func()
                    if link and link.get('href'):
                        href = link['href']
                        # Convert relative URL to absolute
                        pdf_link = urljoin(help_guide_url, href)
                        # Verify it's a PDF
                        if pdf_link.lower().endswith('.pdf') or '.pdf' in pdf_link.lower():
                            return pdf_link
                except:
                    continue

            # If no PDF link found, check for common PDF URL pattern
            parsed_url = urlparse(help_guide_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            path_parts = parsed_url.path.split('/')

            # Common pattern: /ilc/2440/v1/en/print.html or /ilc/2440/v1/en/helpguide.pdf
            if len(path_parts) >= 4:
                base_path = '/'.join(path_parts[:4])
                potential_pdf_urls = [
                    f"{base_url}{base_path}/helpguide.pdf",
                    f"{base_url}{base_path}/print.html",
                ]

                for potential_url in potential_pdf_urls:
                    try:
                        head_response = self.session.head(potential_url, timeout=5)
                        if head_response.status_code == 200:
                            content_type = head_response.headers.get('Content-Type', '')
                            if 'pdf' in content_type.lower() or potential_url.endswith('.pdf'):
                                return potential_url
                    except:
                        continue

            return None

        except Exception as e:
            print(f"  Error finding PDF link: {e}")
            return None

    def download_pdf(self, pdf_url: str, output_path: Path) -> bool:
        """
        Download PDF file from URL

        Args:
            pdf_url: URL of the PDF file
            output_path: Local path to save the PDF

        Returns:
            True if download successful, False otherwise
        """
        try:
            print(f"  Downloading: {pdf_url}")
            response = self.session.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()

            # Verify content type
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not pdf_url.lower().endswith('.pdf'):
                print(f"  Warning: Content-Type is {content_type}, may not be PDF")

            # Download with progress
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify file is not empty and has PDF magic bytes
            file_size = output_path.stat().st_size
            if file_size == 0:
                print(f"  Error: Downloaded file is empty")
                output_path.unlink()
                return False

            # Check PDF magic bytes (%PDF)
            with open(output_path, 'rb') as f:
                magic_bytes = f.read(4)
                if magic_bytes != b'%PDF':
                    print(f"  Warning: File does not appear to be a PDF (magic bytes: {magic_bytes})")

            print(f"  ✓ Downloaded: {file_size / 1024 / 1024:.2f} MB")
            return True

        except Exception as e:
            print(f"  ✗ Download failed: {e}")
            if output_path.exists():
                output_path.unlink()
            return False

    def download_camera_pdf(self, model: str, help_guide_url: str) -> Dict:
        """
        Download PDF for a specific camera model

        Args:
            model: Camera model name
            help_guide_url: URL of the help guide

        Returns:
            Dictionary with download statistics
        """
        print(f"\n{'='*60}")
        print(f"Processing: {model}")
        print(f"URL: {help_guide_url}")
        print(f"{'='*60}")

        stats = {
            "model": model,
            "help_guide_url": help_guide_url,
            "success": False,
            "pdf_url": None,
            "file_size_bytes": 0,
            "error": None
        }

        # Create model directory
        model_dir = self.output_dir / model / "raw"
        model_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Find PDF link
            pdf_url = self.find_pdf_link(help_guide_url)

            if not pdf_url:
                stats["error"] = "PDF link not found on help guide page"
                print(f"  ✗ {stats['error']}")
                return stats

            stats["pdf_url"] = pdf_url

            # Download PDF
            pdf_filename = f"{model}_helpguide.pdf"
            output_path = model_dir / pdf_filename

            if self.download_pdf(pdf_url, output_path):
                stats["success"] = True
                stats["file_size_bytes"] = output_path.stat().st_size
                stats["output_path"] = str(output_path)
            else:
                stats["error"] = "Download failed"

            time.sleep(self.delay)

        except Exception as e:
            stats["error"] = str(e)
            print(f"  ✗ Error: {e}")

        return stats

    def download_all(self, camera_urls: Dict[str, str]) -> List[Dict]:
        """
        Download PDFs for all cameras

        Args:
            camera_urls: Dictionary mapping camera model to help guide URL

        Returns:
            List of download statistics for each camera
        """
        all_stats = []

        for model, url in camera_urls.items():
            stats = self.download_camera_pdf(model, url)
            all_stats.append(stats)

            # Save intermediate summary after each download
            self.save_summary(all_stats)

        return all_stats

    def save_summary(self, all_stats: List[Dict]):
        """Save download summary to JSON file"""
        summary_path = self.output_dir / "download_summary.json"

        summary = {
            "total_cameras": len(all_stats),
            "successful_downloads": sum(1 for s in all_stats if s["success"]),
            "failed_downloads": sum(1 for s in all_stats if not s["success"]),
            "total_size_mb": sum(s.get("file_size_bytes", 0) for s in all_stats) / 1024 / 1024,
            "downloads": all_stats
        }

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='Download help guide PDFs for Sony cameras')
    parser.add_argument('--camera', type=str, help='Specific camera model to download')
    parser.add_argument('--output-dir', type=str, default='data/help-guides',
                        help='Output directory for PDFs')
    parser.add_argument('--delay', type=float, default=1.5,
                        help='Delay between downloads in seconds')
    parser.add_argument('--source', type=str, default='data/html-source.md',
                        help='Source file with camera URLs')

    args = parser.parse_args()

    downloader = HelpGuidePDFDownloader(output_dir=args.output_dir, delay=args.delay)

    # Load camera URLs
    print(f"Loading camera URLs from {args.source}...")
    camera_urls = downloader.load_camera_urls(args.source)
    print(f"Found {len(camera_urls)} camera models")

    # Download specific camera or all
    if args.camera:
        camera = args.camera.upper()
        if camera not in camera_urls:
            print(f"Error: Camera {camera} not found in source file")
            print(f"Available cameras: {', '.join(sorted(camera_urls.keys()))}")
            return

        camera_urls = {camera: camera_urls[camera]}

    # Download PDFs
    all_stats = downloader.download_all(camera_urls)

    # Print summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)

    successful = sum(1 for s in all_stats if s["success"])
    failed = sum(1 for s in all_stats if not s["success"])
    total_size = sum(s.get("file_size_bytes", 0) for s in all_stats) / 1024 / 1024

    print(f"Total cameras: {len(all_stats)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total size: {total_size:.2f} MB")
    print(f"\nSummary saved to: {args.output_dir}/download_summary.json")

    if failed > 0:
        print(f"\nFailed downloads:")
        for stat in all_stats:
            if not stat["success"]:
                print(f"  - {stat['model']}: {stat['error']}")


if __name__ == "__main__":
    main()
