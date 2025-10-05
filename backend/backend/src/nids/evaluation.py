"""
Evaluation module for offline PCAP analysis and performance metrics.
"""

import time
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import numpy as np
from loguru import logger

try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report, roc_auc_score, roc_curve
    )
    import matplotlib.pyplot as plt
    import seaborn as sns
    SKLEARN_AVAILABLE = True
    PLOTTING_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    PLOTTING_AVAILABLE = False
    logger.warning("sklearn/matplotlib not available - limited evaluation features")

from .core import RealTimeNIDS
from .schemas import ModelPrediction, Alert


class NIDSEvaluator:
    """
    Comprehensive evaluation system for NIDS performance.
    Supports offline PCAP replay with ground truth comparison.
    """
    
    def __init__(self, nids: RealTimeNIDS, results_dir: str = "results"):
        """
        Initialize evaluator.
        
        Args:
            nids: NIDS instance to evaluate
            results_dir: Directory for evaluation results
        """
        self.nids = nids
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"NIDS evaluator initialized (results: {self.results_dir})")
    
    def evaluate_pcap(self, 
                     pcap_file: str,
                     ground_truth: Optional[Dict[str, Any]] = None,
                     replay_speed: float = 1.0) -> Dict[str, Any]:
        """
        Evaluate NIDS performance on PCAP file.
        
        Args:
            pcap_file: Path to PCAP file
            ground_truth: Optional ground truth labels
            replay_speed: Replay speed multiplier
            
        Returns:
            Comprehensive evaluation results
        """
        logger.info(f"Evaluating PCAP: {pcap_file}")
        
        # Process PCAP file
        start_time = time.time()
        results = self.nids.process_offline(pcap_file, replay_speed)
        total_time = time.time() - start_time
        
        # Extract predictions and alerts
        predictions = results.get('predictions', [])
        alerts = results.get('alerts', [])
        
        # Basic performance metrics
        evaluation = {
            'pcap_file': pcap_file,
            'timestamp': time.time(),
            'processing_stats': {
                'total_packets': results['packets_processed'],
                'total_alerts': results['alerts_generated'],
                'processing_time_seconds': total_time,
                'packets_per_second': results.get('packets_per_second', 0),
                'avg_latency_ms': results.get('avg_latency_ms', 0),
                'p95_latency_ms': results.get('p95_latency_ms', 0)
            }
        }
        
        # Performance analysis
        if predictions:
            evaluation['latency_analysis'] = self._analyze_latency(predictions)
            evaluation['detection_analysis'] = self._analyze_detections(predictions, alerts)
        
        # Ground truth comparison if available
        if ground_truth and SKLEARN_AVAILABLE:
            evaluation['accuracy_metrics'] = self._evaluate_accuracy(predictions, ground_truth)
        
        # Save results
        self._save_evaluation_results(evaluation)
        
        logger.info(f"Evaluation complete: {evaluation['processing_stats']['total_packets']} packets processed")
        
        return evaluation
    
    def _analyze_latency(self, predictions: List[ModelPrediction]) -> Dict[str, float]:
        """Analyze processing latency statistics."""
        latencies = [p.processing_time_ms for p in predictions]
        
        if not latencies:
            return {}
        
        latencies_np = np.array(latencies)
        
        return {
            'mean_ms': float(np.mean(latencies_np)),
            'median_ms': float(np.median(latencies_np)),
            'std_ms': float(np.std(latencies_np)),
            'min_ms': float(np.min(latencies_np)),
            'max_ms': float(np.max(latencies_np)),
            'p95_ms': float(np.percentile(latencies_np, 95)),
            'p99_ms': float(np.percentile(latencies_np, 99)),
            'target_50ms_compliance': float(np.mean(latencies_np <= 50.0)),
            'target_200ms_compliance': float(np.mean(latencies_np <= 200.0))
        }
    
    def _analyze_detections(self, predictions: List[ModelPrediction], alerts: List[Alert]) -> Dict[str, Any]:
        """Analyze detection patterns and statistics."""
        if not predictions:
            return {}
        
        # Attack detection statistics
        attack_predictions = [p for p in predictions if p.is_attack]
        attack_probabilities = [p.attack_probability for p in predictions]
        
        analysis = {
            'total_predictions': len(predictions),
            'attack_predictions': len(attack_predictions),
            'attack_rate': len(attack_predictions) / len(predictions),
            'alerts_generated': len(alerts),
            'alert_rate': len(alerts) / len(predictions) if predictions else 0
        }
        
        # Probability distribution
        if attack_probabilities:
            probs_np = np.array(attack_probabilities)
            analysis['probability_stats'] = {
                'mean': float(np.mean(probs_np)),
                'std': float(np.std(probs_np)),
                'high_confidence_rate': float(np.mean(probs_np > 0.8))
            }
        
        # Attack class distribution
        if attack_predictions:
            attack_classes = [p.attack_class for p in attack_predictions if p.attack_class]
            if attack_classes:
                class_counts = {}
                for cls in attack_classes:
                    class_counts[cls] = class_counts.get(cls, 0) + 1
                analysis['attack_class_distribution'] = class_counts
        
        return analysis
    
    def _evaluate_accuracy(self, predictions: List[ModelPrediction], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate accuracy against ground truth labels."""
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available for accuracy evaluation")
            return {}
        
        # Extract predictions and true labels
        # This assumes ground_truth contains packet-level labels
        # You'll need to adapt this based on your ground truth format
        
        y_pred = [1 if p.is_attack else 0 for p in predictions]
        y_proba = [p.attack_probability for p in predictions]
        
        # For demonstration, create dummy ground truth
        # In practice, you'd load this from your labeled dataset
        y_true = ground_truth.get('labels', [0] * len(predictions))
        
        if len(y_true) != len(y_pred):
            logger.warning("Ground truth length mismatch - using available data")
            min_len = min(len(y_true), len(y_pred))
            y_true = y_true[:min_len]
            y_pred = y_pred[:min_len]
            y_proba = y_proba[:min_len]
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1)
        }
        
        # ROC AUC if we have positive samples
        if len(set(y_true)) > 1:
            try:
                auc = roc_auc_score(y_true, y_proba)
                metrics['auc'] = float(auc)
            except ValueError as e:
                logger.warning(f"Could not calculate AUC: {e}")
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # Per-class metrics
        if len(set(y_true)) > 1:
            report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
            metrics['classification_report'] = report
        
        return metrics
    
    def _save_evaluation_results(self, evaluation: Dict[str, Any]):
        """Save evaluation results to file."""
        timestamp = int(time.time())
        results_file = self.results_dir / f"evaluation_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(evaluation, f, indent=2, default=str)
            
            logger.info(f"Evaluation results saved: {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save evaluation results: {e}")
    
    def generate_report(self, evaluation: Dict[str, Any]) -> str:
        """Generate human-readable evaluation report."""
        report = []
        report.append("NIDS EVALUATION REPORT")
        report.append("=" * 50)
        report.append("")
        
        # Basic info
        report.append(f"PCAP File: {evaluation['pcap_file']}")
        report.append(f"Evaluation Time: {time.ctime(evaluation['timestamp'])}")
        report.append("")
        
        # Processing statistics
        stats = evaluation['processing_stats']
        report.append("PROCESSING PERFORMANCE")
        report.append("-" * 30)
        report.append(f"Total Packets:     {stats['total_packets']:,}")
        report.append(f"Total Alerts:      {stats['total_alerts']:,}")
        report.append(f"Processing Time:   {stats['processing_time_seconds']:.2f} seconds")
        report.append(f"Throughput:        {stats['packets_per_second']:.1f} packets/second")
        report.append(f"Average Latency:   {stats['avg_latency_ms']:.2f} ms")
        report.append(f"P95 Latency:       {stats['p95_latency_ms']:.2f} ms")
        report.append("")
        
        # Latency analysis
        if 'latency_analysis' in evaluation:
            latency = evaluation['latency_analysis']
            report.append("LATENCY ANALYSIS")
            report.append("-" * 20)
            report.append(f"Mean:              {latency['mean_ms']:.2f} ms")
            report.append(f"Median:            {latency['median_ms']:.2f} ms")
            report.append(f"P95:               {latency['p95_ms']:.2f} ms")
            report.append(f"P99:               {latency['p99_ms']:.2f} ms")
            report.append(f"≤50ms compliance:  {latency['target_50ms_compliance']*100:.1f}%")
            report.append(f"≤200ms compliance: {latency['target_200ms_compliance']*100:.1f}%")
            report.append("")
        
        # Detection analysis
        if 'detection_analysis' in evaluation:
            detection = evaluation['detection_analysis']
            report.append("DETECTION ANALYSIS")
            report.append("-" * 20)
            report.append(f"Attack Rate:       {detection['attack_rate']*100:.2f}%")
            report.append(f"Alert Rate:        {detection['alert_rate']*100:.2f}%")
            
            if 'attack_class_distribution' in detection:
                report.append("Attack Classes:")
                for cls, count in detection['attack_class_distribution'].items():
                    report.append(f"  {cls}: {count}")
            report.append("")
        
        # Accuracy metrics
        if 'accuracy_metrics' in evaluation:
            accuracy = evaluation['accuracy_metrics']
            report.append("ACCURACY METRICS")
            report.append("-" * 20)
            report.append(f"Accuracy:          {accuracy['accuracy']:.4f}")
            report.append(f"Precision:         {accuracy['precision']:.4f}")
            report.append(f"Recall:            {accuracy['recall']:.4f}")
            report.append(f"F1-Score:          {accuracy['f1_score']:.4f}")
            if 'auc' in accuracy:
                report.append(f"AUC:               {accuracy['auc']:.4f}")
            report.append("")
        
        return "\\n".join(report)
    
    def plot_results(self, evaluation: Dict[str, Any]):
        """Generate evaluation plots."""
        if not PLOTTING_AVAILABLE:
            logger.warning("matplotlib not available for plotting")
            return
        
        # Create plots directory
        plots_dir = self.results_dir / "plots"
        plots_dir.mkdir(exist_ok=True)
        
        # Latency distribution plot
        if 'latency_analysis' in evaluation:
            self._plot_latency_distribution(evaluation, plots_dir)
        
        # Confusion matrix plot
        if 'accuracy_metrics' in evaluation and 'confusion_matrix' in evaluation['accuracy_metrics']:
            self._plot_confusion_matrix(evaluation, plots_dir)
        
        logger.info(f"Plots saved to {plots_dir}")
    
    def _plot_latency_distribution(self, evaluation: Dict[str, Any], plots_dir: Path):
        """Plot latency distribution."""
        try:
            latency = evaluation['latency_analysis']
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Histogram
            # Note: We don't have raw latency data here, so this is a placeholder
            ax1.axvline(latency['mean_ms'], color='red', linestyle='--', label=f"Mean: {latency['mean_ms']:.1f}ms")
            ax1.axvline(50, color='green', linestyle='--', label="50ms target")
            ax1.set_xlabel('Latency (ms)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Processing Latency Distribution')
            ax1.legend()
            
            # Box plot summary
            stats = [latency['min_ms'], latency['p95_ms'], latency['median_ms'], latency['p95_ms'], latency['max_ms']]
            ax2.boxplot([stats], labels=['Latency'])
            ax2.set_ylabel('Latency (ms)')
            ax2.set_title('Latency Summary')
            
            plt.tight_layout()
            plt.savefig(plots_dir / 'latency_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Failed to plot latency distribution: {e}")
    
    def _plot_confusion_matrix(self, evaluation: Dict[str, Any], plots_dir: Path):
        """Plot confusion matrix."""
        try:
            cm = np.array(evaluation['accuracy_metrics']['confusion_matrix'])
            
            plt.figure(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                       xticklabels=['Normal', 'Attack'],
                       yticklabels=['Normal', 'Attack'])
            plt.title('Confusion Matrix')
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
            
            plt.tight_layout()
            plt.savefig(plots_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Failed to plot confusion matrix: {e}")


def benchmark_latency(nids: RealTimeNIDS, num_packets: int = 1000) -> Dict[str, float]:
    """
    Benchmark processing latency with synthetic packets.
    
    Args:
        nids: NIDS instance to benchmark
        num_packets: Number of synthetic packets to process
        
    Returns:
        Latency statistics
    """
    from .schemas import PacketInfo
    import random
    
    logger.info(f"Benchmarking latency with {num_packets} synthetic packets")
    
    # Generate synthetic packets
    packets = []
    for i in range(num_packets):
        packet = PacketInfo(
            timestamp=time.time() + i * 0.001,
            src_ip=f"192.168.1.{random.randint(1, 254)}",
            dst_ip=f"10.0.0.{random.randint(1, 254)}",
            src_port=random.randint(1024, 65535),
            dst_port=random.choice([80, 443, 22, 53, 21]),
            protocol=random.choice(['tcp', 'udp']),
            packet_size=random.randint(64, 1500),
            payload_size=random.randint(0, 1400),
            payload=b'\\x00' * random.randint(0, 100)
        )
        packets.append(packet)
    
    # Process packets and measure latency
    latencies = []
    
    for packet in packets:
        start_time = time.time()
        
        # Extract features
        features = nids.feature_extractor.extract_features(packet)
        
        # Get prediction
        prediction = nids.model_adapter.predict(features)
        
        latency = (time.time() - start_time) * 1000  # Convert to ms
        latencies.append(latency)
    
    # Calculate statistics
    latencies_np = np.array(latencies)
    
    stats = {
        'mean_ms': float(np.mean(latencies_np)),
        'median_ms': float(np.median(latencies_np)),
        'std_ms': float(np.std(latencies_np)),
        'min_ms': float(np.min(latencies_np)),
        'max_ms': float(np.max(latencies_np)),
        'p95_ms': float(np.percentile(latencies_np, 95)),
        'p99_ms': float(np.percentile(latencies_np, 99)),
        'target_50ms_compliance': float(np.mean(latencies_np <= 50.0)),
        'packets_processed': num_packets
    }
    
    logger.info(f"Latency benchmark complete: {stats['mean_ms']:.2f}ms average, {stats['p95_ms']:.2f}ms P95")
    
    return stats