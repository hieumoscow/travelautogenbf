from typing import Dict, Callable, Tuple
import logging

LOG = logging.getLogger(__name__)


DEFAULT_ACTIONS = [
    {
        "title": "What activities can I do in Singapore?",
        "value": "What activities can I do in Singapore?"
    },
    {
        "title": "Tell me more about Singapore's culture",
        "value": "Tell me more about Singapore's culture"
    },
    {
        "title": "What's the best time to visit Singapore?",
        "value": "What's the best time to visit Singapore?"
    },
    {
        "title": "Recommend some local food in Singapore",
        "value": "Recommend some local food in Singapore"
    }
]

class MessageFormatter:
    """Handles formatting of different message types based on backend data structures"""
    
    def __init__(self):
        self.formatters: Dict[str, Callable] = {
            'activities_booking': self.format_activities,
            'destination_info': self.format_destination_info,
            'flight_booking': self.format_flight_booking,
            'hotel_booking': self.format_hotel_booking,
            'car_rental': self.format_car_rental,
            'default_agent': self.format_default,
            'group_chat_manager': self.format_group_chat
        }

    def format_activities(self, data: dict) -> str:
        activities = data.get('data', {}).get('activities', [])
        destination = data.get('data', {}).get('destination_city', '')
        
        formatted_text = [f"🎯 Exploring {destination}"]
        
        # Group activities by type
        activity_types = {}
        for activity in activities:
            activity_type = activity.get('activity_type', 'Other')
            if activity_type not in activity_types:
                activity_types[activity_type] = []
            activity_types[activity_type].append(activity)
        
        for type_name, type_activities in activity_types.items():
            formatted_text.append(f"\n📍 {type_name}")
            for activity in type_activities:
                name = activity.get('activity_name', '')
                desc = activity.get('activity_description', '')
                formatted_text.append(f"• {name}")
                formatted_text.append(f"  {desc}\n")
                
        return "\n".join(formatted_text)

    def format_destination_info(self, data: dict) -> str:
        info = data.get('data', {})
        return "\n".join([
            f"🌏 {info.get('city', '')}, {info.get('country', '')}\n",
            "📝 Description:",
            f"{info.get('description', '')}\n",
            "⏰ Best Time to Visit:",
            f"{info.get('best_time_to_visit', '')}\n",
            "🌡️ Average Temperature:",
            f"{info.get('average_temperature', '')}\n",
            f"💰 Currency: {info.get('currency', '')}",
            f"🗣️ Language: {info.get('language', '')}\n",
            "✈️ Similar Destinations:",
            ", ".join(info.get('similar_destinations', []))
        ])

    def format_flight_booking(self, data: dict) -> str:
        booking = data.get('data', {})
        return "\n".join([
            "✈️ Flight Booking Details",
            f"From: {booking.get('departure_city', '')}",
            f"To: {booking.get('destination_city', '')}",
            f"Departure: {booking.get('departure_date', '')}",
            f"Return: {booking.get('return_date', '')}",
            f"Airline: {booking.get('airline', '')}",
            f"Flight: {booking.get('flight_number', '')}",
            f"Passengers: {booking.get('number_of_passengers', '')}",
            f"Total Price: ${booking.get('total_price', ''):.2f}",
            f"Booking Reference: {booking.get('booking_reference', '')}"
        ])

    def format_hotel_booking(self, data: dict) -> str:
        booking = data.get('data', {})
        return "\n".join([
            "🏨 Hotel Booking Details",
            f"City: {booking.get('city', '')}",
            f"Hotel: {booking.get('hotel_name', '')}",
            f"Check-in: {booking.get('check_in_date', '')}",
            f"Check-out: {booking.get('check_out_date', '')}",
            f"Room Type: {booking.get('room_type', '')}",
            f"Total Price: ${booking.get('total_price', ''):.2f}",
            f"Booking Reference: {booking.get('booking_reference', '')}"
        ])

    def format_car_rental(self, data: dict) -> str:
        rental = data.get('data', {})
        return "\n".join([
            "🚗 Car Rental Details",
            f"City: {rental.get('rental_city', '')}",
            f"Pickup: {rental.get('rental_start_date', '')}",
            f"Return: {rental.get('rental_end_date', '')}",
            f"Vehicle Type: {rental.get('car_type', '')}",
            f"Rental Company: {rental.get('company', '')}",
            f"Total Price: ${rental.get('total_price', ''):.2f}",
            f"Booking Reference: {rental.get('booking_reference', '')}"
        ])

    def format_group_chat(self, data: dict) -> str:
        chat = data.get('data', {})
        return f"{chat.get('sender', 'Unknown')}: {chat.get('content', '')}"

    def format_default(self, data: dict) -> str:
        if 'message' in data:
            return data['message']
        return str(data.get('data', ''))
    
    def format_message(self, message_data: dict) -> Tuple[str, list]:
            """
            Format message and return both formatted text and suggested actions
            Returns tuple of (formatted_text, suggested_actions)
            """
            try:
                agent_type = message_data.get('agent_type', 'default_agent')
                formatter = self.formatters.get(agent_type, self.format_default)
                formatted_text = formatter(message_data)
                
                # Get suggested actions from message or use defaults
                suggested_actions = message_data.get('suggested_actions', DEFAULT_ACTIONS)
                
                return formatted_text, suggested_actions
                
            except Exception as e:
                LOG.error(f"Error formatting message: {str(e)}")
                return str(message_data), DEFAULT_ACTIONS
