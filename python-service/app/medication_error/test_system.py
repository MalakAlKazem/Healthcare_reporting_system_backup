"""
Complete Test File for Medication Error System
Tests all components and generates all 7 charts
"""

import sys
from pathlib import Path

# Add module path
sys.path.insert(0, str(Path(__file__).parent))

from data_processor import MedicationErrorProcessor
from statistics import MedicationErrorStatistics
from history_manager import MedicationErrorHistory
from chart_generator import MedicationErrorCharts

from loguru import logger


def test_complete_system():
    """Test the complete medication error system"""
    
    print("=" * 70)
    print("🧪 MEDICATION ERROR SYSTEM - COMPLETE TEST")
    print("=" * 70)
    
    # File path - adjust to your location
    excel_file = 'sample-data/medicationError-Q3.xlsx'
    
    # Check if file exists
    if not Path(excel_file).exists():
        # Try alternative paths
        alternative_paths = [
            '../sample-data/medicationError-Q3.xlsx',
            'medicationError-Q3.xlsx',
            '/mnt/user-data/uploads/medicationError-Q3.xlsx'
        ]
        
        for alt_path in alternative_paths:
            if Path(alt_path).exists():
                excel_file = alt_path
                break
        else:
            print(f"❌ File not found: {excel_file}")
            print(f"   Tried: {alternative_paths}")
            return False
    
    print(f"\n📂 Using file: {excel_file}")
    
    # ========================================================================
    # STEP 1: PROCESS DATA
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 1: DATA PROCESSING")
    print("=" * 70)
    
    processor = MedicationErrorProcessor()
    result = processor.process_file(excel_file)
    
    print(f"\n✅ Data Processed:")
    print(f"   Quarter: {result['quarter']} {result['year']}")
    print(f"   Total Errors: {result['total_errors']}")
    print(f"   Total Doses: {result['total_doses']:,}")
    print(f"   Error Rate: {result['error_rate']}%")
    print(f"   Target: {result['target']}%")
    
    # ========================================================================
    # STEP 2: CALCULATE STATISTICS
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 2: STATISTICS CALCULATION")
    print("=" * 70)
    
    stats_calc = MedicationErrorStatistics()
    stats = stats_calc.calculate_all_statistics(
        result['data'],
        result['total_doses'],
        result['quarter'],
        result['year']
    )
    
    print(f"\n✅ Statistics Calculated:")
    print(f"\n   📊 Chart 3 Data - Error Cycle (Total: {stats['error_cycle']['total']}):")
    for k, v in stats['error_cycle']['counts'].items():
        pct = stats['error_cycle']['percentages'][k]
        print(f"      {k}: {v} ({pct}%)")
    
    print(f"\n   📊 Chart 4 Data - Detected By (Total: {stats['detected_by']['total']}):")
    for k, v in stats['detected_by']['counts'].items():
        pct = stats['detected_by']['percentages'][k]
        print(f"      {k}: {v} ({pct}%)")
    
    print(f"\n   📊 Chart 5 Data - Duty Shift (Total: {stats['duty_shift']['total']}):")
    for k, v in stats['duty_shift']['counts'].items():
        pct = stats['duty_shift']['percentages'][k]
        print(f"      {k}: {v} ({pct}%)")
    
    print(f"\n   📊 Chart 6 Data - Staff Involved (Total: {stats['staff_involved']['total']}):")
    for k, v in stats['staff_involved']['counts'].items():
        pct = stats['staff_involved']['percentages'][k]
        print(f"      {k}: {v} ({pct}%)")
    
    print(f"\n   📊 Chart 7 Data - Error Causes (Total: {stats['error_causes']['total']}):")
    for k, v in list(stats['error_causes']['counts'].items())[:6]:
        pct = stats['error_causes']['percentages'][k]
        print(f"      {k}: {v} ({pct}%)")
    
    # ========================================================================
    # STEP 3: LOAD/SAVE HISTORICAL DATA
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 3: HISTORICAL DATA MANAGEMENT")
    print("=" * 70)
    
    history_mgr = MedicationErrorHistory('storage/medication_error_history.json')
    
    # Save current quarter
    history_mgr.save_quarter(result['quarter'], result['year'], stats)
    
    # Get history for charts
    all_history = history_mgr.get_last_n_quarters(11)
    
    print(f"\n✅ Historical Data:")
    print(f"   Total Quarters: {len(all_history)}")
    print(f"   Last 5 Quarters:")
    for h in all_history[-5:]:
        print(f"      {h['quarter']} {h['year']}: {h['error_rate']}% ({h['total_errors']} errors)")
    
    # ========================================================================
    # STEP 4: GENERATE ALL CHARTS
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 4: CHART GENERATION")
    print("=" * 70)
    
    chart_gen = MedicationErrorCharts(output_dir='output/charts')
    
    print("\n🎨 Generating all 7 charts...")
    charts = chart_gen.generate_all_charts(stats, all_history)
    
    print(f"\n✅ Charts Generated:")
    for chart_name, image_bytes in charts.items():
        # Save to file
        output_path = chart_gen.save_chart(chart_name, image_bytes)
        print(f"   ✓ {chart_name}: {len(image_bytes):,} bytes → {output_path}")
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    
    all_pass = True
    
    # Check total errors = 45
    if stats['summary']['total_errors'] == 45:
        print("   ✅ Total errors = 45")
    else:
        print(f"   ❌ Total errors = {stats['summary']['total_errors']} (expected 45)")
        all_pass = False
    
    # Check all chart totals = 45
    for chart_name, data_key in [
        ('Chart 3', 'error_cycle'),
        ('Chart 4', 'detected_by'),
        ('Chart 5', 'duty_shift'),
        ('Chart 6', 'staff_involved')
    ]:
        total = stats[data_key]['total']
        if total == 45:
            print(f"   ✅ {chart_name} total = 45")
        else:
            print(f"   ❌ {chart_name} total = {total} (expected 45)")
            all_pass = False
    
    # Check all 7 charts generated
    if len(charts) == 7:
        print(f"   ✅ All 7 charts generated")
    else:
        print(f"   ❌ Only {len(charts)} charts generated (expected 7)")
        all_pass = False
    
    # Check error rate
    expected_rate = 0.0104  # 45/431124 * 100
    if abs(stats['summary']['error_rate'] - expected_rate) < 0.0001:
        print(f"   ✅ Error rate = {stats['summary']['error_rate']}%")
    else:
        print(f"   ⚠️  Error rate = {stats['summary']['error_rate']}% (expected ~{expected_rate}%)")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - CHECK ABOVE")
    print("=" * 70)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Data File: {excel_file}")
    print(f"   Quarter: {result['quarter']} {result['year']}")
    print(f"   Total Errors: {stats['summary']['total_errors']}")
    print(f"   Error Rate: {stats['summary']['error_rate']}%")
    print(f"   Charts Generated: {len(charts)}")
    print(f"   Output Directory: output/charts/")
    
    print("\n✨ TEST COMPLETE!")
    
    return all_pass


if __name__ == '__main__':
    success = test_complete_system()
    sys.exit(0 if success else 1)
