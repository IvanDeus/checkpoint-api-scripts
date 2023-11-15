import argparse
import json
from cpapi import APIClient, APIClientArgs
# get all networks from access roles to a json file 
def get_access_roles(server, username, password, save_path=None):
    # Setup client
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        # Login
        login_res = client.login(username, password)
        if login_res.success is False:
            print("Login failed:", login_res.error_message)
            exit(1)
        # Initialize parameters for pagination
        offset = 0
        limit = 200
        all_access_roles = []

        while True:
            # Get access roles with offset and limit
            show_access_roles_res = client.api_call(
                "show-access-roles",
                {"details-level": "full", "limit": limit, "offset": offset}
            )
            if not show_access_roles_res.success:
                print("Failed to retrieve access roles:", show_access_roles_res.error_message)
                exit(1)
            access_roles = show_access_roles_res.data.get("objects", [])
            # Break if no more access roles
            if not access_roles:
                break
            # Add access roles to the list
            all_access_roles.extend(access_roles)
            offset += limit
        # Prepare data to save or print
        output_data = []
        # Loop through each access role to extract user and network information
        for role in all_access_roles:
            role_name = role.get("name", "")
          # Check if networks is set to "any"
            networks = role.get("networks", [])
            if isinstance(networks, str) and networks.lower() == 'any':
                networks_info = [{"name": "any"}]
            else:
                networks_info = [
                    {"name": nets.get("name", "")}
                    for nets in role.get("networks", [])
                ]
            output_data.append({"Access Role": role_name, "Networks": networks_info})
        client.api_call("logout")
        # Save or print the output
        if save_path:
            with open(save_path, "w") as json_file:
                json.dump(output_data, json_file, indent=2)
            print(f"Data saved to {save_path}")
        else:
            print(json.dumps(output_data, indent=2))
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve and print access roles information.")
    parser.add_argument("server", help="Server address")
    parser.add_argument("username", help="Username")
    parser.add_argument("password", help="Password")
    parser.add_argument("--save", help="JSON file path to save the output")
    args = parser.parse_args()

    get_access_roles(args.server, args.username, args.password, args.save)
