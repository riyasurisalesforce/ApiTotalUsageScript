
#!/usr/bin/env python3
"""
API Total Usage CSV Extractor
==============================================================================
This script extracts Total Usage API calls from Salesforce Event Log Files
using Salesforce CLI commands for authentication and querying.

Prerequisites:
1. Python 3.6+
2. Salesforce CLI installed and configured
3. Salesforce External Client App (ECA) with JWT authentication
4. Private key file for JWT authentication

Usage:
    python extract_total_usage_calls.py --client-id <client_id> --username <username> --jwt-key-file <jwt_key_file> --instance-url <instance_url> --org-alias <org_alias> --output-dir <output_dir>

Example:
    python extract_total_usage_calls.py --client-id 3MVG9A2kN3Bn17hs... --username user@company.com --jwt-key-file /path/to/key.pem --instance-url https://login.salesforce.com --org-alias myorg --output-dir /path/to/output

Cron example:
    0 2 * * * /usr/bin/python3 /path/to/extract_total_usage_calls.py --client-id 3MVG9A2kN3Bn17hs... --username user@company.com --jwt-key-file /path/to/key.pem --instance-url https://login.salesforce.com --org-alias myorg --output-dir /path/to/output

Note: Use 'which python3' or 'which python' to find the correct python path for cron
==============================================================================
"""

