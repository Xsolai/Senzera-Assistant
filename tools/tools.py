import sqlite3
import re
DATABASE_PATH = 'instance/database.db'

def create_profile(name, user_id=None, gdpr_consent=False, gender=None):
    """
    Creates a profile with the provided name, user_id, and gdpr_consent if they don't already exist.
    
    Parameters:
    - name: str - The name associated with the profile
    - user_id: str - The unique user ID (optional, autogenerated if not provided)
    - gdpr_consent: bool - User's GDPR consent (True or False)
    
    Returns:
    - A dictionary indicating success or failure
    """
    if not name:
        return {"success": False, "error": "Name is required."}, 400

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO profiles (user_id, name, gdpr_consent, gender) VALUES (?, ?, ?, ?)",
                (user_id, name, gdpr_consent, gender)
            )
            conn.commit()
            return {"success": True, "message": "Profile created successfully.", "Name": name, "GDPR Consent": gdpr_consent, "gender":gender}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Profile with this name or user_id already exists."}, 409
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

def replace_double_with_single_asterisks(text):
    return re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)

def remove_sources(text):
     # Use regex to match the pattern 【number:number†filename.extension】
    clean_text = re.sub(r"【\d+:\d+†[^\s]+】", "", text)
    return clean_text

def check_profile(user_id):
    """
    Checks if a profile exists for the given user_id in the profiles database
    and returns a formatted response indicating the next action.

    Parameters:
    - user_id (str): The unique identifier of the user to look up.

    Returns:
    - dict: A well-formatted response with information about the user and the next steps.
      If a profile exists:
        - "message" (str): A greeting or prompt based on GDPR consent status.
        - "assist" (bool): True if GDPR consent is given, allowing immediate assistance.
        - "name" (str): The customer's name.
      If no profile is found:
        - Returns a message prompting GDPR consent.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, gdpr_consent, gender FROM profiles WHERE user_id = ?", (user_id,))
        profile = cursor.fetchone()
    
    if profile:
        name, _, gender = profile
        return {
            "message": f"Welcome back, {name}! How can I assist you today?",
            "gender": gender,
            "assist": True,
            "name": name
        }    
    # If no profile is found
    return {
        "message": "There is no profile for this user.",
        "assist": False
    }
    

# def update_profile(gdpr_consent, user_id):
#     """
#     Updates the GDPR consent status in the profiles database for a specific user.

#     Parameters:
#     - user_id (str): The unique identifier of the user.
#     - gdpr_consent (bool): The new GDPR consent status to be set.

#     Returns:
#     - dict: A response indicating success or failure of the update operation.
#       - If the profile is updated successfully:
#         - "success" (bool): True
#         - "message" (str): Confirmation message
#       - If no profile with the specified user_id exists:
#         - "success" (bool): False
#         - "error" (str): Error message explaining that the profile does not exist.
#     """
#     try:
#         with sqlite3.connect(DATABASE_PATH) as conn:
#             cursor = conn.cursor()
#             # Update GDPR consent status
#             cursor.execute(
#                 "UPDATE profiles SET gdpr_consent = ? WHERE user_id = ?",
#                 (gdpr_consent, user_id)
#             )
#             conn.commit()

#             # Check if any rows were affected to determine if the user_id exists
#             if cursor.rowcount == 0:
#                 return {
#                     "success": False,
#                     "error": "Profile with this user_id does not exist."
#                 }
            
#             return {
#                 "success": True,
#                 "message": "GDPR consent status updated successfully. Now Assist with queryies."
#             }
    
#     except Exception as e:
#         return {
#             "success": False,
#             "error": f"An error occurred: {str(e)}"
#         }
