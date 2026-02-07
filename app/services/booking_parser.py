import spacy
import re
import dateutil.parser as date_parser
from datetime import datetime, timedelta, date, time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BookingStatus(Enum):
    DETECTED = "detected"
    INCOMPLETE = "incomplete"
    VALID = "valid"
    INVALID = "invalid"


@dataclass
class BookingInfo:
    name: Optional[str] = None
    email: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD format
    time: Optional[str] = None  # HH:MM format
    interview_type: Optional[str] = None
    status: BookingStatus = BookingStatus.INCOMPLETE
    confidence: float = 0.0
    missing_fields: Optional[List[str]] = None
    extracted_text: str = ""

    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []


class BookingParser:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            logger.error("spaCy model 'en_core_web_sm' not found. Please install it.")
            self.nlp = None

        self.booking_keywords = [
            "book",
            "schedule",
            "appointment",
            "interview",
            "meeting",
            "slot",
            "time",
            "date",
            "available",
            "reserve",
            "set up",
            "arrange",
        ]

        # Email regex pattern
        self.email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        # Interview type keywords
        self.interview_types = {
            "technical": [
                "technical",
                "coding",
                "programming",
                "development",
                "engineer",
                "software",
                "algorithm",
            ],
            "hr": [
                "hr",
                "human resources",
                "behavioral",
                "culture",
                "recruiter",
                "hiring",
            ],
            "phone": ["phone", "call", "voice", "telephone", "ring"],
            "video": ["video", "zoom", "teams", "meet", "online", "virtual", "skype"],
            "onsite": ["onsite", "in-person", "office", "visit", "face-to-face"],
        }

    def detect_booking_intent(self, text: str) -> bool:
        """Detect if text contains booking intent using spaCy"""
        if not self.nlp:
            # Fallback to simple keyword matching
            return any(keyword in text.lower() for keyword in self.booking_keywords)

        doc = self.nlp(text.lower())

        # Check for booking keywords
        booking_score = 0
        for token in doc:
            if token.lemma_ in self.booking_keywords:
                booking_score += 1

        # Look for time-related entities
        has_temporal = False
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME", "CARDINAL"]:
                has_temporal = True
                booking_score += 0.5

        return booking_score >= 1 or (has_temporal and booking_score > 0)

    def extract_person_names(self, text: str) -> List[str]:
        """Extract person names using spaCy NER"""
        if not self.nlp:
            return []

        doc = self.nlp(text)
        names = []

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Clean and validate name
                name = ent.text.strip()
                if len(name) > 1 and len(name.split()) <= 5:  # Reasonable name length
                    names.append(name)

        # Also check for patterns like "My name is X" or "I'm X"
        name_patterns = [
            r"(?:my name is|i am|i\'m|call me|this is)\s+([A-Z][a-zA-Z\s]+)",
            r"(?:from|signed)\s+([A-Z][a-zA-Z\s]+)",
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if len(name) > 1 and name not in names:
                    names.append(name)

        return names

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address using regex"""
        matches = re.findall(self.email_pattern, text)
        return matches[0] if matches else None

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates using spaCy + dateutil"""
        dates = []

        if self.nlp:
            doc = self.nlp(text)

            # Extract DATE entities from spaCy
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    try:
                        # Use dateutil to parse the date
                        parsed_date = date_parser.parse(ent.text, fuzzy=True)
                        # Ensure it's not in the past (with 1-day tolerance)
                        if parsed_date.date() >= datetime.now().date() - timedelta(
                            days=1
                        ):
                            date_str = parsed_date.strftime("%Y-%m-%d")
                            if date_str not in dates:
                                dates.append(date_str)
                    except (ValueError, OverflowError):
                        continue

        # Also try common date patterns
        date_patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # MM/DD/YYYY
            r"\b\d{1,2}-\d{1,2}-\d{4}\b",  # MM-DD-YYYY
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    parsed_date = date_parser.parse(match)
                    if parsed_date.date() >= datetime.now().date():
                        date_str = parsed_date.strftime("%Y-%m-%d")
                        if date_str not in dates:
                            dates.append(date_str)
                except:
                    continue

        return dates

    def extract_times(self, text: str) -> List[str]:
        """Extract times using spaCy + regex patterns"""
        times = []

        if self.nlp:
            doc = self.nlp(text)

            # Extract TIME entities from spaCy
            for ent in doc.ents:
                if ent.label_ == "TIME":
                    normalized_time = self._normalize_time(ent.text)
                    if normalized_time and normalized_time not in times:
                        times.append(normalized_time)

        # Common time patterns
        time_patterns = [
            r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b",
            r"\b\d{1,2}\s*(?:AM|PM|am|pm)\b",
            r"\b(?:noon|midnight)\b",
        ]

        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                normalized_time = self._normalize_time(match)
                if normalized_time and normalized_time not in times:
                    times.append(normalized_time)

        return times

    def _normalize_time(self, time_str: str) -> Optional[str]:
        """Normalize time to HH:MM 24-hour format"""
        try:
            time_str = time_str.strip().lower()

            # Handle special cases
            if "noon" in time_str:
                return "12:00"
            elif "midnight" in time_str:
                return "00:00"

            # Parse various formats
            if "pm" in time_str or "am" in time_str:
                # Remove am/pm and clean
                time_clean = re.sub(r"\s*(am|pm)\s*", "", time_str)

                if ":" not in time_clean:
                    time_clean += ":00"

                try:
                    time_obj = datetime.strptime(time_clean, "%H:%M").time()
                    hours = time_obj.hour
                    minutes = time_obj.minute

                    # Adjust for PM/AM
                    if "pm" in time_str and hours != 12:
                        hours += 12
                    elif "am" in time_str and hours == 12:
                        hours = 0

                    return f"{hours:02d}:{minutes:02d}"
                except ValueError:
                    return None
            else:
                # Assume 24-hour format
                if ":" not in time_str:
                    if len(time_str) <= 2:
                        time_str += ":00"
                    else:
                        return None  # Invalid format

                try:
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
                    return f"{time_obj.hour:02d}:{time_obj.minute:02d}"
                except ValueError:
                    return None

        except Exception as e:
            logger.debug(f"Time normalization error for '{time_str}': {e}")
            return None

    def extract_interview_type(self, text: str) -> str:
        """Extract interview type based on keywords and context"""
        if self.nlp:
            doc = self.nlp(text.lower())

            # Use spaCy tokens for better matching
            tokens = [token.lemma_ for token in doc]

            for interview_type, keywords in self.interview_types.items():
                for keyword in keywords:
                    if keyword in tokens:
                        return interview_type
        else:
            # Fallback to simple matching
            text_lower = text.lower()
            for interview_type, keywords in self.interview_types.items():
                if any(keyword in text_lower for keyword in keywords):
                    return interview_type

        return "general"

    async def parse_booking_request(self, text: str) -> BookingInfo:
        """Parse booking request using spaCy"""
        booking_info = BookingInfo(extracted_text=text)

        # Check booking intent first
        if not self.detect_booking_intent(text):
            booking_info.status = BookingStatus.INCOMPLETE
            booking_info.confidence = 0.1
            return booking_info

        booking_info.status = BookingStatus.DETECTED
        booking_info.confidence = 0.4

        # Extract information using spaCy
        names = self.extract_person_names(text)
        booking_info.name = names[0] if names else None

        booking_info.email = self.extract_email(text)

        dates = self.extract_dates(text)
        booking_info.date = dates[0] if dates else None

        times = self.extract_times(text)
        booking_info.time = times[0] if times else None

        booking_info.interview_type = self.extract_interview_type(text)

        # Determine missing fields
        missing_fields = []
        if not booking_info.name:
            missing_fields.append("name")
        if not booking_info.email:
            missing_fields.append("email")
        if not booking_info.date:
            missing_fields.append("date")
        if not booking_info.time:
            missing_fields.append("time")

        booking_info.missing_fields = missing_fields

        # Calculate final status and confidence
        if not missing_fields:
            booking_info.status = BookingStatus.VALID
            booking_info.confidence = 0.9
        elif len(missing_fields) <= 2:
            booking_info.status = BookingStatus.INCOMPLETE
            booking_info.confidence = 0.7
        else:
            booking_info.status = BookingStatus.INCOMPLETE
            booking_info.confidence = 0.5

        return booking_info

    async def process_booking_with_llm(self, text: str, llm_service) -> BookingInfo:
        """Hybrid approach: spaCy + LLM for maximum accuracy"""
        try:
            # First pass: spaCy extraction
            spacy_result = await self.parse_booking_request(text)

            # If spaCy found everything, use it
            if spacy_result.status == BookingStatus.VALID:
                spacy_result.confidence = (
                    0.95  # High confidence for complete spaCy results
                )
                return spacy_result

            # Enhance with LLM for missing information
            prompt = f"""Extract booking/interview information from this message. Focus on missing details.

user_message: {text}

Current extracted info:
- Name: {spacy_result.name or 'missing'}
- Email: {spacy_result.email or 'missing'}  
- Date: {spacy_result.date or 'missing'}
- Time: {spacy_result.time or 'missing'}

Extract and return in this format:
name: [full person name or 'not_found']
email: [email address or 'not_found']
date: [date in YYYY-MM-DD format or 'not_found']  
time: [time in HH:MM format or 'not_found']
type: [technical/hr/phone/video/onsite/general]
intent: [booking/scheduling or 'none']

response:"""

            llm_response = await llm_service._call_ollama(prompt)
            llm_result = self._parse_llm_response(llm_response, text)

            # Combine results (prefer spaCy when available)
            combined_result = self._combine_results(spacy_result, llm_result)

            return combined_result

        except Exception as e:
            logger.error(f"Error in hybrid booking extraction: {e}")
            # Fallback to spaCy-only result
            return await self.parse_booking_request(text)

    def _combine_results(
        self, spacy_result: BookingInfo, llm_result: BookingInfo
    ) -> BookingInfo:
        """Intelligently combine spaCy and LLM results"""
        combined = BookingInfo(extracted_text=spacy_result.extracted_text)

        # Prefer spaCy for structured data, LLM for missing pieces
        combined.name = spacy_result.name or llm_result.name
        combined.email = spacy_result.email or llm_result.email
        combined.date = spacy_result.date or llm_result.date
        combined.time = spacy_result.time or llm_result.time
        combined.interview_type = (
            spacy_result.interview_type or llm_result.interview_type or "general"
        )

        # Recalculate missing fields and status
        missing_fields = []
        if not combined.name:
            missing_fields.append("name")
        if not combined.email:
            missing_fields.append("email")
        if not combined.date:
            missing_fields.append("date")
        if not combined.time:
            missing_fields.append("time")

        combined.missing_fields = missing_fields

        # Calculate confidence (higher for spaCy contributions)
        spacy_contributions = sum(
            [
                1
                for field in [
                    spacy_result.name,
                    spacy_result.email,
                    spacy_result.date,
                    spacy_result.time,
                ]
                if field is not None
            ]
        )

        if not missing_fields:
            combined.status = BookingStatus.VALID
            combined.confidence = 0.95 if spacy_contributions >= 3 else 0.85
        elif len(missing_fields) <= 2:
            combined.status = BookingStatus.INCOMPLETE
            combined.confidence = 0.75 if spacy_contributions >= 2 else 0.65
        else:
            combined.status = BookingStatus.INCOMPLETE
            combined.confidence = 0.55

        return combined

    def _parse_llm_response(self, llm_response: str, original_text: str) -> BookingInfo:
        """Parse the LLM response to extract booking information"""
        booking_info = BookingInfo(extracted_text=original_text)

        try:
            lines = llm_response.strip().split("\n")
            extracted_data = {}

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if value.lower() not in ["not_found", "missing", ""] and value:
                        extracted_data[key] = value

            # Map extracted data
            booking_info.name = extracted_data.get("name")
            booking_info.email = extracted_data.get("email")
            booking_info.date = extracted_data.get("date")
            booking_info.time = extracted_data.get("time")
            booking_info.interview_type = extracted_data.get("type", "general")

            # Determine status based on intent and completeness
            intent = extracted_data.get("intent", "none").lower()
            if intent in ["booking", "scheduling"]:
                booking_info.status = BookingStatus.DETECTED

                missing_fields = []
                if not booking_info.name:
                    missing_fields.append("name")
                if not booking_info.email:
                    missing_fields.append("email")
                if not booking_info.date:
                    missing_fields.append("date")
                if not booking_info.time:
                    missing_fields.append("time")

                booking_info.missing_fields = missing_fields

                if not missing_fields:
                    booking_info.status = BookingStatus.VALID
                    booking_info.confidence = 0.85
                else:
                    booking_info.status = BookingStatus.INCOMPLETE
                    booking_info.confidence = 0.65
            else:
                booking_info.status = BookingStatus.INCOMPLETE
                booking_info.confidence = 0.3

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            booking_info.status = BookingStatus.INCOMPLETE
            booking_info.confidence = 0.2

        return booking_info

    def validate_booking_info(self, booking_info: BookingInfo) -> Dict[str, Any]:
        """Validate extracted booking information"""
        validation_result = {"is_valid": False, "errors": [], "suggestions": []}

        # Validate email format
        if booking_info.email:
            if not re.match(self.email_pattern, booking_info.email):
                validation_result["errors"].append("Invalid email format")

        # Validate date (not in the past)
        if booking_info.date:
            try:
                booking_date = datetime.strptime(booking_info.date, "%Y-%m-%d").date()
                if booking_date < datetime.now().date():
                    validation_result["errors"].append("Date cannot be in the past")
            except ValueError:
                validation_result["errors"].append(
                    "Invalid date format (use YYYY-MM-DD)"
                )

        # Validate time format
        if booking_info.time:
            try:
                datetime.strptime(booking_info.time, "%H:%M")
            except ValueError:
                validation_result["errors"].append("Invalid time format (use HH:MM)")

        # Validate name
        if booking_info.name:
            if len(booking_info.name.strip()) < 2:
                validation_result["errors"].append("Name too short")
            elif len(booking_info.name) > 100:
                validation_result["errors"].append("Name too long")

        # Generate suggestions for missing fields
        if booking_info.missing_fields:
            field_prompts = {
                "name": "Please provide your full name",
                "email": "Please provide your email address",
                "date": "Please specify the date (e.g., 2024-02-15 or 'tomorrow')",
                "time": "Please specify the time (e.g., 2:30 PM or 14:30)",
            }

            for field in booking_info.missing_fields:
                if field in field_prompts:
                    validation_result["suggestions"].append(field_prompts[field])

        validation_result["is_valid"] = (
            len(validation_result["errors"]) == 0
            and len(booking_info.missing_fields) == 0
        )

        return validation_result
