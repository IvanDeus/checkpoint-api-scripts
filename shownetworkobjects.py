import argparse
from cpapi import APIClient, APIClientArgs
# show selected objects by type from management or any object type
def show_objects(server, username, password, obj_types, negate):
    # Setup client
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        # Login
        login_res = client.login(username, password)
        if login_res.success is False:
            print("Login failed:", login_res.error_message)
            exit(1)
        print(f"Objects of Types: {', '.join(obj_types)}")
        # Initialize variables for pagination and storing objects
        all_objects = []
        offset = 0
        limit = 200
        total = 1  # Dummy value to start the loop
        # Fetch objects of the specified types or all objects if obj_types is ["any"]
        while offset < total:
            show_objects_res = client.api_call("show-objects", {"offset": offset, "limit": limit})
            if show_objects_res.success:
                objects_batch = show_objects_res.data.get("objects", [])
                total = show_objects_res.data.get("total", 0)
                # Filter for objects of the specified types or show all objects
                for obj in objects_batch:
                    if (not negate and (obj_types == ["any"] or obj.get("type") in obj_types)) or (negate and obj.get("type") not in obj_types):
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
        client.api_call("logout")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve and print network objects of specified types or all objects.")
    parser.add_argument("server", help="Server address")
    parser.add_argument("username", help="Username")
    parser.add_argument("password", help="Password")
    parser.add_argument("obj_types", help="Comma-separated list of object types to retrieve (e.g., host, network, any)")
    parser.add_argument("--negate", action="store_true", help="Omit objects of the specified types")
    args = parser.parse_args()
    show_objects(args.server, args.username, args.password, args.obj_types.split(','), args.negate)
