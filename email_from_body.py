import re

email_body = "Please contact us at support@example.com or admin@example.co.uk nives..h.sscyno.uk.co.@in.an for more info."

email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
matches = re.findall(email_pattern, email_body)

print(matches)
