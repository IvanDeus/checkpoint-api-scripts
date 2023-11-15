import sys
import json
from cpapi import APIClient, APIClientArgs
# take json file from getnetworksfromaccessroles.py as input and add access role
def create_access_role(server, username, password, access_role_data):
    # Setup client
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        # Login
        login_res = client.login(username, password)
        if login_res.success is False:
            print("Login failed:", login_res.error_message)
            exit(1)
        for role_data in access_role_data:
            # Prepare the payload for the API call
            role_name = role_data["Access Role"]
            #extract name values
            networks = [network["name"] for network in role_data["Networks"]]
            payload = {
                "name": role_name,
                "machines": "any",
                "networks": networks,
                "remote-access-clients": "any",
                "users": "any"
            }
            #print (payload)
            # Create the new access role
            add_access_role_res = client.api_call("add-access-role", payload)
            if add_access_role_res.success:
                print(f"New access role '{role_name}' created successfully.")
            else:
                print(f"Failed to create new access role '{role_name}':", add_access_role_res.error_message)
        # Publish the changes
        publish_res = client.api_call("publish", {})
        if publish_res.success:
            print("Changes published successfully.")
        else:
            print("Failed to publish changes:", publish_res.error_message)
        # Logout
        client.api_call("logout")

if __name__ == "__main__":
    # Check if the correct number of command-line arguments is provided
    if len(sys.argv) != 5:
        print("Usage: python script.py <server> <username> <password> <json_file>")
        exit(1)
