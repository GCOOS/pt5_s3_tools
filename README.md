# PT5 Uploader

A Python tool for uploading Imaging FlowCytobot (IFCB) data files to Amazon S3 as part of the GCOOS ORION project.

## Overview

This tool is designed to efficiently upload IFCB (Imaging FlowCytobot) data files to Amazon S3. IFCB is an automated submersible flow cytometer that provides continuous, high-resolution measurements of phytoplankton and microzooplankton abundance and composition.

## Features

- **AWS Credentials Validation**: Verifies AWS credentials before starting uploads
- **IFCB Data Support**: Optimized for handling IFCB data file uploads
- **Recursive Upload**: Option to upload entire directories and subdirectories
- **Concurrent Processing**: 
  - Up to 32 concurrent file uploads
  - Connection pool optimization (100 connections)
  - Automatic retry on failures (3 attempts)
- **Progress Tracking**:
  - Overall progress bar showing files completed
  - Initial file count display
  - Detailed summary report with:
    * Total files processed
    * Total data transferred
    * Upload duration
    * Average transfer rate
    * Files processed per second
- **Colorized Output**: Enhanced readability with color-coded messages
- **Dry-Run Mode**: Test uploads without actually transferring files
- **Environment Variables**: Configure default settings via .env file
- **Detailed Logging**: Comprehensive logging of all operations

## Prerequisites

- Python 3.6 or higher
- AWS credentials with S3 access
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pt5_uploader.git
cd pt5_uploader
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_UPLOAD_URL=s3://your-bucket/path
IFCB_DATA_DIR=/path/to/ifcb/data
```

## Usage

Basic usage:
```bash
python pt5_uploader.py
```

With options:
```bash
# Upload recursively
python pt5_uploader.py --recursive

# Dry run to see what would be uploaded
python pt5_uploader.py --dry-run

# Validate AWS credentials only
python pt5_uploader.py --validate

# Enable verbose logging
python pt5_uploader.py --verbose

# Specify custom source and destination
python pt5_uploader.py --source /path/to/files --bucket my-bucket --prefix my/path
```

## Error Handling

The tool includes comprehensive error handling:
- AWS credential validation
- File existence checks
- Upload retry logic
- Detailed error messages
- Progress tracking even during errors

## Development Guidelines

- Follow PEP 8 style guide
- Maximum line length: 79 characters
- Maximum function length: 35 lines
- Include docstrings for all functions
- Use type hints
- Add logging for important operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

robertdcurrier@tamu.edu

## Acknowledgments

- GCOOS ORION project team
- AWS Boto3 team
- IFCB development team
