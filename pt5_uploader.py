#!/usr/bin/env python3
"""
PT5 Uploader - A tool for uploading Imaging FlowCytobot (IFCB) data files to 
Amazon S3.

This script is specifically designed for the GCOOS ORION project to manage and 
upload IFCB (Imaging FlowCytobot) data files to Amazon S3. IFCB is an automated 
submersible flow cytometer that provides continuous, high-resolution measurements 
of phytoplankton and microzooplankton abundance and composition.

Features:
    - AWS credentials validation
    - Support for IFCB data file uploads
    - Recursive directory upload option
    - Colorized console output
    - Progress tracking with tqdm
    - Dry-run mode for testing
    - Environment variable configuration
    - Detailed logging

Author: robertdcurrier@tamu.edu
"""

import argparse
import logging
import os
import sys
from typing import Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from colorama import Fore, Style, init
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def validate_aws_credentials() -> bool:
    """
    Validate AWS credentials by attempting to list S3 buckets.
    
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    try:
        s3_client = boto3.client('s3')
        s3_client.list_buckets()
        logger.info(f"{Fore.GREEN}AWS credentials validated successfully"
                   f"{Style.RESET_ALL}")
        return True
    except NoCredentialsError:
        logger.error(f"{Fore.RED}Error: AWS credentials not found. Please "
                    f"check your .env file for AWS_ACCESS_KEY_ID and "
                    f"AWS_SECRET_ACCESS_KEY{Style.RESET_ALL}")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidAccessKeyId':
            logger.error(f"{Fore.RED}Error: Invalid AWS Access Key ID"
                        f"{Style.RESET_ALL}")
        elif error_code == 'SignatureDoesNotMatch':
            logger.error(f"{Fore.RED}Error: Invalid AWS Secret Access Key"
                        f"{Style.RESET_ALL}")
        else:
            logger.error(f"{Fore.RED}Error: AWS credentials validation failed: "
                        f"{str(e)}{Style.RESET_ALL}")
        return False
    except Exception as e:
        logger.error(f"{Fore.RED}Error: Unexpected error validating AWS "
                    f"credentials: {str(e)}{Style.RESET_ALL}")
        return False

def get_default_source() -> Optional[str]:
    """Get the default source directory from environment variables."""
    ifcb_dir = os.getenv('IFCB_DATA_DIR')
    if ifcb_dir and os.path.exists(ifcb_dir):
        return ifcb_dir
    return None

def get_default_bucket() -> Optional[str]:
    """Get the default bucket from AWS_UPLOAD_URL environment variable."""
    upload_url = os.getenv('AWS_UPLOAD_URL', '')
    if upload_url.startswith('s3://'):
        # Extract bucket from s3://bucket/path format
        parts = upload_url[5:].split('/')
        return parts[0]
    return None

def setup_argparse() -> argparse.ArgumentParser:
    """Set up and return the argument parser with all required options."""
    default_source = get_default_source()
    default_bucket = get_default_bucket()

    parser = argparse.ArgumentParser(
        description='Upload files to Amazon S3 with progress tracking'
    )
    parser.add_argument(
        '--source',
        help='Source file or directory to upload',
        default=default_source
    )
    parser.add_argument(
        '--bucket',
        help='Target S3 bucket name',
        default=default_bucket
    )
    parser.add_argument(
        '--prefix',
        help='S3 key prefix (optional)',
        default=''
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Upload directories recursively'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Only validate AWS credentials and exit'
    )
    return parser

def validate_args(args: argparse.Namespace) -> bool:
    """Validate command line arguments."""
    if not args.source:
        logger.error(f"{Fore.RED}Error: Source path not specified and "
                    f"IFCB_DATA_DIR not set{Style.RESET_ALL}")
        return False
    if not os.path.exists(args.source):
        logger.error(f"{Fore.RED}Error: Source path does not exist: "
                    f"{args.source}{Style.RESET_ALL}")
        return False
    if not args.bucket:
        logger.error(f"{Fore.RED}Error: Bucket not specified and "
                    f"AWS_UPLOAD_URL not set{Style.RESET_ALL}")
        return False
    return True

def main() -> int:
    """Main entry point for the application."""
    parser = setup_argparse()
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # If --validate is set, only check credentials and exit
    if args.validate:
        logger.info(f"{Fore.CYAN}Validating AWS credentials...{Style.RESET_ALL}")
        return 0 if validate_aws_credentials() else 1

    if not validate_args(args):
        return 1

    if not validate_aws_credentials():
        return 1

    try:
        # TODO: Implement file upload logic
        logger.info(f"{Fore.GREEN}Starting upload process...{Style.RESET_ALL}")
        return 0
    except Exception as e:
        logger.error(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
