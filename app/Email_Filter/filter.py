def classify_emails(emails, groups_data):
    """
    Classify emails into groups based on keywords in subject and body.

    Args:
        emails (List[Dict]): List of emails with email details.
        groups_data (Dict): JSON containing group information and keywords.

    Returns:
        List[Dict]: List of emails with assigned groups.
    """
    groups = groups_data["data"]["groups"]

    for email in emails:
        email["group"] = ""  # Default group is empty
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()

        # Check keywords in subject first
        for group in groups:
            for keyword_data in group.get("keywords", []):
                keyword = keyword_data["keyword"].lower()
                if keyword in subject:
                    email["group"] = group["name"]
                    break
            if email["group"]:  # If group is already assigned, stop checking
                break

        # If no group is assigned, check keywords in body
        if not email["group"]:
            for group in groups:
                for keyword_data in group.get("keywords", []):
                    keyword = keyword_data["keyword"].lower()
                    if keyword in body:
                        email["group"] = group["name"]
                        break
                if email["group"]:  # If group is already assigned, stop checking
                    break

    return emails
