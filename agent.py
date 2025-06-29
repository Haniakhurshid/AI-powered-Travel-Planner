import streamlit as st
import json
import os
from datetime import datetime
from amadeus import Client, ResponseError
from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv
load_dotenv()
print("✅ GOOGLE_API_KEY from .env in Streamlit =", os.getenv("GOOGLE_API_KEY"))


# ================================
# 🔑 Amadeus API credentials
# ================================
AMADEUS_CLIENT_ID = ""
AMADEUS_CLIENT_SECRET = ""

amadeus = Client(
    client_id=AMADEUS_CLIENT_ID,
    client_secret=AMADEUS_CLIENT_SECRET
)

# ================================
# 🗺️ Streamlit UI setup
# ================================
st.set_page_config(page_title="🌍 AI Travel Planner", layout="wide")
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #ff5733;
        }
        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #555;
        }
        .stSlider > div {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True,
)

st.markdown('<h1 class="title">✈️ AI-Powered Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Plan your dream trip with AI! Get personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)

# ================================
# 🛫 User Inputs
# ================================
st.markdown("### 🌍 Where are you headed?")
source = st.text_input("🛫 Departure City (IATA Code):", "BOM")
destination = st.text_input("🛬 Destination (IATA Code):", "DEL")

st.markdown("### 📅 Plan Your Adventure")
num_days = st.slider("🕒 Trip Duration (days):", 1, 14, 5)
travel_theme = st.selectbox("🎭 Select Your Travel Theme:",
                            ["💑 Couple Getaway", "👨‍👩‍👧‍👦 Family Vacation", "🏔️ Adventure Trip", "🧳 Solo Exploration"])

st.markdown("---")
st.markdown(f"""
    <div style="
        text-align: center; 
        padding: 15px; 
        background-color: #ffecd1; 
        border-radius: 10px; 
        margin-top: 20px;
    ">
        <h3>🌟 Your {travel_theme} to {destination} is about to begin! 🌟</h3>
        <p>Let's find the best flights, stays, and experiences for your unforgettable journey.</p>
    </div>
    """, unsafe_allow_html=True,
)

activity_preferences = st.text_area("🌍 What activities do you enjoy?",
                                    "Relaxing on the beach, exploring historical sites")
departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

# ================================
# ⚙️ Sidebar preferences
# ================================
st.sidebar.title("🌎 Travel Assistant")
st.sidebar.subheader("Personalize Your Trip")

budget = st.sidebar.radio("💰 Budget Preference:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("✈️ Flight Class:", ["ECONOMY", "BUSINESS", "FIRST"])
hotel_rating = st.sidebar.selectbox("🏨 Preferred Hotel Rating:", ["Any", "3⭐", "4⭐", "5⭐"])

st.sidebar.subheader("🎒 Packing Checklist")
packing_list = {
    "👕 Clothes": True,
    "🩴 Comfortable Footwear": True,
    "🕶️ Sunglasses & Sunscreen": False,
    "📖 Travel Guidebook": False,
    "💊 Medications & First-Aid": True
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

st.sidebar.subheader("🛂 Travel Essentials")
visa_required = st.sidebar.checkbox("🛃 Check Visa Requirements")
travel_insurance = st.sidebar.checkbox("🛡️ Get Travel Insurance")
currency_converter = st.sidebar.checkbox("💱 Currency Exchange Rates")

# ================================
# ✈️ Amadeus flight functions
# ================================
def fetch_flights_amadeus(source, destination, departure_date, return_date, num_adults=1, travel_class="ECONOMY"):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=source,
            destinationLocationCode=destination,
            departureDate=str(departure_date),
            returnDate=str(return_date),
            adults=num_adults,
            travelClass=travel_class,
            currencyCode="INR",
            max=10
        )
        return response.data
    except ResponseError as error:
        print(error)
        return []

def extract_cheapest_flights_amadeus(flight_data):
    sorted_flights = sorted(
        flight_data,
        key=lambda x: float(x["price"]["total"])
    )[:3]

    formatted_flights = []
    for offer in sorted_flights:
        itinerary = offer["itineraries"][0]
        first_segment = itinerary["segments"][0]
        last_segment = itinerary["segments"][-1]

        departure_time = first_segment["departure"]["at"]
        arrival_time = last_segment["arrival"]["at"]
        carrier_code = first_segment["carrierCode"]
        duration = itinerary["duration"].replace("PT", "").lower()

        price = offer["price"]["total"] + " " + offer["price"]["currency"]

        formatted_flights.append({
            "carrier_code": carrier_code,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration": duration,
            "price": price,
            "offer": offer
        })

    return formatted_flights
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not set. Please add it to your .env file.")

# ================================
# 🤖 Agents
# ================================
researcher = Agent(
    name="Researcher",
    instructions=[
        "Identify the travel destination specified by the user.",
        "Gather detailed information on the destination, including climate, culture, and safety tips.",
        "Find popular attractions, landmarks, and must-visit places.",
        "Search for activities that match the user’s interests and travel style.",
        "Provide well-structured summaries with key insights and recommendations."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

planner = Agent(
    name="Planner",
    instructions=[
        "Gather details about the user's travel preferences and budget.",
        "Create a detailed itinerary with scheduled activities and estimated costs.",
        "Ensure the itinerary includes transportation options and travel time estimates.",
        "Present the itinerary in a structured format."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

hotel_restaurant_finder = Agent(
    name="Hotel & Restaurant Finder",
    instructions=[
        "Identify key locations in the user's travel itinerary.",
        "Search for highly rated hotels near those locations.",
        "Search for top-rated restaurants based on cuisine preferences and proximity.",
        "Provide direct booking links or reservation options where possible."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

# ================================
# 🚀 Generate Travel Plan
# ================================
if st.button("🚀 Generate Travel Plan"):
    with st.spinner("✈️ Fetching best flight options..."):
        amadeus_data = fetch_flights_amadeus(source, destination, departure_date, return_date,
                                             travel_class=flight_class.upper())
        cheapest_flights = extract_cheapest_flights_amadeus(amadeus_data)

    with st.spinner("🔍 Researching best attractions & activities..."):
        research_prompt = (
            f"Research the best attractions and activities in {destination} for a {num_days}-day {travel_theme.lower()} trip. "
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. "
            f"Hotel Rating: {hotel_rating}. Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}."
        )
        research_results = researcher.run(research_prompt, stream=False)

    with st.spinner("🏨 Searching for hotels & restaurants..."):
        hotel_restaurant_prompt = (
            f"Find the best hotels and restaurants near popular attractions in {destination} for a {travel_theme.lower()} trip. "
            f"Budget: {budget}. Hotel Rating: {hotel_rating}. Preferred activities: {activity_preferences}."
        )
        hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)

    with st.spinner("🗺️ Creating your personalized itinerary..."):
        planning_prompt = (
            f"Based on the following data, create a {num_days}-day itinerary for a {travel_theme.lower()} trip to {destination}. "
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. Hotel Rating: {hotel_rating}. "
            f"Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}. Research: {research_results.content}. "
            f"Flights: {json.dumps(cheapest_flights)}. Hotels & Restaurants: {hotel_restaurant_results.content}."
        )
        itinerary = planner.run(planning_prompt, stream=False)

    st.subheader("✈️ Cheapest Flight Options")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                st.markdown(f"""
                    <div style="
                        border: 2px solid #ddd; 
                        border-radius: 10px; 
                        padding: 15px; 
                        text-align: center;
                        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
                        background-color: #f9f9f9;
                        margin-bottom: 20px;
                    ">
                        <h3 style="margin: 10px 0;">✈️ {flight["carrier_code"]}</h3>
                        <p><strong>Departure:</strong> {flight["departure_time"]}</p>
                        <p><strong>Arrival:</strong> {flight["arrival_time"]}</p>
                        <p><strong>Duration:</strong> {flight["duration"]}</p>
                        <h2 style="color: #008000;">💰 {flight["price"]}</h2>
                        <p style="font-size: 14px; color: #888;">Book via partner site</p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No flight data available.")

    st.subheader("🏨 Hotels & Restaurants")
    st.write(hotel_restaurant_results.content)

    st.subheader("🗺️ Your Personalized Itinerary")
    st.write(itinerary.content)

    st.success("✅ Travel plan generated successfully!")
