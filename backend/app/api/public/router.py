#!/usr/bin/env python3
"""
Public API Router
RESTful API following external API pattern for user-facing operations
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel

from .dependencies import rate_limit
from .rate_limiter import rate_limiter
from ...extraction_service import UserPreferences
from ...event_service import EventCrawler
from ...cache_manager import CacheManager
from ...search_service import SearchService
from ...extraction_service import ExtractionService
from ...usage_tracker import UsageTracker
from ...conversation_storage import ConversationStorage

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/public", tags=["public"])

# Initialize services (reuse from main.py pattern)
event_crawler = EventCrawler()
cache_manager = CacheManager(ttl_hours=6)  # Match main.py CACHE_TTL_HOURS
search_service = SearchService()
extraction_service = ExtractionService()
usage_tracker = UsageTracker()
conversation_storage = ConversationStorage()

# Pydantic models (matching main.py)
class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []
    llm_provider: str = "openai"
    user_preferences: Optional[UserPreferences] = None
    is_initial_response: bool = False
    conversation_id: Optional[str] = None
    # Note: user_id is extracted from token, not from request

class ChatResponse(BaseModel):
    message: str
    recommendations: List[Dict[str, Any]] = []
    llm_provider_used: str
    cache_used: bool = False
    cache_age_hours: Optional[float] = None
    extracted_preferences: Optional[UserPreferences] = None
    extraction_summary: Optional[str] = None
    usage_stats: Optional[Dict[str, Any]] = None
    trial_exceeded: bool = False
    conversation_id: str


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def public_chat(
    request: ChatRequest,
    response: Response,
    rate_limit_result: tuple[str, dict] = Depends(rate_limit)
):
    """
    Public chat endpoint with Firebase authentication and rate limiting
    Users can only access their own conversations
    
    Rate Limit: 10 requests per 60 seconds (configurable via environment variables)
    """
    try:
        # Extract user_id and rate_limit_info from dependency
        user_id, rate_limit_info = rate_limit_result
        
        # Add rate limit headers to response
        rate_limiter.add_rate_limit_headers(response, rate_limit_info)
        logger.info(f"Public API chat request from user {user_id}: {request.message}")
        
        # Permission check: Verify conversation belongs to authenticated user
        if request.conversation_id:
            try:
                conversation = conversation_storage.get_conversation(user_id, request.conversation_id)
                if not conversation:
                    raise HTTPException(
                        status_code=404,
                        detail="Conversation not found"
                    )
                # Verify the conversation actually belongs to this user
                # (get_conversation already checks this via Firestore path, but explicit check for clarity)
                conv_user_id = conversation.get("user_id")
                if conv_user_id and conv_user_id != user_id:
                    logger.warning(
                        f"User {user_id} attempted to access conversation {request.conversation_id} "
                        f"belonging to user {conv_user_id}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="You do not have permission to access this conversation"
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error verifying conversation ownership: {e}")
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )
        
        # Check trial limit for anonymous users (if they somehow got a token)
        if user_id.startswith("user_"):  # Anonymous user
            if usage_tracker.check_trial_limit(user_id):
                trial_limit = usage_tracker.trial_limit
                return ChatResponse(
                    message=(
                        f"🔒 You've reached your free trial limit of {trial_limit} interactions! "
                        f"Please register to continue using our service and keep your conversation history."
                    ),
                    recommendations=[],
                    llm_provider_used=request.llm_provider,
                    cache_used=False,
                    trial_exceeded=True,
                    usage_stats=usage_tracker.get_usage(user_id),
                    conversation_id="temp"
                )

        # Increment usage for anonymous users
        if user_id.startswith("user_"):
            usage_stats = usage_tracker.increment_usage(user_id)
        else:
            usage_stats = None

        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = conversation_storage.create_conversation(user_id, {
                "llm_provider": request.llm_provider
            })

        # Save user message
        conversation_storage.save_message(user_id, conversation_id, {
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 1: Extract user preferences if this is an initial response
        extracted_preferences = None
        if request.is_initial_response:
            logger.info("Initial response detected, extracting user preferences")
            extracted_preferences = extraction_service.extract_user_preferences(request.message)
            logger.info(f"Extracted preferences: {extracted_preferences}")
        
        # Step 2: Determine city to use (prioritize extracted preferences)
        city = None
        location_provided = False
        
        # Priority 1: Use extracted location from preferences
        if extracted_preferences and extracted_preferences.location and extracted_preferences.location != "none":
            city = extracted_preferences.location.lower()
            location_provided = True
            logger.info(f"Using city from extracted preferences: {city}")
        
        # Priority 2: Try to extract city from query using existing method
        if not city:
            query_city = extraction_service.extract_location_from_query(request.message)
            if query_city:
                city = query_city.lower()
                location_provided = True
                logger.info(f"Using city from query extraction: {city}")
        
        # Step 3: Handle missing location for initial responses
        if request.is_initial_response and not location_provided:
            logger.info("No location provided in initial response, asking user for location")
            supported_cities = event_crawler.eventbrite_crawler.get_supported_cities()
            formatted_cities = [c.replace('_', ' ').title() for c in supported_cities]
            cities_list = ", ".join(formatted_cities)
            location_message = (
                f"I'd be happy to help you find events! "
                f"To give you the best recommendations, could you please tell me "
                f"which city or area you're interested in? "
                f"(e.g., {cities_list}, or a zipcode)"
            )
            return ChatResponse(
                message=location_message,
                recommendations=[],
                llm_provider_used=request.llm_provider,
                cache_used=False,
                cache_age_hours=None,
                extracted_preferences=extracted_preferences,
                extraction_summary=None,
                conversation_id=conversation_id
            )
        
        # Step 4: Default fallback for non-initial responses or when location still missing
        if not city:
            city = "new york"
            logger.info("No city found, defaulting to New York")
            if not request.is_initial_response:
                logger.info("Informing user that we're defaulting to New York")
        
        logger.info(f"Final city decision: {city}")
        
        # Step 5: Try to get cached events (will fetch fresh if expired)
        cached_events = cache_manager.get_cached_events(city, event_crawler)
        cache_age_hours = cache_manager.get_cache_age(city)

        if cached_events:
            logger.info(f"Using cached events for {city} (age: {cache_age_hours:.1f}h)")
            events = cached_events
            cache_used = cache_age_hours is not None and cache_age_hours > 0
        else:
            logger.warning(f"Failed to get any events for {city}")
            events = []
            cache_used = False
            cache_age_hours = None
        
        # Step 6: LLM-powered intelligent event search with preferences
        logger.info(f"Starting LLM search for query: '{request.message}' with {len(events)} events")
        
        # Convert UserPreferences object to dict for search service
        user_preferences_dict = None
        if extracted_preferences:
            user_preferences_dict = {
                'location': extracted_preferences.location,
                'date': extracted_preferences.date,
                'time': extracted_preferences.time,
                'event_type': extracted_preferences.event_type
            }
        
        top_events = await search_service.intelligent_event_search(
            request.message, 
            events, 
            user_preferences=user_preferences_dict
        )
        logger.info(f"LLM search returned {len(top_events)} events")
        
        # Step 7: Format recommendations
        formatted_recommendations = []
        for event in top_events:
            formatted_recommendations.append({
                "type": "event",
                "data": {
                    **event,
                    "source": "cached" if cache_used else "realtime"
                },
                "relevance_score": event.get('relevance_score', 0.5),
                "explanation": f"Event in {city.title()}: {event.get('title', 'Unknown Event')}"
            })
        
        # Step 8: Generate response message
        location_note = ""
        if not location_provided and city == "new york":
            location_note = " (I couldn't determine your location, so I'm defaulting to New York)"
        
        if top_events:
            response_message = (
                f"🎉 Found {len(top_events)} events in {city.title()} that match your search!"
                f"{location_note} Check out the recommendations below ↓"
            )
        else:
            response_message = (
                f"😔 I couldn't find any events in {city.title()} matching your query."
                f"{location_note} Try asking about 'fashion events', 'music concerts', "
                f"'halloween parties', or 'free events'."
            )
        
        # Step 9: Create extraction summary if preferences were extracted
        extraction_summary = None
        if extracted_preferences:
            summary_parts = []
            if extracted_preferences.location and extracted_preferences.location != "none":
                summary_parts.append(f"📍 {extracted_preferences.location}")
            if extracted_preferences.date and extracted_preferences.date != "none":
                summary_parts.append(f"📅 {extracted_preferences.date}")
            if extracted_preferences.time and extracted_preferences.time != "none":
                summary_parts.append(f"🕐 {extracted_preferences.time}")
            if extracted_preferences.event_type and extracted_preferences.event_type != "none":
                summary_parts.append(f"🎭 {extracted_preferences.event_type}")
            
            if summary_parts:
                extraction_summary = " • ".join(summary_parts)
        
        # Save assistant response
        conversation_storage.save_message(user_id, conversation_id, {
            "role": "assistant",
            "content": response_message,
            "timestamp": datetime.now().isoformat(),
            "recommendations": formatted_recommendations,
            "extracted_preferences": extracted_preferences.dict() if extracted_preferences else None,
            "cache_used": cache_used,
            "cache_age_hours": cache_age_hours
        })

        # Update conversation metadata
        conversation_storage.update_metadata(user_id, conversation_id, {
            "last_message_at": datetime.now().isoformat()
        })
        
        return ChatResponse(
            message=response_message,
            recommendations=formatted_recommendations,
            llm_provider_used=request.llm_provider,
            cache_used=cache_used,
            cache_age_hours=cache_age_hours,
            extracted_preferences=extracted_preferences,
            extraction_summary=extraction_summary,
            usage_stats=usage_stats,
            trial_exceeded=False,
            conversation_id=conversation_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (auth errors, etc.)
        raise
    except Exception as e:
        logger.error(f"Error in public chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )
