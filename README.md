[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/Semiror78/AG-DownGel/blob/main/README.md)
[![ru](https://img.shields.io/badge/lang-ru-green.svg)](https://github.com/Semiror78/AG-DownGel/blob/main/README.ru.md)
[![zh](https://img.shields.io/badge/lang-zh-yellow.svg)](https://github.com/Semiror78/AG-DownGel/blob/main/README.zh.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/Semiror78/AG-DownGel/blob/main/README.ja.md)

# AG-DownGel

A cross-platform GUI downloader for GelBooru.com, built with PyQt6. Search and download images, GIFs, and videos by tags with filtering, AI exclusion, and organized storage.

## Features
- **Tag-based Search**: Enter space-separated tags (e.g., `catgirl solo`); supports GelBooru syntax like `rating:explicit`.
- **File Filtering**: Select images (.jpg, .png, etc.), GIFs, or videos (.mp4, .webm); downloads sorted into subfolders (`images/`, `GIF/`, `videos/`).
- **AI Exclusion**: Checkbox adds `-ai-generated` to exclude AI content.
- **API Support**: Optional User ID/API Key for higher limits (get from [GelBooru Account](https://gelbooru.com/index.php?page=account&s=options)).
- **Localization**: English (default), Russian, Chinese, Japanese; extensible via `locales/*.json`.
- **Downloads**: Saved to `downloads/[sanitized_tags]/` for easy organization.
- **Progress & Errors**: Real-time status, indeterminate progress for pagination.

## Installation
1. Ensure Python 3.10+ and install dependencies:
2. pip install pyqt6 requests
3. Run: `python main.py` (rename your script if needed).
4. Folders auto-created: `downloads/` (output) and `locales/` (translations).

## Usage
1. Select language from dropdown (top).
2. Enter tags in the search field (e.g., `brazilian_miku hatsune_miku feet`).
3. Check "No AI" to exclude AI-generated.
4. Select file types.
5. (Optional) Enter User ID and API Key.
6. Click "Download All" – files save to `downloads/[tags]/`.

## Example Tags
From `guide.txt`:

**Kasane_teto -hatsune_miku rating:explicit**  
(downloads teto without miku, with 18+ content)

**Rating Options:**  
- `rating:explicit` (NSFW)  
- `rating:questionable` (borderline)  
- `rating:sensitive` (mature)  
- `rating:general` (safe)

## Troubleshooting
- **0 Posts?** Add related tags (e.g., `hatsune_miku` for `brazilian_miku`); check GelBooru [DAPI docs](https://gelbooru.com/index.php?page=help&topic=dapi).
- **Rate Limits:** Use API Key for >100 results/page.
- **Custom Languages:** Add `locales/[lang].json` with keys matching `en.json`.

## License
MIT License – free to use/modify.

