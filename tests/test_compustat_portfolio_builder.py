"""
test_compustat_portfolio_builder.py
TDD tests for compustat_portfolio_builder module
"""

import os
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
import requests
from pathlib import Path

import compustat_portfolio_builder


class TestMappingManager:
    """Tests for MappingManager class."""

    def test_init(self, tmp_path):
        """Test initialization with default and custom cache_dir."""
        manager = compustat_portfolio_builder.MappingManager(cache_dir=str(tmp_path))
        assert manager.cache_dir == str(tmp_path)
        assert manager.cache_file == str(tmp_path / 'gvkey_permco_permno.csv')

    def test_init_custom_cache_dir(self):
        """Test initialization with custom cache directory."""
        custom_dir = '/custom/path'
        manager = compustat_portfolio_builder.MappingManager(cache_dir=custom_dir)
        assert manager.cache_dir == custom_dir

    def test_download_and_cache_skips_existing(self, tmp_path, monkeypatch):
        """Test download_and_cache skips download if cache file exists."""
        # Create existing cache file
        cache_file = tmp_path / 'gvkey_permco_permno.csv'
        cache_file.write_text('gvkey,permco,permno\n1,1,1\n')

        manager = compustat_portfolio_builder.MappingManager(cache_dir=str(tmp_path))

        # Mock requests.get to avoid actual download
        original_get = requests.get
        def mock_get(url, stream=False, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    pass
                def __iter__(self):
                    return iter([])
            return MockResponse()

        monkeypatch.setattr('requests.get', mock_get)

        # Should not raise and should skip download
        manager.download_and_cache()

        # File should still exist
        assert cache_file.exists()

    @pytest.mark.skip("Requires actual network access")
    def test_download_and_cache_downloads_new(self):
        """Test download_and_cache downloads new file when cache doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = compustat_portfolio_builder.MappingManager(cache_dir=tmp_dir)
            manager.download_and_cache()
            assert manager.cache_file.exists()

    def test_load_mapping_file_not_found(self, tmp_path):
        """Test load_mapping raises FileNotFoundError when file doesn't exist."""
        manager = compustat_portfolio_builder.MappingManager(cache_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            manager.load_mapping()

    def test_load_mapping_invalid_columns(self, tmp_path):
        """Test load_mapping raises ValueError when columns are missing."""
        cache_file = tmp_path / 'gvkey_permco_permno.csv'
        cache_file.write_text('id,code,value\n1,1,1\n')

        manager = compustat_portfolio_builder.MappingManager(cache_dir=str(tmp_path))
        with pytest.raises(ValueError):
            manager.load_mapping()

    def test_load_mapping_valid_columns(self, tmp_path):
        """Test load_mapping returns correct DataFrame with required columns."""
        cache_file = tmp_path / 'gvkey_permco_permno.csv'
        cache_file.write_text('gvkey,permco,permno\n1,1,1\n2,2,2\n')

        manager = compustat_portfolio_builder.MappingManager(cache_dir=str(tmp_path))
        df = manager.load_mapping()

        assert list(df.columns) == ['gvkey', 'permco', 'permno']
        assert len(df) == 2


class TestCRSPSource:
    """Tests for CRSPSource class."""

    def test_init_auto_detects_file(self, tmp_path):
        """Test initialization auto-detects best CRSP file."""
        # Create test CRSP files
        crsp_dir = tmp_path / 'crsp'
        crsp_dir.mkdir()

        # Main file with more columns
        main_dir = crsp_dir / 'RET__DLSTCD_1962.01_1991.12'
        main_dir.mkdir()
        (main_dir / 'RET__DLSTCD_1962.01_1991.12.csv').write_text(
            'PERMNO,date,SHRCD,EXCHCD,DLRET,PRC\n'
            '12345,2020-01-01,10,1,\n'
        )

        # Secondary file with fewer columns
        sec_dir = crsp_dir / 'zgwss6y8fijax1cr_csv'
        sec_dir.mkdir()
        (sec_dir / 'zgwss6y8fijax1cr.csv').write_text(
            'PERMNO,date,SHRCD\n'
            '12345,2020-01-01,10\n'
        )

        source = compustat_portfolio_builder.CRSPSource(base_dir=str(tmp_path))
        assert source.file_path == str(main_dir / 'RET__DLSTCD_1962.01_1991.12.csv')

    def test_init_no_files_found(self, tmp_path):
        """Test initialization raises FileNotFoundError when no CRSP files exist."""
        # Create temp directory without CRSP files
        with pytest.raises(FileNotFoundError):
            compustat_portfolio_builder.CRSPSource(base_dir=str(tmp_path))

    def test_filter_common_stocks(self):
        """Test filter_common_stocks keeps common stocks (SHRCD 10/11 AND EXCHCD 1/2/3)."""
        df = pd.DataFrame({
            'SHRCD': [10, 11, 20, 30, np.nan, np.nan],
            'EXCHCD': [1, 2, 3, 4, np.nan, np.nan],
            'PERMNO': [1, 2, 3, 4, 5, 6]
        })

        filtered = compustat_portfolio_builder.CRSPSource().filter_common_stocks(df)

        # Keep SHRCD 10/11 AND EXCHCD 1/2/3
        # Rows 0, 1 should remain (SHRCD 10/11, EXCHCD 1/2)
        # Rows 2, 3 should be filtered out (SHRCD 20, 30)
        # Rows 4, 5 should be filtered out (SHRCD NaN)
        assert len(filtered) == 2
        assert list(filtered['PERMNO']) == [1, 2]

    def test_clean_ret_codes_replaces_c_b(self):
        """Test clean_ret_codes replaces 'C' and 'B' with NaN."""
        df = pd.DataFrame({
            'RET': [0.01, 'C', 'B', 0.02, 'X']
        })

        cleaned = compustat_portfolio_builder.CRSPSource().clean_ret_codes(df)

        assert pd.isna(cleaned['RET'][1])  # 'C' replaced with NaN
        assert pd.isna(cleaned['RET'][2])  # 'B' replaced with NaN
        assert pd.isna(cleaned['RET'][4])  # 'X' replaced with NaN
        assert cleaned['RET'][0] == 0.01
        assert cleaned['RET'][3] == 0.02

    def test_incorporate_dlret(self):
        """Test incorporate_dlret fills RET with DLRET when RET is NaN."""
        df = pd.DataFrame({
            'RET': [0.01, np.nan, 0.02, np.nan],
            'DLRET': [np.nan, 0.03, np.nan, 0.04]
        })

        result = compustat_portfolio_builder.CRSPSource().incorporate_dlret(df)

        assert result['RET'][0] == 0.01  # RET not NaN, unchanged
        assert result['RET'][1] == 0.03  # RET NaN, filled with DLRET
        assert result['RET'][2] == 0.02  # RET not NaN, unchanged
        assert result['RET'][3] == 0.04  # RET NaN, filled with DLRET

    def test_process_prc_abs(self):
        """Test process_prc converts PRC to absolute value."""
        df = pd.DataFrame({
            'PRC': [-1.5, 2.3, -0.5, 0.0]
        })

        result = compustat_portfolio_builder.CRSPSource().process_prc(df)

        assert list(result['PRC']) == [1.5, 2.3, 0.5, 0.0]

    @pytest.fixture
    def sample_crsp_data(self, tmp_path):
        """Create sample CRSP data for testing."""
        crsp_dir = tmp_path / 'crsp'
        crsp_dir.mkdir()

        # Create main file with all required columns
        main_dir = crsp_dir / 'RET__DLSTCD_1962.01_1991.12'
        main_dir.mkdir()
        (main_dir / 'RET__DLSTCD_1962.01_1991.12.csv').write_text(
            'PERMNO,date,SHRCD,EXCHCD,PERMCO,DLRET,PRC,RET,SHROUT\n'
            '10001,2020-01-01,10,1,100,0.02,-1.5,0.01,1000000\n'
            '10002,2020-01-02,11,2,101,0.03,2.3,0.02,800000\n'
            '10003,2020-01-03,10,3,102,,0.5,-0.01,500000\n'
            '10004,2020-01-04,20,4,103,0.05,-0.8,C,1200000\n'
        )

        return str(tmp_path)

    def test_load_and_clean(self, sample_crsp_data):
        """Test load_and_clean applies all preprocessing steps."""
        source = compustat_portfolio_builder.CRSPSource(base_dir=sample_crsp_data)
        df = source.load_and_clean()

        # Check date parsing
        assert isinstance(df['date'].iloc[0], pd.Timestamp)

        # Check filtering (keep SHRCD 10/11 AND EXCHCD 1/2/3)
        # Row 0: SHRCD=10, EXCHCD=1 -> keep
        # Row 1: SHRCD=11, EXCHCD=2 -> keep
        # Row 2: SHRCD=10, EXCHCD=3 -> keep
        # Row 3: SHRCD=20, EXCHCD=4 -> filter out
        assert len(df) == 3  # Only rows 0, 1, 2 should remain

        # Check RET cleaning - row 3 (original index 3) has 'C' in RET
        # But row 3 was filtered out, so we need to check row 2 which has non-numeric DLRET
        assert pd.isna(df['RET'].iloc[2])  # Third row has DLRET filled in

        # Check PRC absolute value
        assert df['PRC'].iloc[0] == 1.5  # Negative PRC made positive


class TestBECalculator:
    """Tests for BECalculator class."""

    def test_init(self):
        """Test initialization with default and custom file."""
        calc = compustat_portfolio_builder.BECalculator()
        assert calc.be_file == 'compustat_be.csv'

        custom_file = '/custom/path/be.csv'
        calc = compustat_portfolio_builder.BECalculator(be_file=custom_file)
        assert calc.be_file == custom_file

    def test_deduplicate_be_no_duplicates(self):
        """Test deduplicate_be keeps data when no duplicates exist."""
        df = pd.DataFrame({
            'gvkey': [1, 2, 3, 2],
            'cal_year': [1990, 1990, 1990, 1990],
            'datadate': ['1990-01-01', '1990-01-01', '1990-01-01', '1990-01-01'],
            'be': [100, 200, 300, 400]
        })

        result = compustat_portfolio_builder.BECalculator().deduplicate_be(df)

        # Should keep 3 rows (gvkey 1, 2, 3) - gvkey 2's last row kept
        assert len(result) == 3

    def test_extract_sich_flag(self):
        """Test extract_sich adds is_financial flag."""
        df = pd.DataFrame({
            'sich': [1000, 6000, 6500, 7000, 8000],
            'be': [100, 200, 300, 400, 500]
        })

        result = compustat_portfolio_builder.BECalculator().extract_sich(df)

        assert 'is_financial' in result.columns
        # SICH 6000-6999 are financial companies
        # 6500 is in range, 7000 is not
        assert result['is_financial'].tolist() == [False, True, True, False, False]

    def test_extract_sich_range(self):
        """Test extract_sich correctly identifies financial companies (SICH 6000-6999)."""
        df = pd.DataFrame({
            'sich': [5999, 6000, 6999, 7000],
            'be': [100, 200, 300, 400]
        })

        result = compustat_portfolio_builder.BECalculator().extract_sich(df)

        assert result['is_financial'].tolist() == [False, True, True, False]


class TestBackupManager:
    """Tests for BackupManager class."""

    def test_init(self):
        """Test initialization with default and custom directories."""
        manager = compustat_portfolio_builder.BackupManager()
        assert manager.data_dir == 'data'
        # Use os.path.join for platform-independent path comparison
        expected_backup_dir = os.path.join('data', 'backups')
        assert manager.backup_dir == expected_backup_dir

        custom_dir = '/custom/path'
        manager = compustat_portfolio_builder.BackupManager(data_dir=custom_dir)
        assert manager.data_dir == custom_dir

    def test_compute_file_hash(self):
        """Test _compute_file_hash produces consistent MD5 hashes."""
        manager = compustat_portfolio_builder.BackupManager()

        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('test content')
            filepath = f.name

        try:
            hash1 = manager._compute_file_hash(filepath)
            hash2 = manager._compute_file_hash(filepath)
            assert hash1 == hash2
        finally:
            os.unlink(filepath)

    def test_compute_file_hash_different(self):
        """Test _compute_file_hash produces different hashes for different content."""
        manager = compustat_portfolio_builder.BackupManager()

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write('content 1')
            filepath1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write('content 2')
            filepath2 = f2.name

        try:
            hash1 = manager._compute_file_hash(filepath1)
            hash2 = manager._compute_file_hash(filepath2)
            assert hash1 != hash2
        finally:
            os.unlink(filepath1)
            os.unlink(filepath2)

    def test_backup_creates_directory(self, tmp_path, monkeypatch):
        """Test backup creates backup directory structure."""
        # Create source data files
        for filename in ['ff_25_portfolios.csv', 'ff_6_portfolios.csv', 'ff_factors.csv']:
            filepath = tmp_path / 'data' / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(f'header\ncol1,col2\n1,2\n')

        # Mock requests.get to avoid actual download
        original_get = requests.get
        def mock_get(url, stream=False, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    pass
                def __iter__(self):
                    return iter([])
            return MockResponse()

        monkeypatch.setattr('requests.get', mock_get)

        # Create mapping manager to avoid download
        mapping_mgr = compustat_portfolio_builder.MappingManager(cache_dir=str(tmp_path / 'data'))
        Path(mapping_mgr.cache_file).write_text('gvkey,permco,permno\n1,1,1\n')

        manager = compustat_portfolio_builder.BackupManager(data_dir=str(tmp_path / 'data'))
        backup_path = manager.backup()

        # Check backup directory was created
        assert os.path.exists(backup_path)
        assert backup_path.endswith('-pre-compustat')

        # Check backup contains all files
        for filename in ['ff_25_portfolios.csv', 'ff_6_portfolios.csv', 'ff_factors.csv']:
            backup_file = os.path.join(backup_path, filename)
            assert os.path.exists(backup_file), f"File {filename} missing in backup"

    def test_backup_skips_if_same(self, tmp_path, monkeypatch):
        """Test backup skips if backup with same files already exists."""
        # Create source data files
        for filename in ['ff_25_portfolios.csv', 'ff_6_portfolios.csv', 'ff_factors.csv']:
            filepath = tmp_path / 'data' / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(f'header\ncol1,col2\n1,2\n')

        # Mock requests.get
        original_get = requests.get
        def mock_get(url, stream=False, **kwargs):
            class MockResponse:
                def raise_for_status(self):
                    pass
                def __iter__(self):
                    return iter([])
            return MockResponse()

        monkeypatch.setattr('requests.get', mock_get)

        # Create mapping manager
        mapping_mgr = compustat_portfolio_builder.MappingManager(cache_dir=str(tmp_path / 'data'))
        Path(mapping_mgr.cache_file).write_text('gvkey,permco,permno\n1,1,1\n')

        manager = compustat_portfolio_builder.BackupManager(data_dir=str(tmp_path / 'data'))

        # First backup
        backup_path1 = manager.backup()

        # Second backup - should skip
        backup_path2 = manager.backup()

        # Should return same path
        assert backup_path1 == backup_path2

    def test_restore_file_not_found(self, tmp_path):
        """Test restore raises FileNotFoundError when backup doesn't exist."""
        manager = compustat_portfolio_builder.BackupManager(data_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            manager.restore('/nonexistent/backup')

    def test_restore_creates_missing_files(self, tmp_path):
        """Test restore copies files from backup to data directory."""
        # Create backup directory with files
        backup_dir = tmp_path / 'backup'
        backup_dir.mkdir()
        for filename in ['ff_25_portfolios.csv', 'ff_6_portfolios.csv', 'ff_factors.csv']:
            filepath = backup_dir / filename
            filepath.write_text(f'backup-{filename}\n')

        # Create data directory
        data_dir = tmp_path / 'data'
        data_dir.mkdir()

        manager = compustat_portfolio_builder.BackupManager(data_dir=str(data_dir))
        manager.restore(str(backup_dir))

        # Check files were restored
        for filename in ['ff_25_portfolios.csv', 'ff_6_portfolios.csv', 'ff_factors.csv']:
            restored_path = data_dir / filename
            assert restored_path.exists()
            assert restored_path.read_text().startswith('backup-')