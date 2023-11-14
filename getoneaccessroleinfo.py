import argparse
from cpapi import APIClient, APIClientArgs
import json

def get_access_role_info(server, username, password, access_role_name):
    # Setup client
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        # Login
        login_res = client.login(username, password)
        if login_res.success is False:
            print("Login failed:", login_res.error_message)
            exit(1)
        # Retrieve information about the specific access role
        show_access_role_res = client.api_call("show-access-role", {"name": access_role_name, "details-level": "full"})

        if show_access_role_res.success:
            # Assuming the role information is in the 'access-role' field
            access_role_info = show_access_role_res.data
            print(json.dumps(access_role_info, indent=2))
        else:
            print(f"Failed to retrieve access role '{access_role_name}':", show_access_role_res.error_message)
        # Logout
        client.api_call("logout")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve and print information about a specific access role.")
    parser.add_argument("server", help="Server address")
    parser.add_argument("username", help="Username")
    parser.add_argument("password", help="Password")
    parser.add_argument("access_role_name", help="Name of the access role to retrieve")
    args = parser.parse_args()

    get_access_role_info(args.server, args.username, args.password, args.access_role_name)
