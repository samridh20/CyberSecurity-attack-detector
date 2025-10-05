#!/usr/bin/env python3
"""
Script to export MATLAB model metadata for Python compatibility.
Extracts feature order, scaler parameters, and class encodings.
"""

import json
import argparse
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import scipy.io
    import numpy as np
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("ERROR: scipy not available. Run: pip install scipy")
    sys.exit(1)

from loguru import logger


def extract_matlab_metadata(mat_file: str, output_dir: str):
    """
    Extract metadata from MATLAB .mat file.
    
    Args:
        mat_file: Path to MATLAB .mat file
        output_dir: Output directory for JSON files
    """
    logger.info(f"Extracting metadata from: {mat_file}")
    
    try:
        # Load MATLAB file
        mat_data = scipy.io.loadmat(mat_file)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Extract model data structure
        if 'model_data' in mat_data:
            model_struct = mat_data['model_data']
            
            # Extract feature names/order
            if 'feature_names' in model_struct.dtype.names:
                feature_names = model_struct['feature_names'][0, 0]
                feature_order = [str(name[0]) for name in feature_names.flatten()]
                
                feature_order_file = output_path / 'feature_order.json'
                with open(feature_order_file, 'w') as f:
                    json.dump(feature_order, f, indent=2)
                
                logger.info(f"Feature order saved: {feature_order_file} ({len(feature_order)} features)")
            
            # Extract scaler parameters
            if 'scaler_mu' in model_struct.dtype.names and 'scaler_sigma' in model_struct.dtype.names:
                mu = model_struct['scaler_mu'][0, 0].flatten()
                sigma = model_struct['scaler_sigma'][0, 0].flatten()
                
                scaler_params = {
                    'mean': mu.tolist(),
                    'scale': sigma.tolist(),
                    'n_features': len(mu)
                }
                
                scaler_file = output_path / 'scaler_params.json'
                with open(scaler_file, 'w') as f:
                    json.dump(scaler_params, f, indent=2)
                
                logger.info(f"Scaler parameters saved: {scaler_file}")
            
            # Extract class names
            if 'class_names' in model_struct.dtype.names:
                class_names = model_struct['class_names'][0, 0]
                classes = [str(name[0]) for name in class_names.flatten()]
                
                class_encoder = {
                    'classes': classes,
                    'n_classes': len(classes)
                }
                
                encoder_file = output_path / 'class_encoder.json'
                with open(encoder_file, 'w') as f:
                    json.dump(class_encoder, f, indent=2)
                
                logger.info(f"Class encoder saved: {encoder_file} ({len(classes)} classes)")
            
            # Extract logistic regression coefficients if available
            if 'classifier' in model_struct.dtype.names:
                try:
                    classifier_data = model_struct['classifier'][0, 0]
                    
                    # This part depends on how MATLAB exports the model
                    # You may need to adapt this based on your specific export format
                    
                    # For fitglm models, coefficients might be in different fields
                    # Common fields: Coefficients, Beta, etc.
                    
                    # Placeholder for coefficient extraction
                    coefficients_info = {
                        'note': 'Coefficient extraction needs to be customized based on MATLAB export format',
                        'available_fields': list(classifier_data.dtype.names) if hasattr(classifier_data, 'dtype') else 'N/A'
                    }
                    
                    coeff_file = output_path / 'coefficients.json'
                    with open(coeff_file, 'w') as f:
                        json.dump(coefficients_info, f, indent=2)
                    
                    logger.info(f"Coefficient info saved: {coeff_file}")
                    
                except Exception as e:
                    logger.warning(f"Could not extract coefficients: {e}")
        
        else:
            logger.warning("No 'model_data' structure found in .mat file")
            logger.info("Available keys: " + str(list(mat_data.keys())))
        
        logger.info("Metadata extraction completed")
        
    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}")
        raise


def create_sample_metadata(output_dir: str):
    """Create sample metadata files for testing."""
    logger.info("Creating sample metadata files for testing...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Sample feature order (based on your MATLAB code)
    feature_order = [
        'packet_size', 'direction', 'inter_arrival_delta', 'tcp_flags_bitmap', 'ttl',
        'total_bytes', 'total_packets', 'bytes_ratio', 'packets_per_second', 'syn_fin_ratio',
        'size_mean', 'size_std', 'iat_mean', 'iat_std', 'burstiness',
        'payload_entropy', 'printable_ratio'
    ]
    
    with open(output_path / 'feature_order.json', 'w') as f:
        json.dump(feature_order, f, indent=2)
    
    # Sample scaler parameters
    scaler_params = {
        'mean': [0.0] * len(feature_order),
        'scale': [1.0] * len(feature_order),
        'n_features': len(feature_order)
    }
    
    with open(output_path / 'scaler_params.json', 'w') as f:
        json.dump(scaler_params, f, indent=2)
    
    # Sample class encoder
    class_encoder = {
        'classes': ['Normal', 'DoS', 'Exploits', 'Fuzzers', 'Generic', 'Reconnaissance'],
        'n_classes': 6
    }
    
    with open(output_path / 'class_encoder.json', 'w') as f:
        json.dump(class_encoder, f, indent=2)
    
    logger.info(f"Sample metadata created in: {output_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Export MATLAB Model Metadata")
    parser.add_argument("--mat-file", help="MATLAB .mat file to process")
    parser.add_argument("--output-dir", default="models", help="Output directory")
    parser.add_argument("--create-sample", action="store_true", 
                       help="Create sample metadata files for testing")
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_metadata(args.output_dir)
        return 0
    
    if not args.mat_file:
        logger.error("Either --mat-file or --create-sample must be specified")
        return 1
    
    mat_file = Path(args.mat_file)
    if not mat_file.exists():
        logger.error(f"MATLAB file not found: {mat_file}")
        return 1
    
    try:
        extract_matlab_metadata(str(mat_file), args.output_dir)
        logger.info("Metadata export completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Metadata export failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())