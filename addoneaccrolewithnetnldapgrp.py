from cpapi import APIClient, APIClientArgs
# Define the server and credentials
server = "localhost"
username = "admin"
password = "111"
# New access role nets and ldap information
new_access_role_name = "r017"  # Replace with the desired new access role name
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
        "machines": "any",
        "networks": ["hub(1.1.2.1)", "Net10-8"],
        "remote-access-clients": "any",
        "users": {
            "source": "bnk",
            "selection": "SecFW_2",
            "base-dn": "OU=GroupsFW,OU=GEN3,OU=Ka,DC=bnk,DC=com"
        }
    }
    print (payload)
    # Create the new access role
    add_access_role_res = client.api_call("add-access-role", payload)
    if add_access_role_res.success:
        print(f"New access role '{new_access_role_name}' created successfully.")
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
