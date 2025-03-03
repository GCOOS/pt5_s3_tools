# PT5 Uploader

A Python tool for efficiently uploading Imaging FlowCytobot (IFCB) data files to Amazon S3.

## Overview

This tool is designed to efficiently upload IFCB data files to Amazon S3, with optimized performance for large file sets. It includes features for concurrent processing, progress tracking, and detailed reporting.

## Features

- AWS credentials validation
- Support for IFCB data file uploads
- Recursive directory upload option
- Colorized console output
- Concurrent file uploads (up to 32 workers)
- Connection pool optimization (100 connections)
- Automatic retry on failures (3 attempts)
- Batched file submission (1000 files per batch)
- Pre-computed S3 keys for improved performance
- Overall progress tracking with tqdm
- Detailed summary report with:
  * Total files processed
  * Total data transferred
  * Upload duration
  * Average transfer rate
  * Files processed per second
- Dry-run mode for testing
- Environment variable configuration
- Detailed logging

## System Requirements

- Python 3.6 or higher
- Sufficient system resources for concurrent processing
- Recommended: 4+ CPU cores and 8GB+ RAM for large file sets
- AWS credentials with appropriate S3 permissions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pt5_uploader.git
cd pt5_uploader
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

Basic usage:
```bash
python pt5_uploader.py --source /path/to/files
```

With options:
```bash
python pt5_uploader.py \
    --source /path/to/files \
    --bucket your-bucket \
    --prefix path/in/bucket \
    --recursive \
    --verbose
```

### Command Line Options

- `--source`: Source file or directory to upload
- `--bucket`: Target S3 bucket name
- `--prefix`: S3 key prefix (optional)
- `--recursive`: Upload directories recursively
- `--dry-run`: Show what would be uploaded without actually uploading
- `--verbose`: Enable verbose logging
- `--validate`: Only validate AWS credentials and exit

## Performance Considerations

The tool is optimized for large file sets with the following features:
- Batched file submission (1000 files per batch)
- Pre-computed S3 keys
- Optimized connection pooling
- Concurrent upload processing

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
- S3 upload failures

Failed uploads are logged with detailed error messages.

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
