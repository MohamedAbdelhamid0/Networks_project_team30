import pandas as pd
import os
import glob
from collections import defaultdict

# --- CONFIGURATION ---
# IMPORTANT: This must match the total number of unique packets your client sent per run.
# We are assuming the recommended value of 200 messages (NUM_MESSAGES = 200, BATCH_SIZE = 1).
TOTAL_SENT_PACKETS = 250
# ---------------------

def analyze_single_run(file_path):
    """Reads one sorted CSV and calculates all required metrics."""
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # --- 1. Total Counts ---
    total_received = len(df)
    
    # Unique packets are those that are NOT duplicates (duplicate_flag == 0)
    df_unique = df[df['duplicate_flag'] == 0]
    total_unique_received = len(df_unique)
    
    # Duplicates are those with duplicate_flag == 1
    total_duplicates = df['duplicate_flag'].sum()
    
    # Gaps are those with gap_flag == 1
    total_gaps = df['gap_flag'].sum()
    
    # --- 2. Rate Calculations ---
    # Loss Rate: Packets Sent - Unique Packets Received
    total_lost = TOTAL_SENT_PACKETS - total_unique_received
    loss_rate = (total_lost / TOTAL_SENT_PACKETS) * 100
    
    # Duplicate Rate: Duplicates Received / Total Packets Sent
    duplicate_rate = (total_duplicates / TOTAL_SENT_PACKETS) * 100
    
    # Gap Rate: Gaps Detected / Total Unique Packets Received (to account for packets that never arrived)
    # Note: If no packets arrived, total_unique_received is 0, so avoid division by zero
    gap_rate = (total_gaps / total_unique_received) * 100 if total_unique_received > 0 else 0.0

    # --- 3. Latency Metrics (using the 'network_delay_s' column) ---
    delay_stats = {
        'min': df_unique['network_delay_s'].min() * 1000,   # convert to ms
        'median': df_unique['network_delay_s'].median() * 1000, # convert to ms
        'max': df_unique['network_delay_s'].max() * 1000    # convert to ms
    }
    
    return {
        'total_sent': TOTAL_SENT_PACKETS,
        'total_unique_recv': total_unique_received,
        'total_lost': total_lost,
        'total_duplicates': total_duplicates,
        'total_gaps': total_gaps,
        'loss_rate': loss_rate,
        'duplicate_rate': duplicate_rate,
        'gap_rate': gap_rate,
        'delay_min_ms': delay_stats['min'],
        'delay_median_ms': delay_stats['median'],
        'delay_max_ms': delay_stats['max']
    }

def aggregate_and_print_results(all_results):
    """Aggregates the results by scenario and prints a summary table."""
    
    scenario_metrics = defaultdict(lambda: defaultdict(list))
    
    for scenario, results in all_results.items():
        for result in results:
            if result:
                for key, value in result.items():
                    scenario_metrics[scenario][key].append(value)

    # Prepare final summary table data
    summary_data = []
    
    for scenario in ['baseline', 'loss', 'delay']:
        metrics = scenario_metrics[scenario]
        if not metrics:
            summary_data.append({
                'Scenario': scenario.upper(),
                'Loss Rate (%)': 'N/A',
                'Duplicate Rate (%)': 'N/A',
                'Gap Rate (%)': 'N/A',
                'Latency (min/median/max) (ms)': 'N/A'
            })
            continue

        # Calculate averages for the rates
        avg_loss = pd.Series(metrics['loss_rate']).median() # Using median of the runs
        avg_dup = pd.Series(metrics['duplicate_rate']).median()
        avg_gap = pd.Series(metrics['gap_rate']).median()

        # Calculate min/median/max of the Latency (across all 5 runs combined)
        # Note: Combining all 5 runs for a single min/median/max of latency is often preferred
        # but here we use the median of the 5 median latencies as the central tendency for the report
        median_latencies = metrics['delay_median_ms']
        min_latencies = metrics['delay_min_ms']
        max_latencies = metrics['delay_max_ms']
        
        final_min_lat = pd.Series(min_latencies).min()
        final_median_lat = pd.Series(median_latencies).median()
        final_max_lat = pd.Series(max_latencies).max()

        summary_data.append({
            'Scenario': scenario.upper(),
            'Loss Rate (%)': f"{avg_loss:.2f}",
            'Duplicate Rate (%)': f"{avg_dup:.2f}",
            'Gap Rate (%)': f"{avg_gap:.2f}",
            'Latency (min/median/max) (ms)': f"{final_min_lat:.2f} / {final_median_lat:.2f} / {final_max_lat:.2f}"
        })
        
    df_summary = pd.DataFrame(summary_data)
    
    print("\n" + "="*80)
    print("FINAL EXPERIMENT SUMMARY (Median Rates, Min/Median/Max Latency)")
    print("="*80)
    print(df_summary.to_string(index=False))
    print("="*80)
    print(f"\nDetailed per-run CSV saved to final_analysis_summary.csv")
    df_summary.to_csv("final_analysis_summary.csv", index=False)


def main():
    """Main function to find files and run analysis."""
    print("Starting network experiment data analysis...")
    
    # Search for CSVs in the raw_data directory and its subdirectories
    search_pattern = "raw_data/**/*_packets_log.csv"
    csv_files = glob.glob(search_pattern, recursive=True)
    
    if not csv_files:
        print("Error: No CSV files found matching the pattern 'raw_data/**/*_packets_log.csv'.")
        print("Please ensure your 'raw_data' directory and files are correctly named.")
        return

    all_results = defaultdict(list)

    for file_path in sorted(csv_files):
        # Extract scenario name from the file path (e.g., 'raw_data/baseline/...')
        scenario = os.path.basename(os.path.dirname(file_path))
        print(f"Analyzing: {file_path}")
        
        result = analyze_single_run(file_path)
        all_results[scenario].append(result)
        
    # Aggregate and print the final results
    aggregate_and_print_results(all_results)
    
if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("\nCRITICAL ERROR: pandas library not found.")
        print("Please install it on your Linux VM to run the analysis: 'pip install pandas' or 'pip3 install pandas'")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")