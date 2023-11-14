import argparse
import json
from cpapi import APIClient, APIClientArgs
## take file from getldapgrpsfromaccesroles as input and set ldap group for every access role
def update_access_roles(server, username, password, input_json, source_domain):
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        login_res = client.login(username, password)
        if login_res.success is False:
            print("Login failed:", login_res.error_message)
            exit(1)
        # Read input JSON file
        with open(input_json, "r") as json_file:
            data = json.load(json_file)
        for entry in data:
            access_role_name = entry.get("Access Role", "")
            users_info = entry.get("Users", [])
            # Prepare the payload for the API call
            payload = {
                "name": access_role_name,
                "users": [{
                    "source": source_domain,
                    "selection": user.get("cn", ""),
                    "base-dn": user.get("dn", "")
                } for user in users_info]
            }
            update_access_role_res = client.api_call("set-access-role", payload)
            if update_access_role_res.success:
                print(f"Access role '{access_role_name}' updated successfully.")
            else:
                error_message = update_access_role_res.error_message
                print(f"Failed to update access role '{access_role_name}':", error_message)
                raise Exception(f"Failed to update access role '{access_role_name}': {error_message}")
        # Publish the changes
        publish_res = client.api_call("publish", {})
        if publish_res.success:
            print("Changes published successfully.")
        else:
            print("Failed to publish changes:", publish_res.error_message)
        client.api_call("logout")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update access roles based on input JSON file.")
    parser.add_argument("server", help="Server address")
    parser.add_argument("username", help="Username")
    parser.add_argument("password", help="Password")
    parser.add_argument("input_json", help="Input JSON file containing access role information")
    parser.add_argument("source_domain", help="Source domain for users")
    args = parser.parse_args()

    try:
        update_access_roles(args.server, args.username, args.password, args.input_json, args.source_domain)
    except Exception as e:
        print(f"Error: {e}")