import sys
import json
import logging
import subprocess
import argparse
import requests
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class SalesforceAPITotalUsageExtractor:
    def __init__(self, client_id: str, username: str, jwt_key_file: str, instance_url: str, org_alias: str, output_dir: str):
        """Initialize the Salesforce API extractor with configuration from command line arguments."""
        # Configuration from command line arguments
        self.client_id = client_id
        self.username = username
        self.jwt_key_file = jwt_key_file
        self.instance_url = instance_url
        self.org_alias = org_alias

        # Output configuration
        self.output_dir = Path(output_dir)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Validate configuration
        self.validate_config()

        # Determine the target date for the query
        self.target_date = datetime.utcnow().date() - timedelta(days=1)

        # Setup logging with the correct date from the start
        self.setup_logging()

        # Will be populated after authentication
        self.access_token = None
        self.api_version = None
        self.actual_instance_url = None

    def setup_logging(self):
        """Setup logging with current timestamp."""
        # Create log file in logs directory with current timestamp initially
        logs_dir = self.output_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        log_date_str = self.target_date.strftime('%Y%m%d')
        self.log_file = logs_dir / f"extract_usage_{log_date_str}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()  # This prints to console
            ]
        )
        self.logger = logging.getLogger(__name__)




    def validate_config(self):
        """Validate required configuration parameters."""
        required_params = {
            'client_id': self.client_id,
            'username': self.username,
            'jwt_key_file': self.jwt_key_file,
            'instance_url': self.instance_url,
            'org_alias': self.org_alias,
            'output_dir': str(self.output_dir)
        }

        missing_params = [param for param, value in required_params.items() if not value]
        if missing_params:
            self.logger.error(f"Missing required parameters: {', '.join(missing_params)}")
            sys.exit(1)

        # Check if JWT key file exists
        if not Path(self.jwt_key_file).exists():
            self.logger.error(f"JWT key file not found: {self.jwt_key_file}")
            sys.exit(1)

        # Check if output directory is writable
        if not os.access(self.output_dir, os.W_OK):
            self.logger.error(f"Output directory is not writable: {self.output_dir}")
            sys.exit(1)

    def run_sf_command(self, command: List[str]) -> Dict:
        """Run a Salesforce CLI command and return JSON result."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout:
                parsed_result = json.loads(result.stdout)

                # Check if SF CLI returned an error in JSON format (status != 0)
                if parsed_result.get('status') != 0:
                    self.logger.error(f"SF CLI command failed: {' '.join(command)}")
                    self.logger.error(f"Error: {parsed_result}")
                    raise Exception(f"SF CLI error: {parsed_result.get('message')}")

                return parsed_result
            return {}

        except subprocess.CalledProcessError as e:
            self.logger.error(f"SF CLI command failed: {' '.join(command)}")
            self.logger.error(f"Error: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse SF CLI JSON output: {e}")
            raise

    def authenticate(self):
        """Authenticate with Salesforce using JWT flow via SF CLI."""
        self.logger.info("Authenticating with Salesforce using JWT flow...")

        auth_command = [
            'sf', 'org', 'login', 'jwt',
            '--client-id', self.client_id,
            '--username', self.username,
            '--jwt-key-file', self.jwt_key_file,
            '--instance-url', self.instance_url,
            '--alias', self.org_alias,
            '--json'
        ]

        try:
            # Authenticate
            self.run_sf_command(auth_command)
            self.logger.info("JWT authentication successful")

            # Get org details
            self.logger.info("Retrieving org information...")
            org_info = self.run_sf_command([
                'sf', 'org', 'display',
                '--target-org', self.org_alias,
                '--json'
            ])

            result = org_info.get('result', {})
            self.access_token = result.get('accessToken')
            self.api_version = result.get('apiVersion')
            self.actual_instance_url = result.get('instanceUrl')

            if not all([self.access_token, self.api_version, self.actual_instance_url]):
                raise Exception("Failed to extract required org information")

            self.logger.info(f"Salesforce org version: v{self.api_version}")
            self.logger.info("Authentication completed successfully")

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise

    def query_eventlog_metadata(self) -> List[Dict]:
        """Query EventLogFile metadata using SF CLI."""
        # Use the pre-calculated target date for the query
        start_date = f"{self.target_date}T00:00:00.000Z"
        end_date = f"{self.target_date + timedelta(days=1)}T00:00:00.000Z"

        self.logger.info(f"Querying Event Log Files for date range: {start_date} to {end_date}")

        soql_query = (
            "SELECT Id, EventType, LogDate "
            "FROM EventLogFile "
            "WHERE EventType = 'ApiTotalUsage' "
            "AND Interval = 'Daily' "
            f"AND LogDate >= {start_date} "
            f"AND LogDate < {end_date}"
        )

        try:
            query_result = self.run_sf_command([
                'sf', 'data', 'query',
                '--query', soql_query,
                '--target-org', self.org_alias,
                '--result-format', 'json'
            ])

            result = query_result.get('result', {})
            records = result.get('records', [])

            self.logger.info(f"Found {len(records)} EventLogFile record(s)")
            return records

        except Exception as e:
            self.logger.error(f"Failed to query EventLogFile metadata: {e}")
            raise

    def stream_csv_to_file(self, log_id: str, output_file: Path) -> int:
        """Stream CSV data directly to file and return record count."""
        try:
            download_url = f"{self.actual_instance_url}/services/data/v{self.api_version}/sobjects/EventLogFile/{log_id}/LogFile"

            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }

            response = requests.get(download_url, headers=headers, stream=True, timeout=600)
            response.raise_for_status()

            # Get file size and calculate optimal chunk size
            content_length = int(response.headers.get('content-length', 0))
            chunk_size = min(max(1024 * 1024, content_length // 100), 2 * 1024 * 1024)

            if content_length > 0:
                self.logger.info(f"File size: {content_length:,} bytes, using chunk size: {chunk_size:,}")

            line_count = 0

            # Write as binary file for maximum efficiency
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=False):
                    if chunk:
                        f.write(chunk)
                        # Count newlines efficiently on bytes
                        line_count += chunk.count(b'\n')

            # Return total records (subtract 1 for header line)
            return max(0, line_count - 1)

        except requests.RequestException as e:
            self.logger.error(f"Failed to download CSV for EventLogFile {log_id}: {e}")
            raise
        except IOError as e:
            self.logger.error(f"Failed to write CSV file {output_file}: {e}")
            raise


    def process_eventlog_files(self, records: List[Dict]):
        """Process each EventLogFile record and save CSV data using streaming."""

        for record in records:
            log_id = record['Id']
            log_date = record['LogDate']

            self.logger.info(f"Processing EventLogFile: {log_id} (Date: {log_date})")

            # Create filename with date and EventLogFile ID in output subdirectory
            date_timestamp = ''.join(filter(str.isdigit, log_date))[:8]
            output_subdir = self.output_dir / "output"
            output_subdir.mkdir(exist_ok=True)
            csv_filename = output_subdir / f"ApiTotalUsage_{date_timestamp}_{log_id}.csv"

            # Stream CSV data directly to file
            self.logger.info(f"Streaming CSV data for EventLogFile: {log_id}")
            try:
                total_records = self.stream_csv_to_file(log_id, csv_filename)

                self.logger.info(f"Saved complete ApiTotalUsage file with {total_records} total API calls")
                self.logger.info(f"Complete API usage data saved to: {csv_filename}")

                # Log and show CSV file creation
                self.logger.info(f"CSV file created: {csv_filename}")
                print(f"CSV file created: {csv_filename}")

            except Exception as e:
                self.logger.error(f"Failed to process EventLogFile {log_id}: {e}")
                raise

    def run(self):
        """Main execution method."""
        try:
            self.logger.info("Starting API Total Usage extraction...")

            # Authenticate with Salesforce using SF CLI
            self.authenticate()

            # Query EventLogFile metadata using SF CLI
            records = self.query_eventlog_metadata()

            # Always print the log file path for user reference
            print(f"Log file for date {self.target_date.strftime('%Y-%m-%d')}: {self.log_file}")

            if not records:
                self.logger.info("No EventLogFile records found for the specified date range. Exiting.")
                return

            # Log extraction details
            self.logger.info("Starting API Total Usage extraction with EventLog data...")
            self.logger.info(f"Output directory: {self.output_dir}")

            # Process each EventLogFile
            self.process_eventlog_files(records)

            # Success summary
            self.logger.info("SUCCESS: API Total Usage extraction completed!")
            self.logger.info("Extraction completed successfully!")

        except Exception as e:
            self.logger.error(f"FAILURE: API Total Usage extraction failed! {e}")
            print(f"\nFAILURE: API Total Usage extraction failed!")
            print(f"Check log file for details: {self.log_file}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Extract Salesforce API Total Usage data from Event Log Files')
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument('--client-id', required=True, help='Salesforce Connected App Client ID')
    required_args.add_argument('--username', required=True, help='Salesforce username')
    required_args.add_argument('--jwt-key-file', required=True, help='Path to JWT private key file')
    required_args.add_argument('--instance-url', required=True, help='Salesforce instance my domain URL')
    required_args.add_argument('--org-alias', required=True, help='Org alias for Salesforce CLI')
    required_args.add_argument('--output-dir', required=True, help='Output directory for CSV files')

    args = parser.parse_args()

    extractor = SalesforceAPITotalUsageExtractor(
        args.client_id,
        args.username,
        args.jwt_key_file,
        args.instance_url,
        args.org_alias,
        args.output_dir
    )
    extractor.run()


if __name__ == "__main__":
    main()
