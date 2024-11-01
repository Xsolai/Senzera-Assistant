def determine_price_category(location, has_card_response):
    # Normalize user response to lower case for flexible matching
    response = has_card_response.lower().strip()
    
    if location.lower() == "munich":
        if response in ["yes", "i do", "i have", "i have a card"]:
            return "price_munich_with_card"
        else:
            return "price_munich_without_card"
    else:  # For all other locations treated as 'Mittel'
        if response in ["yes", "i do", "i have", "i have a card"]:
            return "price_mittel_with_card"
        else:
            return "price_mittel_without_card"