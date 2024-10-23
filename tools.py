tools = [
    {
        "type": "function",
        "function": {
            "name": "get_sites",
            "description": "Retrieve site information by querying the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name to get site information within the city."
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Retrieve product information for a specific customer and site by querying the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city for which product information is to be retrieved."
                    },
                    "service_name": {
                        "type": "string",
                        "description": "The service name for which product information is to be retrieved."
                    }
                },
                "required": ["city", "service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employees",
            "description": "Retrieve employees who are available to perform a specific service at a studio on a specific date and time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The location of the studio where the service is requested."
                    },
                    "service_name": {
                        "type": "string",
                        "description": "The name of the service to be performed."
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "The date of the appointment in 'YYYY-MM-DD' format."
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "The time of the appointment in 'HH:MM:SS' format."
                    }
                },
                "required": ["city", "service_name", "appointment_date", "appointment_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_suggestions",
            "description": "Retrieve a list of available appointment dates and times for a specific service at a specific studio location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The location of the studio where the service is requested."
                    },
                    "service_name": {
                        "type": "string",
                        "description": "The name of the service to be performed."
                    }
                },
                "required": ["city", "service_name"]
            }
        }
    },
   {
        "type": "function",
        "function": {
            "name": "confirm_appointment",
            "description": "Create a confirmed appointment by gathering necessary information and linking it to service availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "The full name of the customer."
                    },
                    "customer_contact": {
                        "type": "string",
                        "description": "The contact information of the customer (phone or email)."
                    },
                    "city": {
                        "type": "string",
                        "description": "The location of the studio where the service is booked."
                    },
                    "service_name": {
                        "type": "string",
                        "description": "The name of the service being booked."
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "The date of the appointment in 'YYYY-MM-DD' format."
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "The time of the appointment in 'HH:MM:SS' format."
                    },
                    "service_price":{
                        "type": "integer",
                        "description": "the price of of service price category"
                    }
                },
                "required": [
                    "customer_name", 
                    "customer_contact", 
                    "city", 
                    "service_name", 
                    "appointment_date", 
                    "appointment_time",
                    "service_price"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel a confirmed appointment by removing it from the database using the appointment ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The ID of the appointment to be canceled."
                    }
                },
                "required": ["appointment_id"]
            }
        }
    }

]