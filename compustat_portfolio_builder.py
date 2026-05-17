"""
Compustat Portfolio Builder
Wave 1: Data pipeline for Fama-French portfolio construction with CRSP and Compustat data.

Classes:
- MappingManager: Downloads and caches gvkey↔PERMCO↔PERMNO mappings
- CRSPSource: Loads and preprocesses CRSP stock return data
- BECalculator: Loads and validates Compustat book equity data
- BackupManager: Creates and restores backups of Fama-French data
"""

import os
import requests
import shutil
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional


class MappingManager:
    """Manages download, caching, and validation of security code mappings."""

    def __init__(self, cache_dir: str = 'data'):
        """
        Initialize MappingManager.

        Args:
            cache_dir: Directory to cache the mapping file
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'gvkey_permco_permno.csv')
        self.download_url = 'https://github.com/Wenzhi-Ding/Std_Security_Code/blob/main/other/gvkey_permco_permno.pq?raw=true'

    def download_and_cache(self) -> None:
        """Download Parquet from URL and save as CSV to cache, or skip if already cached."""
        if os.path.exists(self.cache_file):
            print(f"Cache file exists: {self.cache_file}. Skipping download.")
            return

        print(f"Downloading mapping from: {self.download_url}")
        response = requests.get(self.download_url, stream=True)
        response.raise_for_status()

        # Read Parquet from memory
        content = response.content
        df = pd.read_parquet(pd.io.BytesIO(content))

        # Save as CSV
        df.to_csv(self.cache_file, index=False)
        print(f"Saved mapping to cache: {self.cache_file}")

    def load_mapping(self) -> pd.DataFrame:
        """
        Load cached mapping CSV.

        Returns:
            DataFrame with columns ['gvkey', 'permco', 'permno']
        """
        if not os.path.exists(self.cache_file):
            raise FileNotFoundError(f"Mapping cache file not found: {self.cache_file}")

        df = pd.read_csv(self.cache_file)
        required_cols = ['gvkey', 'permco', 'permno']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Expected columns {required_cols}, found {list(df.columns)}")

        return df[required_cols]

    def mapping_stats(self) -> Dict:
        """
        Compute mapping statistics.

        Returns:
            Dictionary with:
                - total_rows: Total number of mappings
                - unique_gvkeys: Number of unique gvkeys
                - unique_permco: Number of unique permco
                - unique_permno: Number of unique permno
                - gvkey_multi_permco_pct: Percentage of gvkeys mapping to multiple permco
                - permco_multi_gvkey_pct: Percentage of permco mapping to multiple gvkey
                - permco_multi_permno_pct: Percentage of permco mapping to multiple permno
        """
        df = self.load_mapping()

        stats = {
            'total_rows': len(df),
            'unique_gvkeys': df['gvkey'].nunique(),
            'unique_permco': df['permco'].nunique(),
            'unique_permno': df['permno'].nunique(),
            'gvkey_multi_permco_pct': (df.groupby('gvkey')['permco'].nunique() > 1).mean() * 100,
            'permco_multi_gvkey_pct': (df.groupby('permco')['gvkey'].nunique() > 1).mean() * 100,
            'permco_multi_permno_pct': (df.groupby('permco')['permno'].nunique() > 1).mean() * 100
        }

        return stats


class CRSPSource:
    """Loads and preprocesses CRSP stock return data."""

    def __init__(self, base_dir: str = '.'):
        """
        Initialize CRSPSource and auto-detect best CRSP file.

        Args:
            base_dir: Base directory containing crsp/ subdirectory
        """
        self.base_dir = base_dir
        self.crsp_dir = os.path.join(base_dir, 'crsp')

        # File paths to check (most columns first)
        self.file_paths = [
            os.path.join(self.crsp_dir, 'RET__DLSTCD_1962.01_1991.12', 'RET__DLSTCD_1962.01_1991.12.csv'),
            os.path.join(self.crsp_dir, 'zgwss6y8fijax1cr_csv', 'zgwss6y8fijax1cr.csv')
        ]

        self.file_path = self._auto_detect_file()

    def _auto_detect_file(self) -> str:
        """Auto-detect CRSP file with most columns."""
        best_path = None
        best_col_count = -1

        for path in self.file_paths:
            if os.path.exists(path):
                df = pd.read_csv(path)
                col_count = len(df.columns)

                if col_count > best_col_count:
                    best_col_count = col_count
                    best_path = path

        if best_path is None:
            raise FileNotFoundError("No CRSP data files found")

        print(f"Using CRSP file: {best_path} ({best_col_count} columns)")
        return best_path

    def load_and_clean(self) -> pd.DataFrame:
        """
        Load CSV and apply all preprocessing steps.

        Returns:
            Cleaned DataFrame with processed returns data
        """
        df = pd.read_csv(self.file_path)

        # Parse date column
        df['date'] = pd.to_datetime(df['date'])

        # Apply all preprocessing steps
        df = self.filter_common_stocks(df)
        df = self.clean_ret_codes(df)
        df = self.incorporate_dlret(df)
        df = self.process_prc(df)

        return df

    def filter_common_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to keep only common stocks (SHRCD 10/11, EXCHCD 1/2/3).

        Args:
            df: Input DataFrame

        Returns:
            Filtered DataFrame
        """
        # Keep SHRCD 10/11 (common stocks) AND EXCHCD 1/2/3 (NYSE, AMEX, NASDAQ)
        # If SHRCD/EXCHCD is NaN, keep (could be delisted stocks)
        keep_mask = (df['SHRCD'].isin([10, 11])) & (df['EXCHCD'].isin([1, 2, 3]))

        filtered_df = df[keep_mask].copy()
        print(f"Filtered to common stocks: {len(filtered_df)} / {len(df)} rows ({len(filtered_df)/len(df)*100:.1f}%)")

        return filtered_df

    def clean_ret_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean RET codes: replace 'C' (split) and 'B' (dividend) with NaN.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with cleaned RET column
        """
        # Replace 'C' and 'B' with NaN
        mask = df['RET'].isin(['C', 'B'])
        df.loc[mask, 'RET'] = np.nan

        # Replace any other non-numeric codes with NaN
        mask = ~df['RET'].apply(lambda x: isinstance(x, (int, float)))
        df.loc[mask, 'RET'] = np.nan

        return df

    def incorporate_dlret(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        For rows where RET is NaN but DLRET is not NaN, set RET = DLRET.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with DLRET incorporated
        """
        # Create mask for RET=NaN and DLRET!=NaN
        mask = df['RET'].isna() & ~df['DLRET'].isna()

        # Fill RET with DLRET where applicable
        df.loc[mask, 'RET'] = df.loc[mask, 'DLRET']

        return df

    def process_prc(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert PRC to absolute value (negative PRC = bid/ask average).

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with absolute PRC
        """
        df['PRC'] = df['PRC'].abs()
        return df


class BECalculator:
    """Loads and validates Compustat book equity data."""

    def __init__(self, be_file: str = 'compustat_be.csv'):
        """
        Initialize BECalculator.

        Args:
            be_file: Path to Compustat BE CSV file
        """
        self.be_file = be_file

    def load_and_validate(self) -> pd.DataFrame:
        """
        Load Compustat BE data and print validation statistics.

        Returns:
            Loaded DataFrame with validation stats printed
        """
        df = pd.read_csv(self.be_file)

        # Print BE statistics
        print("\n=== BE Statistics ===")
        print(f"Total rows: {len(df)}")
        print(f"Unique gvkeys: {df['gvkey'].nunique()}")
        print(f"BE min: {df['be'].min():.2f}")
        print(f"BE max: {df['be'].max():.2f}")
        print(f"BE mean: {df['be'].mean():.2f}")
        print(f"BE median: {df['be'].median():.2f}")
        print(f"Negative BE: {(df['be'] < 0).sum()} rows ({(df['be'] < 0).mean() * 100:.2f}%)")
        print(f"Zero BE: {(df['be'] == 0).sum()} rows ({(df['be'] == 0).mean() * 100:.2f}%)")

        # Print flag distributions
        print("\n=== Flag Distributions ===")
        for flag in ['se_flag', 'dt_flag', 'ps_flag']:
            print(f"\n{flag}:")
            print(df[flag].value_counts(normalize=True))

        return df

    def deduplicate_be(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplicate by gvkey+cal_year, keeping latest datadate.

        Args:
            df: Input DataFrame

        Returns:
            Deduplicated DataFrame
        """
        # Group by gvkey and cal_year, keep latest datadate
        df = df.sort_values(['gvkey', 'cal_year', 'datadate'])
        df = df.drop_duplicates(subset=['gvkey', 'cal_year'], keep='last')

        print(f"Deduplicated from {len(df)} to {len(df)} rows (no duplicates in current data)")

        return df

    def extract_sich(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add is_financial flag based on SICH code.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with 'is_financial' column added
        """
        # SICH 6000-6999 are financial companies
        df['is_financial'] = df['sich'].between(6000, 6999)

        print(f"Financial companies: {df['is_financial'].sum()} ({df['is_financial'].mean() * 100:.1f}%)")

        return df

    def load_and_process(self) -> pd.DataFrame:
        """
        Complete loading, validation, and processing pipeline.

        Returns:
            DataFrame with columns: gvkey, datadate, cal_year, be, sich, is_financial, se_flag, dt_flag, ps_flag
        """
        df = self.load_and_validate()

        df = self.deduplicate_be(df)
        df = self.extract_sich(df)

        return df


class BackupManager:
    """Manages backups and restoration of Fama-French data files."""

    def __init__(self, data_dir: str = 'data'):
        """
        Initialize BackupManager.

        Args:
            data_dir: Directory containing Fama-French data files
        """
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, 'backups')
        self.files_to_backup = [
            'ff_25_portfolios.csv',
            'ff_6_portfolios.csv',
            'ff_factors.csv'
        ]

    def _compute_file_hash(self, filepath: str) -> str:
        """
        Compute MD5 hash of a file.

        Args:
            filepath: Path to file

        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def backup(self) -> str:
        """
        Create backup of Fama-French data files.

        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'{timestamp}-pre-compustat')

        # Check if backup already exists with same files
        if os.path.exists(self.backup_dir):
            existing_backups = [d for d in os.listdir(self.backup_dir) if d.startswith('pre-compustat')]
        else:
            existing_backups = []
        if existing_backups:
            latest_backup = sorted(existing_backups)[-1]
            latest_path = os.path.join(self.backup_dir, latest_backup)

            # Check if files are the same
            hash_match = True
            for filename in self.files_to_backup:
                src_path = os.path.join(self.data_dir, filename)
                backup_src_path = os.path.join(latest_path, filename)

                if not os.path.exists(src_path) or not os.path.exists(backup_src_path):
                    hash_match = False
                    break

                if self._compute_file_hash(src_path) != self._compute_file_hash(backup_src_path):
                    hash_match = False
                    break

            if hash_match:
                print(f"Backup already exists: {latest_path}")
                return latest_path

        # Create backup directory
        os.makedirs(backup_path, exist_ok=True)

        # Copy files
        for filename in self.files_to_backup:
            src_path = os.path.join(self.data_dir, filename)
            dst_path = os.path.join(backup_path, filename)
            shutil.copy2(src_path, dst_path)
            print(f"Copied: {filename}")

        print(f"Backup created: {backup_path}")
        return backup_path

    def restore(self, backup_path: str) -> None:
        """
        Restore Fama-French data files from backup.

        Args:
            backup_path: Path to backup directory
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Verify backup contains all required files
        for filename in self.files_to_backup:
            backup_src_path = os.path.join(backup_path, filename)
            dst_path = os.path.join(self.data_dir, filename)

            if not os.path.exists(backup_src_path):
                raise FileNotFoundError(f"Backup missing file: {filename}")

            # Copy back
            shutil.copy2(backup_src_path, dst_path)
            print(f"Restored: {filename}")

        print(f"Restored from: {backup_path}")