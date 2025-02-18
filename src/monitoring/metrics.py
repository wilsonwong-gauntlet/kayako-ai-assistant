"""Metrics tracking for the voice assistant."""

import time
from typing import Dict, Optional
from datetime import datetime
import sentry_sdk

class CallMetrics:
    """Track metrics for a single call."""
    
    def __init__(self, call_sid: str):
        self.call_sid = call_sid
        self.start_time = time.time()
        self.last_interaction = self.start_time
        self.total_tokens = 0
        self.transcription_confidences: list[float] = []
        self.kb_searches = 0
        self.tickets_created = 0
        self.resolved_by_kb = False
        self.escalated = False
        
    def track_transcription(self, confidence: float) -> None:
        """Track a transcription event."""
        self.transcription_confidences.append(confidence)
        self.last_interaction = time.time()
        
        # Send metrics to Sentry
        sentry_sdk.set_measurement(
            "transcription_confidence",
            confidence,
            unit="ratio"
        )
    
    def track_tokens(self, completion_tokens: int, prompt_tokens: int) -> None:
        """Track token usage."""
        total = completion_tokens + prompt_tokens
        self.total_tokens += total
        
        # Send metrics to Sentry
        sentry_sdk.set_measurement(
            "tokens_used",
            total,
            unit="token"
        )
        
    def track_kb_search(self, found_relevant: bool) -> None:
        """Track knowledge base search."""
        self.kb_searches += 1
        if found_relevant:
            self.resolved_by_kb = True
            
        # Send metrics to Sentry
        sentry_sdk.set_measurement(
            "kb_searches",
            1,
            unit="search"
        )
        sentry_sdk.set_tag("kb_resolution", str(found_relevant))
    
    def track_ticket_creation(self) -> None:
        """Track ticket creation."""
        self.tickets_created += 1
        self.escalated = True
        
        # Send metrics to Sentry
        sentry_sdk.set_measurement(
            "tickets_created",
            1,
            unit="ticket"
        )
    
    def end_call(self) -> None:
        """Track call completion metrics."""
        duration = time.time() - self.start_time
        idle_time = time.time() - self.last_interaction
        
        # Send final metrics to Sentry
        sentry_sdk.set_measurement(
            "call_duration",
            duration,
            unit="second"
        )
        sentry_sdk.set_measurement(
            "idle_time",
            idle_time,
            unit="second"
        )
        
        # Set final tags
        sentry_sdk.set_tag("resolution_type", 
            "kb" if self.resolved_by_kb else "escalated" if self.escalated else "unknown")
        sentry_sdk.set_tag("transcription_quality",
            "high" if all(c > 0.9 for c in self.transcription_confidences)
            else "medium" if all(c > 0.7 for c in self.transcription_confidences)
            else "low")

class MetricsManager:
    """Manage metrics for all active calls."""
    
    def __init__(self):
        self.active_calls: Dict[str, CallMetrics] = {}
    
    def start_call(self, call_sid: str) -> None:
        """Start tracking metrics for a new call."""
        self.active_calls[call_sid] = CallMetrics(call_sid)
        
        # Start Sentry transaction
        sentry_sdk.start_transaction(
            op="call",
            name=f"voice_call_{call_sid}",
            description="Voice call handling"
        )
    
    def get_call_metrics(self, call_sid: str) -> Optional[CallMetrics]:
        """Get metrics for a specific call."""
        return self.active_calls.get(call_sid)
    
    def end_call(self, call_sid: str) -> None:
        """End metrics tracking for a call."""
        if call_sid in self.active_calls:
            metrics = self.active_calls[call_sid]
            metrics.end_call()
            del self.active_calls[call_sid]

# Global metrics manager instance
metrics_manager = MetricsManager() 