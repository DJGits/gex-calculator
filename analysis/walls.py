"""
Wall analysis for identifying gamma support and resistance levels
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

from data.models import GammaExposure, WallLevel


class WallAnalysisError(Exception):
    """Custom exception for wall analysis errors"""
    pass


class WallAnalyzer:
    """Analyzes gamma exposure to identify call walls and put walls"""
    
    def __init__(self, min_significance_threshold: float = 0.05):
        """
        Initialize wall analyzer
        
        Args:
            min_significance_threshold: Minimum percentage of total exposure to be considered significant
        """
        self.min_significance_threshold = min_significance_threshold
    
    def find_call_walls(self, 
                       gamma_exposures: List[GammaExposure], 
                       current_price: float,
                       max_walls: int = 5) -> List[WallLevel]:
        """
        Identify call walls (resistance levels) from gamma exposure data
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current SPX price
            max_walls: Maximum number of walls to return
            
        Returns:
            List of WallLevel objects representing call walls
        """
        if not gamma_exposures:
            return []
        
        # Filter for strikes with significant negative call gamma exposure (resistance)
        call_candidates = []
        
        for ge in gamma_exposures:
            # Call walls are where market makers have large negative gamma exposure
            # This creates resistance as they need to sell when price rises
            if ge.call_gamma_exposure < 0:  # Negative exposure indicates resistance
                call_candidates.append({
                    'strike': ge.strike,
                    'exposure': abs(ge.call_gamma_exposure),  # Use absolute value for ranking
                    'raw_exposure': ge.call_gamma_exposure,
                    'distance': abs(ge.strike - current_price)
                })
        
        if not call_candidates:
            return []
        
        # Sort by exposure magnitude (descending)
        call_candidates.sort(key=lambda x: x['exposure'], reverse=True)
        
        # Calculate significance threshold
        total_call_exposure = sum(abs(ge.call_gamma_exposure) for ge in gamma_exposures if ge.call_gamma_exposure < 0)
        significance_threshold = total_call_exposure * self.min_significance_threshold
        
        # Create WallLevel objects
        call_walls = []
        rank = 1
        
        for candidate in call_candidates[:max_walls]:
            if candidate['exposure'] >= significance_threshold:
                wall = WallLevel(
                    strike=candidate['strike'],
                    exposure_value=candidate['raw_exposure'],
                    wall_type='call_wall',
                    distance_from_spot=candidate['distance'],
                    significance_rank=rank
                )
                call_walls.append(wall)
                rank += 1
        
        return call_walls
    
    def find_put_walls(self, 
                      gamma_exposures: List[GammaExposure], 
                      current_price: float,
                      max_walls: int = 5) -> List[WallLevel]:
        """
        Identify put walls (support levels) from gamma exposure data
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current SPX price
            max_walls: Maximum number of walls to return
            
        Returns:
            List of WallLevel objects representing put walls
        """
        if not gamma_exposures:
            return []
        
        # Filter for strikes with significant positive put gamma exposure (support)
        put_candidates = []
        
        for ge in gamma_exposures:
            # Put walls are where market makers have large positive gamma exposure
            # This creates support as they need to buy when price falls
            if ge.put_gamma_exposure > 0:  # Positive exposure indicates support
                put_candidates.append({
                    'strike': ge.strike,
                    'exposure': ge.put_gamma_exposure,
                    'raw_exposure': ge.put_gamma_exposure,
                    'distance': abs(ge.strike - current_price)
                })
        
        if not put_candidates:
            return []
        
        # Sort by exposure magnitude (descending)
        put_candidates.sort(key=lambda x: x['exposure'], reverse=True)
        
        # Calculate significance threshold
        total_put_exposure = sum(ge.put_gamma_exposure for ge in gamma_exposures if ge.put_gamma_exposure > 0)
        significance_threshold = total_put_exposure * self.min_significance_threshold
        
        # Create WallLevel objects
        put_walls = []
        rank = 1
        
        for candidate in put_candidates[:max_walls]:
            if candidate['exposure'] >= significance_threshold:
                wall = WallLevel(
                    strike=candidate['strike'],
                    exposure_value=candidate['raw_exposure'],
                    wall_type='put_wall',
                    distance_from_spot=candidate['distance'],
                    significance_rank=rank
                )
                put_walls.append(wall)
                rank += 1
        
        return put_walls
    
    def find_all_walls(self, 
                      gamma_exposures: List[GammaExposure], 
                      current_price: float,
                      max_walls_per_type: int = 5) -> Dict[str, List[WallLevel]]:
        """
        Find both call walls and put walls
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current SPX price
            max_walls_per_type: Maximum number of walls per type
            
        Returns:
            Dictionary with 'call_walls' and 'put_walls' keys
        """
        try:
            call_walls = self.find_call_walls(gamma_exposures, current_price, max_walls_per_type)
            put_walls = self.find_put_walls(gamma_exposures, current_price, max_walls_per_type)
            
            return {
                'call_walls': call_walls,
                'put_walls': put_walls
            }
            
        except Exception as e:
            raise WallAnalysisError(f"Error finding walls: {str(e)}")
    
    def calculate_wall_distances(self, 
                               walls: List[WallLevel], 
                               current_price: float) -> List[WallLevel]:
        """
        Calculate and update distances from current price to walls
        
        Args:
            walls: List of WallLevel objects
            current_price: Current SPX price
            
        Returns:
            Updated list of WallLevel objects with correct distances
        """
        updated_walls = []
        
        for wall in walls:
            # Create new wall with updated distance
            updated_wall = WallLevel(
                strike=wall.strike,
                exposure_value=wall.exposure_value,
                wall_type=wall.wall_type,
                distance_from_spot=abs(wall.strike - current_price),
                significance_rank=wall.significance_rank
            )
            updated_walls.append(updated_wall)
        
        return updated_walls
    
    def get_nearest_walls(self, 
                         walls: Dict[str, List[WallLevel]], 
                         current_price: float,
                         max_distance_pct: float = 0.1) -> Dict[str, List[WallLevel]]:
        """
        Filter walls to only include those within a certain distance of current price
        
        Args:
            walls: Dictionary of wall lists
            current_price: Current SPX price
            max_distance_pct: Maximum distance as percentage of current price
            
        Returns:
            Filtered dictionary of nearby walls
        """
        max_distance = current_price * max_distance_pct
        
        nearby_walls = {}
        
        for wall_type, wall_list in walls.items():
            nearby = [wall for wall in wall_list if wall.distance_from_spot <= max_distance]
            nearby_walls[wall_type] = nearby
        
        return nearby_walls
    
    def get_wall_summary(self, 
                        walls: Dict[str, List[WallLevel]], 
                        current_price: float) -> Dict[str, Any]:
        """
        Generate summary statistics for identified walls
        
        Args:
            walls: Dictionary of wall lists
            current_price: Current SPX price
            
        Returns:
            Dictionary containing wall summary statistics
        """
        call_walls = walls.get('call_walls', [])
        put_walls = walls.get('put_walls', [])
        
        summary = {
            'total_walls': len(call_walls) + len(put_walls),
            'call_walls_count': len(call_walls),
            'put_walls_count': len(put_walls),
            'current_price': current_price
        }
        
        # Primary walls (rank 1)
        primary_call_wall = next((w for w in call_walls if w.significance_rank == 1), None)
        primary_put_wall = next((w for w in put_walls if w.significance_rank == 1), None)
        
        if primary_call_wall:
            summary['primary_call_wall'] = {
                'strike': primary_call_wall.strike,
                'exposure': primary_call_wall.exposure_value,
                'distance': primary_call_wall.distance_from_spot,
                'distance_pct': (primary_call_wall.distance_from_spot / current_price) * 100
            }
        
        if primary_put_wall:
            summary['primary_put_wall'] = {
                'strike': primary_put_wall.strike,
                'exposure': primary_put_wall.exposure_value,
                'distance': primary_put_wall.distance_from_spot,
                'distance_pct': (primary_put_wall.distance_from_spot / current_price) * 100
            }
        
        # Nearest walls
        all_walls = call_walls + put_walls
        if all_walls:
            nearest_wall = min(all_walls, key=lambda w: w.distance_from_spot)
            summary['nearest_wall'] = {
                'type': nearest_wall.wall_type,
                'strike': nearest_wall.strike,
                'distance': nearest_wall.distance_from_spot,
                'distance_pct': (nearest_wall.distance_from_spot / current_price) * 100
            }
        
        # Average distances
        if call_walls:
            avg_call_distance = sum(w.distance_from_spot for w in call_walls) / len(call_walls)
            summary['avg_call_wall_distance'] = avg_call_distance
            summary['avg_call_wall_distance_pct'] = (avg_call_distance / current_price) * 100
        
        if put_walls:
            avg_put_distance = sum(w.distance_from_spot for w in put_walls) / len(put_walls)
            summary['avg_put_wall_distance'] = avg_put_distance
            summary['avg_put_wall_distance_pct'] = (avg_put_distance / current_price) * 100
        
        return summary
    
    def rank_walls_by_significance(self, 
                                 walls: List[WallLevel], 
                                 total_exposure: float) -> List[WallLevel]:
        """
        Re-rank walls by their significance relative to total exposure
        
        Args:
            walls: List of WallLevel objects
            total_exposure: Total gamma exposure for normalization
            
        Returns:
            Re-ranked list of WallLevel objects
        """
        if not walls or total_exposure == 0:
            return walls
        
        # Calculate significance scores
        wall_scores = []
        for wall in walls:
            significance_score = abs(wall.exposure_value) / abs(total_exposure)
            wall_scores.append((wall, significance_score))
        
        # Sort by significance score (descending)
        wall_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Create new walls with updated ranks
        ranked_walls = []
        for rank, (wall, score) in enumerate(wall_scores, 1):
            ranked_wall = WallLevel(
                strike=wall.strike,
                exposure_value=wall.exposure_value,
                wall_type=wall.wall_type,
                distance_from_spot=wall.distance_from_spot,
                significance_rank=rank
            )
            ranked_walls.append(ranked_wall)
        
        return ranked_walls