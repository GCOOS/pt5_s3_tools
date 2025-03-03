# PT5 Uploader

A Python-based tool for uploading Imaging FlowCytobot (IFCB) data files to Amazon S3 as 
part of the GCOOS ORION project. This tool is designed to handle both single file and 
directory uploads with configurable options for bucket selection and file handling.

## Overview

This tool is specifically designed for the GCOOS ORION project to manage and upload IFCB 
(Imaging FlowCytobot) data files to Amazon S3. IFCB is an automated submersible 
flow cytometer that provides continuous, high-resolution measurements of phytoplankton 
and microzooplankton abundance and composition.

## Features

- 🔐 AWS credentials validation
- 📁 Support for IFCB data file uploads
- 🔄 Recursive directory upload option for IFCB data directories
- 🎨 Colorized console output
- 📊 Progress tracking with tqdm
- 🔍 Dry-run mode for testing
- ⚙️ Environment variable configuration
- 📝 Detailed logging

## Prerequisites

- Python 3.6 or higher
- AWS account with S3 access
- AWS credentials with appropriate permissions
- IFCB data files in the specified directory

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
IFCB_DATA_DIR=/path/to/your/ifcb/data
```

### Environment Variables

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_DEFAULT_REGION`: Default AWS region
- `AWS_S3_REGION`: S3-specific region
- `AWS_UPLOAD_URL`: Default S3 bucket and path (format: s3://bucket/path)
- `IFCB_DATA_DIR`: Default IFCB data directory for uploads

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

- `--source`: Source IFCB file or directory to upload (defaults to IFCB_DATA_DIR)
- `--bucket`: Target S3 bucket name (defaults to bucket from AWS_UPLOAD_URL)
- `--prefix`: S3 key prefix (optional)
- `--recursive`: Upload IFCB data directories recursively
- `--dry-run`: Show what would be uploaded without actually uploading
- `--verbose`: Enable verbose logging
- `--validate`: Only validate AWS credentials and exit

### Examples

1. Validate AWS credentials:
```bash
python pt5_uploader.py --validate
```

2. Upload a single IFCB data file:
```bash
python pt5_uploader.py --source /path/to/ifcb_file.txt --bucket my-bucket
```

3. Upload an IFCB data directory recursively:
```bash
python pt5_uploader.py --source /path/to/ifcb_data --bucket my-bucket --recursive
```

4. Dry run with verbose output:
```bash
python pt5_uploader.py --dry-run --verbose
```

## Error Handling

The tool provides clear error messages for common issues:

- Invalid AWS credentials
- Missing environment variables
- Non-existent IFCB data paths
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

robertdcurrier@tamu.edu

## Acknowledgments

- AWS SDK for Python (boto3)
- tqdm for progress bars
- colorama for cross-platform colored output
- GCOOS ORION project team
- IFCB development team
