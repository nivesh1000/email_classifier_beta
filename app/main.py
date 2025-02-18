from Authenticator.authenticator import UserAuthenticator
from Token_Refresher.token_refresher import TokenManager

# Usage Example:

if __name__ == "__main__":
    # Initialize the TokenManager
    token_manager = TokenManager()

    # Refresh and update tokens
    try:
        token_manager.refresh_tokens()
    except Exception as e:
        print(f"Error during token refresh: {e}")
