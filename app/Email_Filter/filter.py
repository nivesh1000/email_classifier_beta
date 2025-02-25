def classify_emails(emails, groups_data):
    """
    Classify emails into groups based on keywords in subject and body.

    Args:
        emails (List[Dict]): List of emails with email details.
        groups_data (Dict): JSON containing group information and keywords.

    Returns:
        List[Dict]: List of emails with assigned groups as group_id and keyword_id.
    """
    groups = groups_data["data"]["groups"]

    for email in emails:
        email["group"] = {"group_id": None, "keyword_id": None}  # Default is empty
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()

        # Check keywords in subject first
        for group in groups:
            for keyword_data in group.get("keywords", []):
                keyword = keyword_data["keyword"].lower()
                if keyword in subject:
                    email["group"] = {"group_id": group["id"], "keyword_id": keyword_data["id"]}
                    break
            if email["group"]["group_id"] is not None:  # If group is assigned, stop checking
                break

        # If no group is assigned, check keywords in body
        if email["group"]["group_id"] is None:
            for group in groups:
                for keyword_data in group.get("keywords", []):
                    keyword = keyword_data["keyword"].lower()
                    if keyword in body:
                        email["group"] = {"group_id": group["id"], "keyword_id": keyword_data["id"]}
                        break
                if email["group"]["group_id"] is not None:  # If group is assigned, stop checking
                    break

    return emails
