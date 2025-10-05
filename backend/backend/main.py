#!/usr/bin/env python3
"""
NIDS Backend - Main Entry Point
Real-Time Network Intrusion Detection System Backend
"""

import argparse
import signal
import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nids import RealTimeNIDS


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="NIDS Backend - Real-Time Network Intrusion Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start real-time detection with default config
  python main.py

  # Use custom configuration
  python main.py --config config/production.yaml

  # Process offline PCAP file
  python main.py --pcap data/traffic.pcap --offline

  # Run demo with synthetic traffic
  python main.py --demo --duration 60

  # Start API server
  python main.py --api --port 8000
        """
    )
    
    parser.add_argument("--config", default=str(Path(__file__).parent / "config" / "config.yaml"),
                       help="Configuration file path (default: config/config.yaml)")
    parser.add_argument("--pcap", help="PCAP file for offline analysis")
    parser.add_argument("--offline", action="store_true",
                       help="Run in offline mode (requires --pcap)")
    parser.add_argument("--demo", action="store_true",
                       help="Run synthetic traffic demo")
    parser.add_argument("--api", action="store_true",
                       help="Start REST API server")
    parser.add_argument("--port", type=int, default=8000,
                       help="API server port (default: 8000)")
    parser.add_argument("--duration", type=int, default=0,
                       help="Run duration in seconds (0 = indefinite)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level=log_level, 
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | {message}")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.api:
            # Start API server
            from api.server import start_api_server
            logger.info(f"Starting NIDS API server on port {args.port}")
            start_api_server(port=args.port, config_path=args.config)
            
        else:
            # Check configuration file
            config_file = Path(args.config)
            if not config_file.exists():
                logger.error(f"Configuration file not found: {config_file}")
                logger.info("Available configs in config/:")
                config_dir = Path("config")
                if config_dir.exists():
                    for cfg in config_dir.glob("*.yaml"):
                        logger.info(f"  - {cfg.name}")
                return 1
            
            # Initialize NIDS
            logger.info("Initializing NIDS Backend...")
            nids = RealTimeNIDS(str(config_file))
            
            if args.demo:
                # Run demo mode
                logger.info("Running in demo mode...")
                from scripts.demo import run_synthetic_demo
                run_synthetic_demo(nids, duration=args.duration or 60)
                
            elif args.offline and args.pcap:
                # Run offline analysis
                logger.info(f"Running offline analysis on: {args.pcap}")
                results = nids.process_offline(args.pcap)
                
                # Print results
                print(f"\\nOFFLINE ANALYSIS RESULTS")
                print(f"========================")
                print(f"Packets processed: {results['packets_processed']:,}")
                print(f"Alerts generated:  {results['alerts_generated']:,}")
                print(f"Processing time:   {results['processing_time_seconds']:.2f} seconds")
                print(f"Throughput:        {results['packets_per_second']:.1f} packets/second")
                
                if 'avg_latency_ms' in results:
                    print(f"Average latency:   {results['avg_latency_ms']:.2f} ms")
                    print(f"P95 latency:       {results['p95_latency_ms']:.2f} ms")
                
            else:
                # Run real-time detection
                logger.info("Starting real-time network intrusion detection...")
                
                with nids:
                    nids.start_detection()
                    
                    if args.duration > 0:
                        # Run for specified duration
                        import time
                        logger.info(f"Running for {args.duration} seconds...")
                        time.sleep(args.duration)
                        logger.info("Duration completed, stopping...")
                    else:
                        # Run indefinitely
                        logger.info("Running indefinitely (Ctrl+C to stop)...")
                        try:
                            while True:
                                import time
                                time.sleep(1)
                                
                                # Print status every 60 seconds
                                status = nids.get_status()
                                if status['packets_processed'] > 0 and status['packets_processed'] % 1000 == 0:
                                    logger.info(f"Status: {status}")
                        
                        except KeyboardInterrupt:
                            logger.info("Interrupted by user")
        
        logger.info("NIDS Backend shutdown complete")
        return 0
        
    except Exception as e:
        logger.error(f"NIDS Backend failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())