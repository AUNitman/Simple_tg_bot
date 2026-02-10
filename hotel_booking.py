"""
Модуль для работы с бронированием отелей
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class HotelBookingSystem:
    """Система бронирования отелей с многошаговым диалогом"""
    
    def __init__(self, database_path: str = "hotels_database.json"):
        with open(database_path, 'r', encoding='utf-8') as f:
            self.database = json.load(f)
    
    def get_cities(self) -> List[Dict[str, str]]:
        """Получить список доступных городов"""
        cities = []
        for city_id, city_data in self.database['cities'].items():
            cities.append({
                'id': city_id,
                'name': city_data['name']
            })
        return cities
    
    def get_hotels_by_city(self, city_id: str) -> List[Dict]:
        """Получить отели по городу"""
        if city_id not in self.database['cities']:
            return []
        return self.database['cities'][city_id]['hotels']
    
    def filter_hotels_by_price(self, hotels: List[Dict], price_range: str) -> List[Dict]:
        """Фильтровать отели по ценовому диапазону"""
        if price_range not in self.database['price_ranges']:
            return hotels
        
        price_info = self.database['price_ranges'][price_range]
        filtered = []
        
        for hotel in hotels:
            if price_info['min'] <= hotel['price_per_night'] <= price_info['max']:
                filtered.append(hotel)
        
        return filtered
    
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        """Получить отель по ID"""
        for city_data in self.database['cities'].values():
            for hotel in city_data['hotels']:
                if hotel['id'] == hotel_id:
                    return hotel
        return None
    
    def format_hotel_info(self, hotel: Dict, show_rooms: bool = False) -> str:
        """Форматировать информацию об отеле"""
        stars = "⭐" * hotel['stars']
        rating = f"{'⭐' * int(hotel['rating'])} {hotel['rating']}/5.0"
        
        amenities = ", ".join(hotel['amenities'][:4])
        if len(hotel['amenities']) > 4:
            amenities += f" и ещё {len(hotel['amenities']) - 4}"
        
        cancellation = "✅ Бесплатная отмена" if hotel['free_cancellation'] else "❌ Без возврата"
        
        info = f"""🏨 **{hotel['name']}**
{stars} | {rating}

📍 {hotel['address']}
💰 От {hotel['price_per_night']:,} ₽/ночь

✨ **Удобства:** {amenities}
{cancellation}

📝 {hotel['description']}"""
        
        if show_rooms:
            info += "\n\n**Доступные номера:**"
            for i, room in enumerate(hotel['room_types'], 1):
                info += f"\n{i}. {room['type']} - {room['price']:,} ₽ (до {room['capacity']} чел.)"
        
        return info
    
    def format_hotels_list(self, hotels: List[Dict]) -> str:
        """Форматировать список отелей"""
        if not hotels:
            return "😔 К сожалению, отели не найдены. Попробуйте изменить параметры поиска."
        
        result = f"🏨 **Найдено отелей: {len(hotels)}**\n\n"
        
        for i, hotel in enumerate(hotels, 1):
            stars = "⭐" * hotel['stars']
            result += f"{i}. **{hotel['name']}** {stars}\n"
            result += f"   💰 От {hotel['price_per_night']:,} ₽/ночь | ⭐ {hotel['rating']}/5.0\n"
            result += f"   📍 {hotel['address']}\n\n"
        
        return result
    
    def calculate_total_price(self, hotel_id: str, room_type: str, nights: int, guests: int = 2) -> Optional[Dict]:
        """Рассчитать общую стоимость"""
        hotel = self.get_hotel_by_id(hotel_id)
        if not hotel:
            return None
        
        # Найти тип номера
        room = None
        for r in hotel['room_types']:
            if r['type'] == room_type:
                room = r
                break
        
        if not room:
            return None
        
        if guests > room['capacity']:
            return None
        
        total = room['price'] * nights
        
        return {
            'hotel_name': hotel['name'],
            'room_type': room_type,
            'price_per_night': room['price'],
            'nights': nights,
            'guests': guests,
            'total': total,
            'free_cancellation': hotel['free_cancellation']
        }
    
    def format_booking_summary(self, booking_data: Dict) -> str:
        """Форматировать итоговую информацию о бронировании"""
        summary = f"""📋 **Итоговая информация о бронировании:**

🏨 **Отель:** {booking_data.get('hotel_name', 'Не указан')}
🏠 **Тип номера:** {booking_data.get('room_type', 'Не указан')}
👥 **Количество гостей:** {booking_data.get('guests', 'Не указано')}

📅 **Даты:**
   • Заезд: {booking_data.get('check_in', 'Не указано')}
   • Выезд: {booking_data.get('check_out', 'Не указано')}
   • Ночей: {booking_data.get('nights', 'Не указано')}

💰 **Стоимость:**
   • За ночь: {booking_data.get('price_per_night', 0):,} ₽
   • Всего: {booking_data.get('total', 0):,} ₽

👤 **Контактные данные:**
   • Имя: {booking_data.get('guest_name', 'Не указано')}
   • Телефон: {booking_data.get('phone', 'Не указано')}
   • Email: {booking_data.get('email', 'Не указано')}
"""
        
        if booking_data.get('free_cancellation'):
            summary += "\n✅ **Бесплатная отмена** до даты заезда"
        else:
            summary += "\n❌ **Невозвратный тариф**"
        
        return summary


class BookingState:
    """Состояния процесса бронирования"""
    IDLE = "idle"
    SELECTING_CITY = "selecting_city"
    SELECTING_PRICE_RANGE = "selecting_price_range"
    VIEWING_HOTELS = "viewing_hotels"
    SELECTING_HOTEL = "selecting_hotel"
    SELECTING_ROOM = "selecting_room"
    ENTERING_DATES = "entering_dates"
    ENTERING_GUESTS = "entering_guests"
    ENTERING_CONTACT_NAME = "entering_contact_name"
    ENTERING_CONTACT_PHONE = "entering_contact_phone"
    ENTERING_CONTACT_EMAIL = "entering_contact_email"
    CONFIRMING_BOOKING = "confirming_booking"
    COMPLETED = "completed"


def init_booking_data() -> Dict:
    """Инициализировать данные бронирования"""
    return {
        'state': BookingState.IDLE,
        'city_id': None,
        'city_name': None,
        'price_range': None,
        'hotels': [],
        'selected_hotel_id': None,
        'selected_hotel_name': None,
        'selected_room_type': None,
        'check_in': None,
        'check_out': None,
        'nights': None,
        'guests': 2,
        'guest_name': None,
        'phone': None,
        'email': None,
        'price_per_night': None,
        'total': None,
        'free_cancellation': None
    }
