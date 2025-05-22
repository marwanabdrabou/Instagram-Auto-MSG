import pandas as pd
import os
import csv
from datetime import datetime
from typing import List, Set
from config import INPUT_DIR, OUTPUT_DIR, RESULTS_FILE

class FileManager:
    @staticmethod
    def load_profiles(file_path: str) -> List[str]:
        """Load Instagram profiles from Excel file"""
        try:
            df = pd.read_excel(file_path)
            
            # Check for required columns
            if 'URL' not in df.columns:
                raise ValueError("Excel file must contain a 'URL' column")
                
            # Clean and validate URLs
            profiles = df["URL"].str.strip().dropna().tolist()
            valid_profiles = [url for url in profiles if url.startswith(('https://www.instagram.com/', 'instagram.com/'))]
            
            if not valid_profiles:
                raise ValueError("No valid Instagram profile URLs found in the file")
                
            return valid_profiles
            
        except Exception as e:
            raise Exception(f"Error loading profiles: {str(e)}")

    @staticmethod
    def load_sent_profiles() -> Set[str]:
        """Load already sent profiles from results file"""
        try:
            if os.path.exists(RESULTS_FILE):
                df = pd.read_csv(RESULTS_FILE)
                return set(df[df['Status'] == 'Success']['Profile URL'].tolist())
            return set()
        except Exception as e:
            print(f"Warning: Could not load sent profiles - {str(e)}")
            return set()

    @staticmethod
    def init_results_file():
        """Initialize results CSV file with headers if it doesn't exist"""
        if not os.path.exists(RESULTS_FILE):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Profile URL', 'Status', 'Message', 'Timestamp', 'Error'])

    @staticmethod
    def record_result(profile_url: str, status: str, message: str, error: str = None):
        """Record a result to the CSV file"""
        try:
            with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    profile_url, 
                    status, 
                    message[:500],  # Truncate long messages
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    str(error)[:200] if error else ''
                ])
        except Exception as e:
            print(f"Error recording result: {str(e)}")

    @staticmethod
    def get_results_df():
        """Load results as a DataFrame"""
        try:
            if os.path.exists(RESULTS_FILE):
                return pd.read_csv(RESULTS_FILE)
            return pd.DataFrame()
        except Exception as e:
            print(f"Error loading results: {str(e)}")
            return pd.DataFrame()