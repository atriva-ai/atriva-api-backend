"""
Analytics type constants and configurations
"""

from enum import Enum
from typing import Dict, Any

class AnalyticsType(str, Enum):
    PEOPLE_COUNTING = "people_counting"
    DWELL_TIME = "dwell_time"
    DEMOGRAPHIC = "demographic"

class AnalyticsConfig:
    """Predefined analytics configurations"""
    
    PEOPLE_COUNTING = {
        "name": "People Counting",
        "type": AnalyticsType.PEOPLE_COUNTING,
        "description": "Track the number of people entering and exiting areas",
        "default_config": {
            "threshold": 0.5,
            "min_height": 100,
            "max_height": 300,
            "tracking_enabled": True,
            "count_direction": "both",  # "in", "out", "both"
            "reset_interval": 3600  # seconds
        }
    }
    
    DWELL_TIME = {
        "name": "Dwell Time Analysis",
        "type": AnalyticsType.DWELL_TIME,
        "description": "Analyze how long people spend in specific areas",
        "default_config": {
            "min_dwell_time": 5,  # seconds
            "max_dwell_time": 300,  # seconds
            "zone_detection": True,
            "heatmap_enabled": True,
            "tracking_interval": 1,  # seconds
            "session_timeout": 30  # seconds
        }
    }
    
    DEMOGRAPHIC = {
        "name": "Demographic Analytics",
        "type": AnalyticsType.DEMOGRAPHIC,
        "description": "Analyze demographic information of visitors",
        "default_config": {
            "age_groups": ["18-25", "26-35", "36-45", "46-55", "55+"],
            "gender_detection": True,
            "emotion_analysis": True,
            "privacy_mode": True,
            "confidence_threshold": 0.7,
            "anonymize_data": True
        }
    }

def get_analytics_config(analytics_type: AnalyticsType) -> Dict[str, Any]:
    """Get configuration for a specific analytics type"""
    configs = {
        AnalyticsType.PEOPLE_COUNTING: AnalyticsConfig.PEOPLE_COUNTING,
        AnalyticsType.DWELL_TIME: AnalyticsConfig.DWELL_TIME,
        AnalyticsType.DEMOGRAPHIC: AnalyticsConfig.DEMOGRAPHIC,
    }
    return configs.get(analytics_type, {})

def get_all_analytics_configs() -> Dict[str, Dict[str, Any]]:
    """Get all predefined analytics configurations"""
    return {
        AnalyticsType.PEOPLE_COUNTING: AnalyticsConfig.PEOPLE_COUNTING,
        AnalyticsType.DWELL_TIME: AnalyticsConfig.DWELL_TIME,
        AnalyticsType.DEMOGRAPHIC: AnalyticsConfig.DEMOGRAPHIC,
    } 