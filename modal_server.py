# Import necessary libraries
import os
import requests

# Define the Modal Labs endpoint LLM
modal_labs_endpoint = "https://api.modal-labs.com/llm"

# Define the Slack endpoint
slack_endpoint = "https://slack.com/api/chat.postMessage"

# Define the function to send stories to Slack
def send_stories_to_slack(stories):
    # Set the Slack API token
    slack_token = os.environ["SLACK_TOKEN"]

    # Set the Slack channel
    slack_channel = os.environ["SLACK_CHANNEL"]

    # Send the stories to Slack
    for story in stories:
        requests.post(
            slack_endpoint,
            headers={"Authorization": f"Bearer {slack_token}"},
            json={"channel": slack_channel, "text": story},
        )

# Define the function to get stories from the Modal Labs endpoint LLM
def get_stories_from_modal_labs():
    # Set the Modal Labs API token
    modal_labs_token = os.environ["MODAL_LABS_TOKEN"]

    # Get the stories from the Modal Labs endpoint LLM
    response = requests.get(
        modal_labs_endpoint,
        headers={"Authorization": f"Bearer {modal_labs_token}"},
    )

    # Return the stories
    return response.json()["stories"]

# Define the main function
def main():
    # Get the stories from the Modal Labs endpoint LLM
    stories = get_stories_from_modal_labs()

    # Send the stories to Slack
    send_stories_to_slack(stories)

# Run the main function
if __name__ == "__main__":
    main()
