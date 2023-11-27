import argparse
from cpapi import APIClient, APIClientArgs
# show selected objects by type from management or any object type
def show_objects(server, username, password, obj_type):
    # Setup client
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        # Login
        login_res = client.login(username, password)
        if login_res.success is False:
            print("Login failed:", login_res.error_message)
            exit(1)
        print(f"{obj_type.capitalize()} Objects:")
        # Initialize variables for pagination and storing objects
        all_objects = []
        offset = 0
        limit = 200
        total = 1 
        # Fetch objects of the specified type or all objects if obj_type is "any"
        while offset < total:
            show_objects_res = client.api_call("show-objects", {"offset": offset, "limit": limit})
            if show_objects_res.success:
                objects_batch = show_objects_res.data.get("objects", [])
                total = show_objects_res.data.get("total", 0)
                # Filter for objects of the specified type or show all objects
                for obj in objects_batch:
                    if obj_type == "any" or obj.get("type") == obj_type:
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
    parser = argparse.ArgumentParser(description="Retrieve and print network objects of a specified type or all objects.")
    parser.add_argument("server", help="Server address")
    parser.add_argument("username", help="Username")
    parser.add_argument("password", help="Password")
    parser.add_argument("obj_type", help="Type of objects to retrieve (e.g., host, network, any)")
    args = parser.parse_args()
    show_objects(args.server, args.username, args.password, args.obj_type)
