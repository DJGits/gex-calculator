"""
Visualization engine for gamma exposure charts using Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from data.models import GammaExposure, WallLevel
from config import (CHART_HEIGHT, CHART_WIDTH, CALL_WALL_COLOR, 
                   PUT_WALL_COLOR, CURRENT_PRICE_COLOR)


class VisualizationError(Exception):
    """Custom exception for visualization errors"""
    pass


class VisualizationEngine:
    """Creates interactive charts and visualizations for gamma exposure analysis"""
    
    def __init__(self, 
                 chart_height: int = CHART_HEIGHT,
                 chart_width: int = CHART_WIDTH):
        """
        Initialize visualization engine
        
        Args:
            chart_height: Default chart height in pixels
            chart_width: Default chart width in pixels
        """
        self.chart_height = chart_height
        self.chart_width = chart_width
        self.theme = {
            'background_color': 'white',
            'grid_color': '#E5E5E5',
            'text_color': '#2E2E2E',
            'call_color': CALL_WALL_COLOR,
            'put_color': PUT_WALL_COLOR,
            'current_price_color': CURRENT_PRICE_COLOR,
            'positive_gamma_color': '#4CAF50',
            'negative_gamma_color': '#F44336'
        }
    
    def create_gamma_exposure_chart(self, 
                                  gamma_exposures: List[GammaExposure],
                                  current_price: Optional[float] = None,
                                  title: str = "Gamma Exposure by Strike Price") -> go.Figure:
        """
        Create bar chart showing gamma exposure by strike price
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current SPX price for reference line
            title: Chart title
            
        Returns:
            Plotly Figure object
        """
        if not gamma_exposures:
            # Return empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No gamma exposure data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.theme['text_color'])
            )
            fig.update_layout(
                title=title,
                height=self.chart_height,
                width=self.chart_width
            )
            return fig
        
        try:
            # Prepare data
            strikes = [ge.strike for ge in gamma_exposures]
            net_exposures = [ge.net_gamma_exposure for ge in gamma_exposures]
            call_exposures = [ge.call_gamma_exposure for ge in gamma_exposures]
            put_exposures = [ge.put_gamma_exposure for ge in gamma_exposures]
            
            # Create figure
            fig = go.Figure()
            
            # Add net gamma exposure bars
            colors = [self.theme['positive_gamma_color'] if exp >= 0 else self.theme['negative_gamma_color'] 
                     for exp in net_exposures]
            
            fig.add_trace(go.Bar(
                x=strikes,
                y=net_exposures,
                name='Net Gamma Exposure',
                marker_color=colors,
                hovertemplate=(
                    '<b>Strike:</b> %{x}<br>'
                    '<b>Net Gamma Exposure:</b> %{y:,.0f}<br>'
                    '<extra></extra>'
                ),
                opacity=0.8
            ))
            
            # Add current price line if provided
            if current_price is not None:
                fig.add_vline(
                    x=current_price,
                    line_dash="dash",
                    line_color=self.theme['current_price_color'],
                    line_width=3,
                    annotation_text=f"Current Price: {current_price:.0f}",
                    annotation_position="top"
                )
            
            # Update layout
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': self.theme['text_color']}
                },
                xaxis_title="Strike Price",
                yaxis_title="Gamma Exposure",
                height=self.chart_height,
                width=self.chart_width,
                plot_bgcolor=self.theme['background_color'],
                paper_bgcolor=self.theme['background_color'],
                font=dict(color=self.theme['text_color']),
                hovermode='x unified',
                showlegend=True
            )
            
            # Update axes
            fig.update_xaxes(
                gridcolor=self.theme['grid_color'],
                showgrid=True,
                tickformat='.0f'
            )
            fig.update_yaxes(
                gridcolor=self.theme['grid_color'],
                showgrid=True,
                tickformat='~s'
            )
            
            return fig
            
        except Exception as e:
            raise VisualizationError(f"Error creating gamma exposure chart: {str(e)}")
    
    def create_call_put_breakdown_chart(self, 
                                      gamma_exposures: List[GammaExposure],
                                      current_price: Optional[float] = None,
                                      title: str = "Call vs Put Gamma Exposure") -> go.Figure:
        """
        Create stacked bar chart showing call and put gamma exposure breakdown
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current SPX price for reference line
            title: Chart title
            
        Returns:
            Plotly Figure object
        """
        if not gamma_exposures:
            return self.create_gamma_exposure_chart(gamma_exposures, current_price, title)
        
        try:
            # Prepare data
            strikes = [ge.strike for ge in gamma_exposures]
            call_exposures = [ge.call_gamma_exposure for ge in gamma_exposures]
            put_exposures = [ge.put_gamma_exposure for ge in gamma_exposures]
            
            # Create figure
            fig = go.Figure()
            
            # Add call exposure bars
            fig.add_trace(go.Bar(
                x=strikes,
                y=call_exposures,
                name='Call Gamma Exposure',
                marker_color=self.theme['call_color'],
                hovertemplate=(
                    '<b>Strike:</b> %{x}<br>'
                    '<b>Call Gamma Exposure:</b> %{y:,.0f}<br>'
                    '<extra></extra>'
                ),
                opacity=0.8
            ))
            
            # Add put exposure bars
            fig.add_trace(go.Bar(
                x=strikes,
                y=put_exposures,
                name='Put Gamma Exposure',
                marker_color=self.theme['put_color'],
                hovertemplate=(
                    '<b>Strike:</b> %{x}<br>'
                    '<b>Put Gamma Exposure:</b> %{y:,.0f}<br>'
                    '<extra></extra>'
                ),
                opacity=0.8
            ))
            
            # Add current price line if provided
            if current_price is not None:
                fig.add_vline(
                    x=current_price,
                    line_dash="dash",
                    line_color=self.theme['current_price_color'],
                    line_width=3,
                    annotation_text=f"Current Price: {current_price:.0f}",
                    annotation_position="top"
                )
            
            # Update layout
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': self.theme['text_color']}
                },
                xaxis_title="Strike Price",
                yaxis_title="Gamma Exposure",
                height=self.chart_height,
                width=self.chart_width,
                plot_bgcolor=self.theme['background_color'],
                paper_bgcolor=self.theme['background_color'],
                font=dict(color=self.theme['text_color']),
                hovermode='x unified',
                barmode='relative',  # Stack bars
                showlegend=True
            )
            
            # Update axes
            fig.update_xaxes(
                gridcolor=self.theme['grid_color'],
                showgrid=True,
                tickformat='.0f'
            )
            fig.update_yaxes(
                gridcolor=self.theme['grid_color'],
                showgrid=True,
                tickformat='~s'
            )
            
            return fig
            
        except Exception as e:
            raise VisualizationError(f"Error creating call/put breakdown chart: {str(e)}")
    
    def highlight_walls(self, 
                       fig: go.Figure, 
                       walls: Dict[str, List[WallLevel]],
                       show_annotations: bool = True) -> go.Figure:
        """
        Add wall highlights to existing chart
        
        Args:
            fig: Existing Plotly figure
            walls: Dictionary with 'call_walls' and 'put_walls' keys
            show_annotations: Whether to show wall annotations
            
        Returns:
            Updated Plotly figure
        """
        try:
            call_walls = walls.get('call_walls', [])
            put_walls = walls.get('put_walls', [])
            
            # Add call wall highlights
            for i, wall in enumerate(call_walls):
                line_width = 4 if wall.significance_rank == 1 else 2
                opacity = 0.8 if wall.significance_rank == 1 else 0.6
                
                fig.add_vline(
                    x=wall.strike,
                    line_color=self.theme['call_color'],
                    line_width=line_width,
                    opacity=opacity,
                    line_dash="solid" if wall.significance_rank == 1 else "dot"
                )
                
                if show_annotations and wall.significance_rank <= 3:  # Only annotate top 3
                    fig.add_annotation(
                        x=wall.strike,
                        y=wall.exposure_value,
                        text=f"Call Wall #{wall.significance_rank}<br>{wall.strike:.0f}",
                        showarrow=True,
                        arrowhead=2,
                        arrowcolor=self.theme['call_color'],
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor=self.theme['call_color'],
                        font=dict(size=10, color=self.theme['text_color'])
                    )
            
            # Add put wall highlights
            for i, wall in enumerate(put_walls):
                line_width = 4 if wall.significance_rank == 1 else 2
                opacity = 0.8 if wall.significance_rank == 1 else 0.6
                
                fig.add_vline(
                    x=wall.strike,
                    line_color=self.theme['put_color'],
                    line_width=line_width,
                    opacity=opacity,
                    line_dash="solid" if wall.significance_rank == 1 else "dot"
                )
                
                if show_annotations and wall.significance_rank <= 3:  # Only annotate top 3
                    fig.add_annotation(
                        x=wall.strike,
                        y=wall.exposure_value,
                        text=f"Put Wall #{wall.significance_rank}<br>{wall.strike:.0f}",
                        showarrow=True,
                        arrowhead=2,
                        arrowcolor=self.theme['put_color'],
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor=self.theme['put_color'],
                        font=dict(size=10, color=self.theme['text_color'])
                    )
            
            return fig
            
        except Exception as e:
            raise VisualizationError(f"Error highlighting walls: {str(e)}")
    
    def create_comprehensive_chart(self, 
                                 gamma_exposures: List[GammaExposure],
                                 walls: Dict[str, List[WallLevel]],
                                 current_price: float,
                                 title: str = "SPX Gamma Exposure Analysis") -> go.Figure:
        """
        Create comprehensive chart with gamma exposure and wall highlights
        
        Args:
            gamma_exposures: List of GammaExposure objects
            walls: Dictionary with wall information
            current_price: Current SPX price
            title: Chart title
            
        Returns:
            Plotly Figure object
        """
        try:
            # Create base chart
            fig = self.create_gamma_exposure_chart(gamma_exposures, current_price, title)
            
            # Add wall highlights
            fig = self.highlight_walls(fig, walls, show_annotations=True)
            
            return fig
            
        except Exception as e:
            raise VisualizationError(f"Error creating comprehensive chart: {str(e)}")
    
    def create_metrics_summary_chart(self, 
                                   metrics_summary: Dict[str, Any],
                                   title: str = "Gamma Exposure Metrics Summary") -> go.Figure:
        """
        Create summary chart showing key metrics
        
        Args:
            metrics_summary: Dictionary with metrics data
            title: Chart title
            
        Returns:
            Plotly Figure object
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Net Gamma Distribution', 'Call vs Put Ratio', 
                              'Exposure Concentration', 'Wall Summary'),
                specs=[[{"type": "bar"}, {"type": "indicator"}],
                       [{"type": "pie"}, {"type": "table"}]]
            )
            
            # Extract core metrics
            core_metrics = metrics_summary.get('core_metrics', {})
            stats = metrics_summary.get('statistics', {})
            concentration = metrics_summary.get('concentration', {})
            
            # 1. Net Gamma Distribution (histogram-like)
            if 'percentiles' in metrics_summary:
                percentiles = metrics_summary['percentiles']
                p_values = list(percentiles.values())
                p_labels = list(percentiles.keys())
                
                fig.add_trace(
                    go.Bar(x=p_labels, y=p_values, name="Percentiles"),
                    row=1, col=1
                )
            
            # 2. Call vs Put Ratio (gauge)
            ratio = core_metrics.get('call_put_gamma_ratio', 0)
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=ratio,
                    title={'text': "Call/Put Ratio"},
                    gauge={'axis': {'range': [None, 2]},
                           'bar': {'color': "darkblue"},
                           'steps': [{'range': [0, 0.5], 'color': "lightgray"},
                                   {'range': [0.5, 1.5], 'color': "gray"}],
                           'threshold': {'line': {'color': "red", 'width': 4},
                                       'thickness': 0.75, 'value': 1}}
                ),
                row=1, col=2
            )
            
            # 3. Exposure Concentration (pie chart)
            if concentration:
                fig.add_trace(
                    go.Pie(
                        labels=['Top 5', 'Top 10', 'Others'],
                        values=[
                            concentration.get('top_5_concentration', 0) * 100,
                            (concentration.get('top_10_concentration', 0) - 
                             concentration.get('top_5_concentration', 0)) * 100,
                            (1 - concentration.get('top_10_concentration', 0)) * 100
                        ],
                        name="Concentration"
                    ),
                    row=2, col=1
                )
            
            # 4. Key Metrics Table
            metrics_data = [
                ['Total Net Gamma', f"{core_metrics.get('total_net_gamma', 0):,.0f}"],
                ['Weighted Avg Strike', f"{core_metrics.get('gamma_weighted_avg_strike', 0):.0f}"],
                ['Max Call Exposure', f"{core_metrics.get('max_call_exposure', 0):,.0f}"],
                ['Max Put Exposure', f"{core_metrics.get('max_put_exposure', 0):,.0f}"],
                ['Standard Deviation', f"{stats.get('std', 0):,.0f}"]
            ]
            
            fig.add_trace(
                go.Table(
                    header=dict(values=['Metric', 'Value'],
                              fill_color='paleturquoise',
                              align='left'),
                    cells=dict(values=[[row[0] for row in metrics_data],
                                     [row[1] for row in metrics_data]],
                             fill_color='lavender',
                             align='left')
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': self.theme['text_color']}
                },
                height=self.chart_height * 1.2,
                width=self.chart_width,
                showlegend=False,
                plot_bgcolor=self.theme['background_color'],
                paper_bgcolor=self.theme['background_color'],
                font=dict(color=self.theme['text_color'])
            )
            
            return fig
            
        except Exception as e:
            raise VisualizationError(f"Error creating metrics summary chart: {str(e)}")
    
    def add_current_price_line(self, 
                              fig: go.Figure, 
                              current_price: float,
                              label: str = "Current Price") -> go.Figure:
        """
        Add current price reference line to chart
        
        Args:
            fig: Existing Plotly figure
            current_price: Current SPX price
            label: Label for the price line
            
        Returns:
            Updated Plotly figure
        """
        try:
            fig.add_vline(
                x=current_price,
                line_dash="dash",
                line_color=self.theme['current_price_color'],
                line_width=3,
                annotation_text=f"{label}: {current_price:.0f}",
                annotation_position="top"
            )
            
            return fig
            
        except Exception as e:
            raise VisualizationError(f"Error adding current price line: {str(e)}")
    
    def export_chart_as_html(self, fig: go.Figure, filename: str) -> str:
        """
        Export chart as HTML file
        
        Args:
            fig: Plotly figure to export
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        try:
            fig.write_html(filename)
            return filename
            
        except Exception as e:
            raise VisualizationError(f"Error exporting chart as HTML: {str(e)}")
    
    def export_chart_as_image(self, fig: go.Figure, filename: str, format: str = 'png') -> str:
        """
        Export chart as image file
        
        Args:
            fig: Plotly figure to export
            filename: Output filename
            format: Image format ('png', 'jpg', 'svg', 'pdf')
            
        Returns:
            Path to exported file
        """
        try:
            fig.write_image(filename, format=format)
            return filename
            
        except Exception as e:
            raise VisualizationError(f"Error exporting chart as {format}: {str(e)}")
    
    def get_chart_data_as_dataframe(self, gamma_exposures: List[GammaExposure]) -> pd.DataFrame:
        """
        Convert gamma exposure data to DataFrame for chart data consistency validation
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            DataFrame with chart data
        """
        if not gamma_exposures:
            return pd.DataFrame()
        
        data = []
        for ge in gamma_exposures:
            data.append({
                'strike': ge.strike,
                'call_gamma_exposure': ge.call_gamma_exposure,
                'put_gamma_exposure': ge.put_gamma_exposure,
                'net_gamma_exposure': ge.net_gamma_exposure,
                'total_open_interest': ge.total_open_interest
            })
        
        return pd.DataFrame(data)