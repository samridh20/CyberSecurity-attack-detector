#!/usr/bin/env python3
"""
Offline evaluation script for PCAP files.
Provides comprehensive performance analysis and accuracy metrics.
"""

import argparse
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nids import RealTimeNIDS
from nids.evaluation import NIDSEvaluator, benchmark_latency
from loguru import logger


def load_ground_truth(ground_truth_file: str) -> dict:
    """Load ground truth labels from file."""
    try:
        with open(ground_truth_file, 'r') as f:
            if ground_truth_file.endswith('.json'):
                return json.load(f)
            else:
                # Assume simple text format: one label per line
                labels = []
                for line in f:
                    labels.append(int(line.strip()))
                return {'labels': labels}
    except Exception as e:
        logger.error(f"Failed to load ground truth: {e}")
        return {}


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="NIDS Offline Evaluation")
    parser.add_argument("--pcap", required=True, help="PCAP file to evaluate")
    parser.add_argument("--config", default="config.yaml", help="Configuration file")
    parser.add_argument("--ground-truth", help="Ground truth labels file")
    parser.add_argument("--replay-speed", type=float, default=1.0, 
                       help="Replay speed multiplier")
    parser.add_argument("--results-dir", default="results", 
                       help="Results output directory")
    parser.add_argument("--benchmark", action="store_true", 
                       help="Run latency benchmark")
    parser.add_argument("--plot", action="store_true", 
                       help="Generate evaluation plots")
    parser.add_argument("--report", action="store_true", 
                       help="Generate text report")
    
    args = parser.parse_args()
    
    # Validate inputs
    pcap_file = Path(args.pcap)
    if not pcap_file.exists():
        logger.error(f"PCAP file not found: {pcap_file}")
        return 1
    
    config_file = Path(args.config)
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        return 1
    
    # Load ground truth if provided
    ground_truth = {}
    if args.ground_truth:
        ground_truth = load_ground_truth(args.ground_truth)
    
    try:
        # Initialize NIDS
        logger.info("Initializing NIDS...")
        nids = RealTimeNIDS(str(config_file))
        
        # Initialize evaluator
        evaluator = NIDSEvaluator(nids, args.results_dir)
        
        # Run latency benchmark if requested
        if args.benchmark:
            logger.info("Running latency benchmark...")
            benchmark_results = benchmark_latency(nids, num_packets=1000)
            logger.info(f"Benchmark results: {benchmark_results}")
        
        # Evaluate PCAP file
        logger.info(f"Evaluating PCAP file: {pcap_file}")
        evaluation = evaluator.evaluate_pcap(
            str(pcap_file),
            ground_truth=ground_truth,
            replay_speed=args.replay_speed
        )
        
        # Generate report if requested
        if args.report:
            report = evaluator.generate_report(evaluation)
            
            # Save report to file
            report_file = Path(args.results_dir) / "evaluation_report.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            
            # Print to console
            print("\\n" + report)
            logger.info(f"Report saved to: {report_file}")
        
        # Generate plots if requested
        if args.plot:
            logger.info("Generating evaluation plots...")
            evaluator.plot_results(evaluation)
        
        # Print summary
        stats = evaluation['processing_stats']
        print(f"\\nEVALUATION SUMMARY")
        print(f"==================")
        print(f"Packets processed: {stats['total_packets']:,}")
        print(f"Alerts generated:  {stats['total_alerts']:,}")
        print(f"Processing time:   {stats['processing_time_seconds']:.2f} seconds")
        print(f"Throughput:        {stats['packets_per_second']:.1f} packets/second")
        print(f"Average latency:   {stats['avg_latency_ms']:.2f} ms")
        print(f"P95 latency:       {stats['p95_latency_ms']:.2f} ms")
        
        # Latency compliance
        if 'latency_analysis' in evaluation:
            latency = evaluation['latency_analysis']
            print(f"≤50ms compliance:  {latency['target_50ms_compliance']*100:.1f}%")
            print(f"≤200ms compliance: {latency['target_200ms_compliance']*100:.1f}%")
        
        # Accuracy metrics if available
        if 'accuracy_metrics' in evaluation:
            accuracy = evaluation['accuracy_metrics']
            print(f"\\nACCURACY METRICS")
            print(f"================")
            print(f"Accuracy:  {accuracy['accuracy']:.4f}")
            print(f"Precision: {accuracy['precision']:.4f}")
            print(f"Recall:    {accuracy['recall']:.4f}")
            print(f"F1-Score:  {accuracy['f1_score']:.4f}")
            if 'auc' in accuracy:
                print(f"AUC:       {accuracy['auc']:.4f}")
        
        logger.info("Evaluation completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())