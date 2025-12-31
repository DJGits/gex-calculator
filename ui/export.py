"""
Data export functionality for CSV and image formats
"""

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any, Optional
import io
import base64
from pathlib import Path

from data.models import GammaExposure, WallLevel, MarketMetrics


class ExportError(Exception):
    """Custom exception for export errors"""
    pass


class ExportManager:
    """Handles data export functionality for CSV and image formats"""
    
    def __init__(self):
        """Initialize export manager"""
        self.timestamp = datetime.now()
    
    def export_gamma_exposures_to_csv(self, 
                                    gamma_exposures: List[GammaExposure],
                                    filename: Optional[str] = None,
                                    include_metadata: bool = True) -> str:
        """
        Export gamma exposure data to CSV format
        
        Args:
            gamma_exposures: List of GammaExposure objects
            filename: Output filename (optional)
            include_metadata: Whether to include metadata in the file
            
        Returns:
            CSV data as string or filename if saved to file
        """
        try:
            if not gamma_exposures:
                raise ExportError("No gamma exposure data to export")
            
            # Convert to DataFrame
            data = []
            for ge in gamma_exposures:
                data.append({
                    'strike': ge.strike,
                    'call_gamma_exposure': ge.call_gamma_exposure,
                    'put_gamma_exposure': ge.put_gamma_exposure,
                    'net_gamma_exposure': ge.net_gamma_exposure,
                    'total_open_interest': ge.total_open_interest
                })
            
            df = pd.DataFrame(data)
            
            # Add metadata if requested
            if include_metadata:
                metadata_rows = [
                    ['# SPX Gamma Exposure Data Export'],
                    [f'# Generated: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'],
                    [f'# Total Strikes: {len(gamma_exposures)}'],
                    [f'# Total Net Gamma: {sum(ge.net_gamma_exposure for ge in gamma_exposures):,.0f}'],
                    ['# '],
                    ['# Columns:'],
                    ['# strike - Strike price'],
                    ['# call_gamma_exposure - Gamma exposure from call options'],
                    ['# put_gamma_exposure - Gamma exposure from put options'],
                    ['# net_gamma_exposure - Net gamma exposure (call + put)'],
                    ['# total_open_interest - Total open interest at strike'],
                    ['# ']
                ]
                
                # Create metadata string
                metadata_str = '\n'.join([row[0] for row in metadata_rows])
                
                # Convert DataFrame to CSV
                csv_data = df.to_csv(index=False)
                
                # Combine metadata and data
                full_csv = metadata_str + '\n' + csv_data
            else:
                full_csv = df.to_csv(index=False)
            
            # Save to file if filename provided
            if filename:
                with open(filename, 'w') as f:
                    f.write(full_csv)
                return filename
            else:
                return full_csv
                
        except Exception as e:
            raise ExportError(f"Error exporting gamma exposures to CSV: {str(e)}")
    
    def export_walls_to_csv(self, 
                           walls: Dict[str, List[WallLevel]],
                           filename: Optional[str] = None,
                           include_metadata: bool = True) -> str:
        """
        Export wall data to CSV format
        
        Args:
            walls: Dictionary with 'call_walls' and 'put_walls' keys
            filename: Output filename (optional)
            include_metadata: Whether to include metadata in the file
            
        Returns:
            CSV data as string or filename if saved to file
        """
        try:
            call_walls = walls.get('call_walls', [])
            put_walls = walls.get('put_walls', [])
            
            if not call_walls and not put_walls:
                raise ExportError("No wall data to export")
            
            # Convert to DataFrame
            data = []
            
            for wall in call_walls:
                data.append({
                    'wall_type': wall.wall_type,
                    'strike': wall.strike,
                    'exposure_value': wall.exposure_value,
                    'distance_from_spot': wall.distance_from_spot,
                    'significance_rank': wall.significance_rank
                })
            
            for wall in put_walls:
                data.append({
                    'wall_type': wall.wall_type,
                    'strike': wall.strike,
                    'exposure_value': wall.exposure_value,
                    'distance_from_spot': wall.distance_from_spot,
                    'significance_rank': wall.significance_rank
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values(['wall_type', 'significance_rank'])
            
            # Add metadata if requested
            if include_metadata:
                metadata_rows = [
                    ['# SPX Gamma Wall Data Export'],
                    [f'# Generated: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'],
                    [f'# Call Walls: {len(call_walls)}'],
                    [f'# Put Walls: {len(put_walls)}'],
                    ['# '],
                    ['# Columns:'],
                    ['# wall_type - Type of wall (call_wall or put_wall)'],
                    ['# strike - Strike price of the wall'],
                    ['# exposure_value - Gamma exposure value at the wall'],
                    ['# distance_from_spot - Distance from current spot price'],
                    ['# significance_rank - Ranking by significance (1 = most significant)'],
                    ['# ']
                ]
                
                # Create metadata string
                metadata_str = '\n'.join([row[0] for row in metadata_rows])
                
                # Convert DataFrame to CSV
                csv_data = df.to_csv(index=False)
                
                # Combine metadata and data
                full_csv = metadata_str + '\n' + csv_data
            else:
                full_csv = df.to_csv(index=False)
            
            # Save to file if filename provided
            if filename:
                with open(filename, 'w') as f:
                    f.write(full_csv)
                return filename
            else:
                return full_csv
                
        except Exception as e:
            raise ExportError(f"Error exporting walls to CSV: {str(e)}")
    
    def export_metrics_to_csv(self, 
                            market_metrics: MarketMetrics,
                            metrics_summary: Dict[str, Any],
                            filename: Optional[str] = None,
                            include_metadata: bool = True) -> str:
        """
        Export market metrics to CSV format
        
        Args:
            market_metrics: MarketMetrics object
            metrics_summary: Additional metrics summary
            filename: Output filename (optional)
            include_metadata: Whether to include metadata in the file
            
        Returns:
            CSV data as string or filename if saved to file
        """
        try:
            # Create metrics data
            data = []
            
            # Core metrics
            core_metrics = market_metrics.to_dict()
            for key, value in core_metrics.items():
                data.append({
                    'category': 'core_metrics',
                    'metric': key,
                    'value': value,
                    'description': self._get_metric_description(key)
                })
            
            # Additional statistics
            if 'statistics' in metrics_summary:
                stats = metrics_summary['statistics']
                for key, value in stats.items():
                    data.append({
                        'category': 'statistics',
                        'metric': key,
                        'value': value,
                        'description': self._get_metric_description(key)
                    })
            
            # Percentiles
            if 'percentiles' in metrics_summary:
                percentiles = metrics_summary['percentiles']
                for key, value in percentiles.items():
                    data.append({
                        'category': 'percentiles',
                        'metric': key,
                        'value': value,
                        'description': f'Percentile {key[1:]} of gamma exposure distribution'
                    })
            
            # Concentration metrics
            if 'concentration' in metrics_summary:
                concentration = metrics_summary['concentration']
                for key, value in concentration.items():
                    data.append({
                        'category': 'concentration',
                        'metric': key,
                        'value': value,
                        'description': self._get_metric_description(key)
                    })
            
            df = pd.DataFrame(data)
            
            # Add metadata if requested
            if include_metadata:
                metadata_rows = [
                    ['# SPX Gamma Exposure Metrics Export'],
                    [f'# Generated: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'],
                    [f'# Current Price: {metrics_summary.get("current_price", "N/A")}'],
                    ['# '],
                    ['# Categories:'],
                    ['# core_metrics - Primary gamma exposure metrics'],
                    ['# statistics - Statistical measures of exposure distribution'],
                    ['# percentiles - Percentile values of exposure distribution'],
                    ['# concentration - Concentration measures'],
                    ['# ']
                ]
                
                # Create metadata string
                metadata_str = '\n'.join([row[0] for row in metadata_rows])
                
                # Convert DataFrame to CSV
                csv_data = df.to_csv(index=False)
                
                # Combine metadata and data
                full_csv = metadata_str + '\n' + csv_data
            else:
                full_csv = df.to_csv(index=False)
            
            # Save to file if filename provided
            if filename:
                with open(filename, 'w') as f:
                    f.write(full_csv)
                return filename
            else:
                return full_csv
                
        except Exception as e:
            raise ExportError(f"Error exporting metrics to CSV: {str(e)}")
    
    def export_chart_to_png(self, 
                           fig: go.Figure, 
                           filename: Optional[str] = None,
                           width: int = 1200,
                           height: int = 800) -> str:
        """
        Export Plotly chart to PNG format
        
        Args:
            fig: Plotly Figure object
            filename: Output filename (optional)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Filename if saved to file, or base64 encoded image data
        """
        try:
            if filename:
                # Save to file
                fig.write_image(filename, format='png', width=width, height=height)
                return filename
            else:
                # Return as base64 encoded data
                img_bytes = fig.to_image(format='png', width=width, height=height)
                img_base64 = base64.b64encode(img_bytes).decode()
                return img_base64
                
        except Exception as e:
            raise ExportError(f"Error exporting chart to PNG: {str(e)}")
    
    def create_comprehensive_export_package(self, 
                                          gamma_exposures: List[GammaExposure],
                                          walls: Dict[str, List[WallLevel]],
                                          market_metrics: MarketMetrics,
                                          metrics_summary: Dict[str, Any],
                                          charts: Dict[str, go.Figure],
                                          output_dir: str = "exports") -> Dict[str, str]:
        """
        Create comprehensive export package with all data and charts
        
        Args:
            gamma_exposures: List of GammaExposure objects
            walls: Dictionary with wall data
            market_metrics: MarketMetrics object
            metrics_summary: Additional metrics summary
            charts: Dictionary of chart figures
            output_dir: Output directory for exports
            
        Returns:
            Dictionary with exported file paths
        """
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Generate timestamp for filenames
            timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
            
            exported_files = {}
            
            # Export gamma exposures
            gamma_filename = output_path / f"gamma_exposures_{timestamp_str}.csv"
            self.export_gamma_exposures_to_csv(gamma_exposures, str(gamma_filename))
            exported_files['gamma_exposures'] = str(gamma_filename)
            
            # Export walls
            if walls.get('call_walls') or walls.get('put_walls'):
                walls_filename = output_path / f"walls_{timestamp_str}.csv"
                self.export_walls_to_csv(walls, str(walls_filename))
                exported_files['walls'] = str(walls_filename)
            
            # Export metrics
            metrics_filename = output_path / f"metrics_{timestamp_str}.csv"
            self.export_metrics_to_csv(market_metrics, metrics_summary, str(metrics_filename))
            exported_files['metrics'] = str(metrics_filename)
            
            # Export charts
            for chart_name, fig in charts.items():
                chart_filename = output_path / f"{chart_name}_{timestamp_str}.png"
                self.export_chart_to_png(fig, str(chart_filename))
                exported_files[f'chart_{chart_name}'] = str(chart_filename)
            
            # Create summary file
            summary_filename = output_path / f"export_summary_{timestamp_str}.txt"
            self._create_export_summary(exported_files, str(summary_filename), metrics_summary)
            exported_files['summary'] = str(summary_filename)
            
            return exported_files
            
        except Exception as e:
            raise ExportError(f"Error creating comprehensive export package: {str(e)}")
    
    def _get_metric_description(self, metric_name: str) -> str:
        """Get description for metric name"""
        descriptions = {
            'total_net_gamma': 'Total net gamma exposure across all strikes',
            'gamma_weighted_avg_strike': 'Gamma-weighted average strike price',
            'call_put_gamma_ratio': 'Ratio of call to put gamma exposure',
            'max_call_exposure': 'Maximum call gamma exposure (most negative)',
            'max_put_exposure': 'Maximum put gamma exposure (most positive)',
            'gamma_exposure_std': 'Standard deviation of gamma exposure',
            'mean': 'Mean gamma exposure',
            'std': 'Standard deviation of gamma exposure',
            'min': 'Minimum gamma exposure',
            'max': 'Maximum gamma exposure',
            'median': 'Median gamma exposure',
            'skewness': 'Skewness of gamma exposure distribution',
            'kurtosis': 'Kurtosis of gamma exposure distribution',
            'top_5_concentration': 'Percentage of exposure in top 5 strikes',
            'top_10_concentration': 'Percentage of exposure in top 10 strikes',
            'herfindahl_index': 'Herfindahl-Hirschman concentration index'
        }
        return descriptions.get(metric_name, 'No description available')
    
    def _create_export_summary(self, 
                              exported_files: Dict[str, str], 
                              filename: str,
                              metrics_summary: Dict[str, Any]):
        """Create export summary file"""
        try:
            with open(filename, 'w') as f:
                f.write("SPX Gamma Exposure Calculator - Export Summary\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Export Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Current Price: {metrics_summary.get('current_price', 'N/A')}\n\n")
                
                f.write("Exported Files:\n")
                f.write("-" * 20 + "\n")
                for file_type, filepath in exported_files.items():
                    if file_type != 'summary':  # Don't include the summary file itself
                        f.write(f"{file_type}: {filepath}\n")
                
                f.write("\nData Summary:\n")
                f.write("-" * 20 + "\n")
                data_quality = metrics_summary.get('data_quality', {})
                f.write(f"Total Strikes: {data_quality.get('total_strikes', 'N/A')}\n")
                f.write(f"Strikes with Exposure: {data_quality.get('strikes_with_exposure', 'N/A')}\n")
                f.write(f"Total Open Interest: {data_quality.get('total_open_interest', 'N/A'):,}\n")
                
                core_metrics = metrics_summary.get('core_metrics', {})
                f.write(f"Total Net Gamma: {core_metrics.get('total_net_gamma', 'N/A'):,.0f}\n")
                f.write(f"Gamma Weighted Avg Strike: {core_metrics.get('gamma_weighted_avg_strike', 'N/A'):.0f}\n")
                
        except Exception as e:
            raise ExportError(f"Error creating export summary: {str(e)}")
    
    def get_export_timestamp(self) -> str:
        """Get formatted timestamp for exports"""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def create_streamlit_download_data(self, data: str, filename: str, mime_type: str = 'text/csv') -> Dict[str, Any]:
        """
        Prepare data for Streamlit download button
        
        Args:
            data: Data to download
            filename: Suggested filename
            mime_type: MIME type for the data
            
        Returns:
            Dictionary with download parameters
        """
        return {
            'data': data,
            'file_name': filename,
            'mime': mime_type
        }