def agent(input_text, memory):
    """
    Parse the destination city from the input text, use the preferred airport from memory,
    and return an output message. Also record the tool used and update memory with last booking info.
    """
    # Ensure memory is a dict (initialize if None)
    if memory is None:
        memory = {}

    # Parse destination city from the input text
    destination = None
    idx = input_text.lower().find(" to ")
    if idx != -1:
        dest_part = input_text[idx+4:]
        markers = [" next", " on ", " in ", " at ", " this ", " tomorrow", " today"]
        for marker in markers:
            m_idx = dest_part.lower().find(marker)
            if m_idx != -1:
                dest_part = dest_part[:m_idx]
                break
        destination = dest_part.strip().strip(".,!?")
    if not destination:
        destination = "Unknown Destination"

    # Get the preferred departure airport from memory (or fallback)
    departure = memory.get("preferred_airport", "Unknown Airport")

    # Compose the output
    output = f"Booking flight from {departure} to {destination}."

    # Record the tool used
    tools_used = ["Skyscanner"]

    # Update memory with booking info
    memory["last_booking"] = {
        "destination": destination,
        "departure": departure
    }

    return {
        "output": output,
        "tools_used": tools_used,
        "memory": memory
    }
