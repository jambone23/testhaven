def agent(input_text, memory):
    """
    Multi-turn agent that handles:
    - Greetings
    - Flight search (with preferred airport)
    - Booking confirmation
    Tracks memory and tool usage for each step.
    """
    if memory is None:
        memory = {}

    input_lower = input_text.lower()
    tools_used = []
    output = ""

    # Step 1: Greeting
    if any(greet in input_lower for greet in ["hello", "hi", "hey"]):
        output = "Hello! How can I help you today?"
        memory["greeted"] = True
        return {
            "output": output,
            "tools_used": [],
            "memory": memory
        }

    # Step 3: Booking confirmation
    if any(phrase in input_lower for phrase in ["book that", "confirm", "go ahead", "yes please", "great, book"]):
        output = "Booking confirmed. You're all set!"
        memory["booking"] = { "status": "confirmed" }
        tools_used = ["BookingAPI"]
        return {
            "output": output,
            "tools_used": tools_used,
            "memory": memory
        }

    # Step 2: Flight search
    destination = None
    idx = input_lower.find(" to ")
    if idx != -1:
        dest_part = input_lower[idx + 4:]
        for marker in [" next", " on ", " in ", " at ", " this ", " tomorrow", " today", "."]:
            marker_idx = dest_part.find(marker)
            if marker_idx != -1:
                dest_part = dest_part[:marker_idx]
                break
        destination = dest_part.strip().title()

    if not destination:
        destination = "Unknown Destination"

    departure = memory.get("preferred_airport", "Unknown Airport")
    output = f"Booking flight from {departure} to {destination}."
    tools_used = ["Skyscanner"]

    memory["last_booking"] = {
        "destination": destination,
        "departure": departure
    }

    return {
        "output": output,
        "tools_used": tools_used,
        "memory": memory
    }

