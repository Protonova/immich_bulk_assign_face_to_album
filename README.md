# 🖼️ Bulk Assign Faces to Images Within Albums

A Python script for bulk assigning faces to assets within a specified album in your Immich install.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![UV](https://img.shields.io/badge/Dependencies-UV-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Beta-orange.svg)

---

## 🎯 Overview
This script allows you to bulk assign your favourite pet or person to all assets within a specified album. It's perfect for scenarios where you have a curated album where you want to quickly tag a person on an image or video within said album.

I recently migrated from Google Photos to Immich: the built-in face recognition doesn't always work perfectly, especially with pets. If you have albums from Google Photos where most images contain a specific person or pet, this script can bulk assign that face to all assets in the album that don't already have it.

## ✨ Features
- **Bulk Face Assignment**: Add a face to multiple images/videos at once
- **Smart Filtering**: Only processes images/videos that don't already have the target person/pet
- **API Validation**: Validates server connection, API key, album, and person IDs
- **Rate Limiting**: Includes delays and retry logic to be respectful to your server and reverse proxy
- **Progress Tracking**: Visually see progress for big jobs and log out to closely examine actions
- **Error Handling**: Graceful handling of network/API errors and timeouts

## 🔑 Prerequisites
- Python 3.7 or higher
- [UV](https://github.com/astral-sh/uv) (recommended) or pip for dependency management
- An Immich server with API access
- A valid Immich API key
- Album ID and Person ID you want to work with
- Ownership of recipient Album

## 📦 Installation

1. **Clone or download the script**
   ```bash
   git clone https://github.com/Protonova/immich_bulk_assign_face_to_album.git
   cd immich_bulk_assign_face_to_album
   ```

2. **Install required dependencies using UV**
   
   [UV](https://docs.astral.sh/uv/) is an extremely fast Python package and project manager, written in Rust (nuff said). It provides better dependency resolution and faster installs (over pip). Dependencies are managed within `pyproject.toml`.
   
   ```bash
   # Install UV if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies
   uv sync
   ```

   Or if you prefer pip:
   ```bash
   pip install requests
   ```
3. If Installing from windows, [Astral](https://docs.astral.sh/uv/getting-started/installation/) has an IEX WFM script. Make sure to add UV to PATH vars after install.
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

## 🚀 Usage

### Basic Command

**Using UV (recommended):**
```bash
uv run immich_bulk_assign_face_to_album.py --server https://your_immich_server.com --key your_api_key --person person_id --album album_id
```

**Using Python directly:**
```bash
python immich_bulk_assign_face_to_album.py --server https://your_immich_server.com --key your_api_key --person person_id --album album_id
```

### With Debug Output

**Using UV:**
```bash
uv run immich_bulk_assign_face_to_album.py --server https://your_immich_server.com --key your_api_key --person person_id --album album_id --debug
```

**Using Python directly:**
```bash
python immich_bulk_assign_face_to_album.py --server https://your_immich_server.com --key your_api_key --person person_id --album album_id --debug
```

### Parameters

| Parameter  | Required | Description |
|------------|----------|-------------|
| `--url`    | ✅ | Your Immich server URL (e.g., `https://immich.domain.com`) |
| `--key`    | ✅ | Your Immich API key |
| `--person` | ✅ | ID of the person you want to add to images |
| `--album`  | ✅ | ID of the album containing the target images |
| `--debug` | ❌ | Enable verbose debug output |

### Getting IDs

**Finding Album IDs:**
1. Go to the "Albums" section in Immich: `https://your_immich_server.com/albums`
2. Navigate to the desired album
3. Grab the unique ID at the end of the URL: `https://your_immich_server.com/albums/{album-id}`

**Finding Person IDs:**
1. Go to the "People" section in Immich: `https://your_immich_server.com/people`
2. Click on the person
3. Grab the unique ID at the end of the URL: `https://your_immich_server.com/people/{person-id}`

## 💡 Example Use Case

**Scenario**: You imported photos from Google Photos and have an album called "My Dog Rex" with 2000+ photos (don't judge lol). Immich's face recognition missed 70% of the images that Rex was in...

**Solution**:
1. Create or identify the pet "Rex" in Immich
2. Grab the album ID and person ID
3. Run the script to bulk assign Rex's face to all images/videos in that album

```bash
uv run immich_bulk_assign_face_to_album.py \
  --url https://immich.mydomain.com \
  --key 1234567890abcdef \
  --person abc123-def456-ghi789 \
  --album xyz789-uvw456-rst123 \
```

## ⚠️ Important Notes

- **Imposed Query Limit**: The script processes only the first 50 assets in an album (for testing purposes, will remove in future)
- **Rate Limiting**: Includes 0.1-second delays between requests to avoid overwhelming your server
- **Backup Recommended**: Always backup your Immich database before running bulk operations. See [this](https://immich.app/docs/administration/backup-and-restore/) guide for instructions.
- **Test First**: Try with a small album first to ensure everything works as expected

## 🔧 Current Limitations & TODOs

This is an alpha version with several planned improvements:

- [x] Code cleanup and better commenting
- [x] Improved variable naming
- [x] Proper variable initialization
- [x] Enhanced error handling and logging
- [ ] Remove hardcoded 50-asset limit
- [x] Session management across all requests
- [ ] Break logic into more focused functions
- [ ] Performance optimizations
- [x] Add progress indicators
- [ ] Refactor constructor, overly complicated
- [ ] Breakup logic into testable functions

## 🛠️ Troubleshooting

**401 Unauthorized Error**
- Verify your API key is correct/valid
- Check that your API key has the necessary permissions (i.g., don't have access to the API or Album)

**Album/Person Not Found**
- Double-check the IDs from your Immich web interface
- Ensure the album and person exist in your Immich instance

**Connection Timeouts**
- The script includes retry logic, but if you have a slow connection, you may need to increase timeout values

## ⭐ Recommendations

1. **Immich-Face-To-Album**
   - https://github.com/romainrbr/immich-face-to-album
   - This script automatically adds images containing a specified person to the target album. Useful for keeping albums updated when you manually tag new faces but forget to add them to albums.
   - Take a look at [immich-face-to-album's readme](https://github.com/romainrbr/immich-face-to-album?tab=readme-ov-file#on-a-schedule) to see how to add as a cron job.
2. **Immich-go**
   - https://github.com/simulot/immich-go
   - Script designed to streamline uploading large photo collections to your Immich server. Highly customizable, check readme for details.

## 🤝 Contributing

This is a personal project in early development. Contributions, suggestions, and improvements are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the [Immich](https://immich.app/) self-hosted photo management system
- I have to include, the awesome team of people who created/maintain the [API Documentation](https://immich.app/docs/api/)
- Created to solve Google Photos migration challenges

---
**⚠️ Disclaimer**: This tool is provided as-is. Always backup your data before running bulk operations on your photo library.