# Reading Log CLI Usage

## Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Log an article or book from a URL:

```bash
python3 cli.py <URL>
```

Example:

```bash
python3 cli.py https://example.com/article
```

### Options

- `--type {article,book}`: Force the content type. If not specified, the tool will automatically determine based on word count (articles < 20k words, books >= 20k words).

- `--base-dir PATH`: Specify the base directory for the reading log (default: current directory).

### Examples

Log an article:

```bash
python3 cli.py https://www.example.com/article
```

Force log as a book:

```bash
python3 cli.py https://www.example.com/book --type book
```

Specify a different base directory:

```bash
python3 cli.py https://www.example.com/article --base-dir /path/to/logs
```

## Features

1. **URL Input**: Feed in any URL from the internet
2. **Content Extraction**: Automatically extracts readable text from web pages
3. **Word Counting**: Counts words in the extracted content
4. **Automatic Categorization**: Determines if content is a book or article based on word count
5. **Date Recording**: Automatically records the current date
6. **File Organization**: Writes to the appropriate file (`{month}-articles.txt` or `{month}-books.txt`) in the `{year}/` directory

## How It Works

1. Fetches the HTML content from the provided URL
2. Extracts readable text using BeautifulSoup, prioritizing main content areas
3. Counts words in the extracted text
4. Extracts metadata (title, author) from HTML meta tags and content
5. Determines content type (book vs article) based on word count threshold
6. Formats an entry matching your existing log file structure
7. Appends the entry to the appropriate file in the year/month directory
