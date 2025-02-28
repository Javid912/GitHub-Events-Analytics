#!/usr/bin/env python3
"""
GitHub Event Parser

Utilities for parsing and validating GitHub events.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class Actor(BaseModel):
    """GitHub actor (user) model."""
    id: int
    login: str
    display_login: Optional[str] = None
    gravatar_id: Optional[str] = None
    url: str
    avatar_url: str


class Repository(BaseModel):
    """GitHub repository model."""
    id: int
    name: str
    url: str


class Organization(BaseModel):
    """GitHub organization model."""
    id: int
    login: str
    gravatar_id: Optional[str] = None
    url: str
    avatar_url: str


class GitHubEvent(BaseModel):
    """GitHub event model with validation."""
    id: str
    type: str
    actor: Actor
    repo: Repository
    public: bool
    created_at: datetime
    org: Optional[Organization] = None
    payload: Dict[str, Any]
    
    # Added fields
    collected_at: Optional[datetime] = None
    
    @validator('type')
    def validate_event_type(cls, v):
        """Validate that the event type is known."""
        valid_types = {
            'CommitCommentEvent', 'CreateEvent', 'DeleteEvent', 'ForkEvent',
            'GollumEvent', 'IssueCommentEvent', 'IssuesEvent', 'MemberEvent',
            'PublicEvent', 'PullRequestEvent', 'PullRequestReviewEvent',
            'PullRequestReviewCommentEvent', 'PushEvent', 'ReleaseEvent',
            'SponsorshipEvent', 'WatchEvent'
        }
        if v not in valid_types:
            # We don't want to reject unknown event types, just log a warning
            # GitHub may add new event types in the future
            print(f"Warning: Unknown event type '{v}'")
        return v


def extract_languages(event: Dict[str, Any]) -> List[str]:
    """
    Extract programming languages from a GitHub event if available.
    
    Args:
        event: GitHub event data
        
    Returns:
        List of programming languages or empty list if not available
    """
    languages = []
    
    # Extract from repository language data if available
    if event.get('type') == 'PushEvent' and 'payload' in event:
        payload = event['payload']
        if 'commits' in payload and payload['commits']:
            for commit in payload['commits']:
                if 'languages' in commit:
                    languages.extend(commit['languages'])
    
    # Extract from repository creation event
    if event.get('type') == 'CreateEvent' and 'payload' in event:
        payload = event['payload']
        if payload.get('ref_type') == 'repository' and 'language' in payload:
            languages.append(payload['language'])
    
    return list(set(languages))  # Remove duplicates


def extract_repository_metrics(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract repository metrics from a GitHub event.
    
    Args:
        event: GitHub event data
        
    Returns:
        Dictionary of repository metrics
    """
    metrics = {
        'repo_id': None,
        'repo_name': None,
        'stars': None,
        'forks': None,
        'watchers': None,
        'open_issues': None,
    }
    
    # Basic repository info
    if 'repo' in event:
        metrics['repo_id'] = event['repo'].get('id')
        metrics['repo_name'] = event['repo'].get('name')
    
    # Extract metrics from specific event types
    if event.get('type') == 'WatchEvent' and 'payload' in event:
        # Star event
        if event['payload'].get('action') == 'started':
            metrics['stars'] = 1  # Increment
    
    elif event.get('type') == 'ForkEvent':
        metrics['forks'] = 1  # Increment
    
    # For PullRequestEvent and IssuesEvent, we might have repository stats
    elif event.get('type') in ('PullRequestEvent', 'IssuesEvent') and 'payload' in event:
        payload = event['payload']
        if 'repository' in payload:
            repo = payload['repository']
            metrics['stars'] = repo.get('stargazers_count')
            metrics['forks'] = repo.get('forks_count')
            metrics['watchers'] = repo.get('watchers_count')
            metrics['open_issues'] = repo.get('open_issues_count')
    
    return metrics


def validate_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a GitHub event using the Pydantic model.
    
    Args:
        event_data: Raw GitHub event data
        
    Returns:
        Validated event data (may include additional derived fields)
        
    Raises:
        ValidationError: If the event data is invalid
    """
    # Parse and validate the event
    event = GitHubEvent.parse_obj(event_data)
    
    # Convert back to dict for Kafka
    validated_data = event.dict()
    
    # Add derived fields
    validated_data['languages'] = extract_languages(event_data)
    validated_data['repository_metrics'] = extract_repository_metrics(event_data)
    
    return validated_data 