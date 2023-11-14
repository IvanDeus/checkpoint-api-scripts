import argparse
from cpapi import APIClient, APIClientArgs
# just show all host and network type objects
def show_network_objects(server, username, password):
    # Setup client
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        # Login
        login_res = client.login(username, password)
        if login_res.success is False:
            print("Login failed:", login_res.error_message)
            exit(1)
        print("Network Hosts and Objects:")
        # Initialize variables for pagination and storing objects
        all_objects = []
        offset = 0
        limit = 200
        total = 1  # Dummy value to start the loop
        # Fetch objects of type 'CpmiHostCkp' and 'network_objects'
        while offset < total:
            show_objects_res = client.api_call("show-objects", {"offset": offset, "limit": limit})
            if show_objects_res.success:
                objects_batch = show_objects_res.data.get("objects", [])
                total = show_objects_res.data.get("total", 0)
                # Filter for objects of type 'host' and 'network'
                for obj in objects_batch:
                    if obj.get("type") in ["host", "network"]:
                        print(f"UID: {obj['uid']}, Name: {obj['name']}, Type: {obj['type']}")
                        all_objects.append({
                            "uid": obj["uid"],
                            "name": obj["name"],
                            "type": obj["type"]
                        })
                # Update offset for the next batch
                offset += limit
            else:
                print("Failed to retrieve objects:", show_objects_res.error_message)
                break
        # Logout
        client.api_call("logout")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve and print network hosts and objects.")
    parser.add_argument("server", help="Server address")
    parser.add_argument("username", help="Username")
    parser.add_argument("password", help="Password")
    args = parser.parse_args()
    show_network_objects(args.server, args.username, args.password)
