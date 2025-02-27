def classify_emails(emails, groups_data):
    """
    Classify emails into groups based on keywords in subject and body.
    If no group is assigned, assign a default group with no keywords.

    Args:
        emails (List[Dict]): List of emails with email details.
        groups_data (Dict): JSON containing group information and keywords.

    Returns:
        List[Dict]: List of emails with assigned groups as a list of dictionaries.
    """
    groups = groups_data["data"]["groups"]

    # Find the default group (group with no keywords)
    default_group = next((group for group in groups if not group.get("keywords")), None)

    for email in emails:
        email["group"] = []  # Initialize as an empty list
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()

        # Check keywords in subject
        for group in groups:
            for keyword_data in group.get("keywords", []):
                keyword = keyword_data["keyword"].lower()
                if keyword in subject:
                    email["group"].append({"group_id": group["id"], "keyword_id": keyword_data["id"]})
                    break  # Continue checking for more matches
        
        # Check keywords in body if no match in subject
        for group in groups:
            for keyword_data in group.get("keywords", []):
                keyword = keyword_data["keyword"].lower()
                if keyword in body:
                    email["group"].append({"group_id": group["id"], "keyword_id": keyword_data["id"]})
                    break  # Continue checking for more matches

        # If no group was assigned, use the default group
        if not email["group"] and default_group:
            email["group"].append({"group_id": default_group["id"], "keyword_id": ""})

    return emails
