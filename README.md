# PT5 Uploader

A Python-based tool for uploading files to Amazon S3 with progress tracking and 
colorized output. This tool is designed to handle both single file and directory 
uploads with configurable options for bucket selection and file handling.

## Features

- 🔐 AWS credentials validation
- 📁 Support for single file and directory uploads
- 🔄 Recursive directory upload option
- 🎨 Colorized console output
- 📊 Progress tracking with tqdm
- 🔍 Dry-run mode for testing
- ⚙️ Environment variable configuration
- 📝 Detailed logging

## Prerequisites

- Python 3.6 or higher
- AWS account with S3 access
- AWS credentials with appropriate permissions

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

## Configuration

Create a `.env` file in the project root with your AWS credentials:

```env
# Amazon S3 settings
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=your_region
AWS_S3_REGION=your_region
AWS_UPLOAD_URL=s3://your-bucket/your-path
IFCB_DATA_DIR=/path/to/your/data
```

### Environment Variables

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_DEFAULT_REGION`: Default AWS region
- `AWS_S3_REGION`: S3-specific region
- `AWS_UPLOAD_URL`: Default S3 bucket and path (format: s3://bucket/path)
- `IFCB_DATA_DIR`: Default source directory for uploads

## Usage

### Basic Usage

```bash
python pt5_uploader.py
```

### Command Line Options

```bash
python pt5_uploader.py [options]
```

#### Options:

- `--source`: Source file or directory to upload (defaults to IFCB_DATA_DIR)
- `--bucket`: Target S3 bucket name (defaults to bucket from AWS_UPLOAD_URL)
- `--prefix`: S3 key prefix (optional)
- `--recursive`: Upload directories recursively
- `--dry-run`: Show what would be uploaded without actually uploading
- `--verbose`: Enable verbose logging
- `--validate`: Only validate AWS credentials and exit

### Examples

1. Validate AWS credentials:
```bash
python pt5_uploader.py --validate
```

2. Upload a single file:
```bash
python pt5_uploader.py --source /path/to/file.txt --bucket my-bucket
```

3. Upload a directory recursively:
```bash
python pt5_uploader.py --source /path/to/dir --bucket my-bucket --recursive
```

4. Dry run with verbose output:
```bash
python pt5_uploader.py --dry-run --verbose
```

## Error Handling

The tool provides clear error messages for common issues:

- Invalid AWS credentials
- Missing environment variables
- Non-existent source paths
- S3 upload failures

All errors are colorized for better visibility:
- 🔴 Red: Errors
- 🟢 Green: Success messages
- 🔵 Blue: Information messages

## Development

### Code Style

This project follows strict coding standards:
- Maximum line length: 79 characters
- Maximum function length: 35 lines
- Type hints for all functions
- Comprehensive docstrings
- Proper error handling

### Running Tests

```bash
# TODO: Add test instructions when tests are implemented
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Neo

## Acknowledgments

- AWS SDK for Python (boto3)
- tqdm for progress bars
- colorama for cross-platform colored output
