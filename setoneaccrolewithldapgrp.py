from cpapi import APIClient, APIClientArgs
# Define the server and credentials
server = "localhost"
username = "admin"
password = "123123"
new_access_role_name = "rol11"  # Replace with the desired new access role name
# Setup client
client_args = APIClientArgs(server=server)
with APIClient(client_args) as client:
    # Login
    login_res = client.login(username, password)
    if login_res.success is False:
        print("Login failed:", login_res.error_message)
        exit(1)
    # Prepare the payload for the API call
    payload = {
        "name": new_access_role_name,
        "users": [{
            "source": "bank",
            "selection": "SecFW_31",
            "base-dn": "OU=GroupsFW,OU=GEN3,OU=Ka,DC=bank,DC=com"
        },
        {
            "source": "bank",
            "selection": "SecFW_33",
            "base-dn": "OU=GroupsFW,OU=GEN3,OU=Ka,DC=bank,DC=com"
        }]
    }
    print (payload)
    add_access_role_res = client.api_call("set-access-role", payload)

    if add_access_role_res.success:
        print(f"Access role '{new_access_role_name}' updated successfully.")
        # Publish the changes
        publish_res = client.api_call("publish", {})
        if publish_res.success:
            print("Changes published successfully.")
        else:
            print("Failed to publish changes:", publish_res.error_message)
    else:
        print(f"Failed to create new access role '{new_access_role_name}':", add_access_role_res.error_message)
    # Logout
    client.api_call("logout")
