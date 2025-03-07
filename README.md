# PT5 S3 Tool

A Python tool for efficiently transferring Imaging FlowCytobot (IFCB) data files to and from Amazon S3.

## Overview

This tool is designed to efficiently upload, download, list, and delete IFCB data files in Amazon S3, with optimized performance for large file sets. It includes features for concurrent processing, progress tracking, and detailed reporting.

## Features

- AWS credentials validation
- Support for IFCB data file uploads and downloads
- Recursive directory processing
- Colorized console output
- Concurrent file transfers (up to 32 workers)
- Connection pool optimization (100 connections)
- Automatic retry on failures (3 attempts)
- Batched file submission (1000 files per batch)
- Pre-computed paths for improved performance
- Overall progress tracking with tqdm
- Detailed summary report with:
  * Total files processed
  * Total data transferred
  * Transfer duration
  * Average transfer rate
  * Files processed per second
- Dry-run mode for testing
- Environment variable configuration (automatically used when no args provided)
- Detailed logging
- S3 bucket listing capabilities
- File filtering options for downloads
- Fast bulk deletion of S3 objects
- Simplified S3 URI handling with the --destination parameter

## System Requirements

- Python 3.6 or higher
- Sufficient system resources for concurrent processing
- Recommended: 4+ CPU cores and 8GB+ RAM for large file sets
- AWS credentials with appropriate S3 permissions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pt5_s3_tool.git
cd pt5_s3_tool
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials:
   - Create a `.env` file in the project root
   - Add your AWS credentials:
     ```
     AWS_ACCESS_KEY_ID=your_access_key
     AWS_SECRET_ACCESS_KEY=your_secret_key
     AWS_UPLOAD_URL=s3://your-bucket/path
     IFCB_DATA_DIR=/path/to/ifcb/data
     ```

## Usage

### Upload Files

```bash
# Using the new --destination parameter (recommended)
python pt5_s3_tool.py --source /path/to/files \
    --destination s3://your-bucket/path/in/bucket \
    --recursive

# Using legacy parameters
python pt5_s3_tool.py --mode upload \
    --source /path/to/files \
    --bucket your-bucket \
    --prefix path/in/bucket \
    --recursive
```

### Download Files

```bash
# Using the new --destination parameter (recommended)
python pt5_s3_tool.py --mode download \
    --source s3://your-bucket/path/in/bucket \
    --destination /local/path \
    --recursive \
    --filter "*.png"

# Using legacy parameters
python pt5_s3_tool.py --mode download \
    --bucket your-bucket \
    --prefix path/in/bucket \
    --destination /local/path \
    --recursive \
    --filter "*.png"
```

### List Bucket Contents

```bash
# Using the new --destination parameter (recommended)
python pt5_s3_tool.py --mode list \
    --destination s3://your-bucket/path/in/bucket \
    --recursive

# Using legacy parameters
python pt5_s3_tool.py --mode list \
    --bucket your-bucket \
    --prefix path/in/bucket \
    --recursive
```

### Delete Files

```bash
# Using the new --destination parameter (recommended)
python pt5_s3_tool.py --mode delete \
    --destination s3://your-bucket/path/in/bucket \
    --recursive

# Alternative syntax with --delete flag
python pt5_s3_tool.py --destination s3://your-bucket/path/in/bucket \
    --delete \
    --recursive \
    --filter "*.tmp"

# Using legacy parameters
python pt5_s3_tool.py --mode delete \
    --bucket your-bucket \
    --prefix path/in/bucket \
    --recursive
```

### Using Environment Variables

If you've set up the `.env` file with `AWS_UPLOAD_URL` and `IFCB_DATA_DIR`, you can run the tool without arguments:

```bash
# Uses environment variables for source and destination
python pt5_s3_tool.py
```

### Command Line Options

#### Common Options
- `--mode`: Operation mode (`upload`, `download`, `list`, or `delete`)
- `--destination`: S3 destination in format s3://bucket/prefix for uploads, or local directory for downloads
- `--recursive`: Process directories recursively
- `--dry-run`: Show what would be transferred without actually transferring
- `--verbose`: Enable verbose logging
- `--validate`: Only validate AWS credentials and exit

#### Legacy Options (deprecated, use --destination instead)
- `--bucket`: Target S3 bucket name
- `--prefix`: S3 key prefix

#### Upload Options
- `--source`: Source file or directory to upload

#### Download Options
- `--source`: S3 prefix to download from (can be in s3://bucket/prefix format)
- `--destination`: Local directory to download files to
- `--overwrite`: Overwrite existing files when downloading
- `--filter`: Filter pattern for files to download (e.g., "*.png")

#### Delete Options
- `--delete`: Alternative to --mode delete, confirms deletion intent
- `--filter`: Filter pattern for files to delete (e.g., "*.tmp")

## Performance Considerations

The tool is optimized for large file sets with the following features:
- Batched file submission (1000 files per batch)
- Pre-computed paths
- Optimized connection pooling
- Concurrent processing
- S3 bulk delete API for fast deletions

For optimal performance, ensure your system has:
- Sufficient CPU cores for concurrent processing
- Adequate memory for handling large file sets
- Fast storage for file operations
- Reliable network connection to AWS

## Error Handling

The tool includes comprehensive error handling for:
- AWS credential validation
- File system operations
- Network connectivity issues
- S3 transfer failures

Failed operations are logged with detailed error messages.

## Development

### Code Style
- Follow PEP 8 guidelines
- Maximum line length: 79 characters
- Maximum function length: 35 lines
- Include docstrings for all functions

### Testing
- Run tests before submitting changes
- Include new tests for new features
- Maintain test coverage above 80%

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Robert D. Currier (robertdcurrier@tamu.edu)

## Acknowledgments

- AWS Boto3 team for the excellent S3 client library
- tqdm team for the progress bar implementation
