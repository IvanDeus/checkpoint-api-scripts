# replace_roles_with_sec_roles.py
# Script that reads exported JSON (from export_rules.py) rules, fetches all existing access roles 
# from the Check Point Management Server that start with "Sec", 
# and replaces the access-role in the rule's source with a "Sec" access role 
# sequentially (infinite wrap-around).
# Whenever the script finds an item with "type": "access-role", it swaps just that item 
# for the next available Sec access role in line, while preserving any other objects 
# (like hosts, IPs, or networks) that might exist alongside it in the source field.
# python3 replace_roles_with_sec_roles.py localhost admin ppp news_resolved.json "new_feat_tst Network"

import argparse
import json
import sys
from cpapi import APIClient, APIClientArgs


def get_Secaccess_roles(client):
    """Fetches access roles starting with 'Sec' from the Management Server."""
    Secroles = []
    offset = 0
    limit = 500

    print("Fetching existing access roles from the server...")
    while True:
        res = client.api_call(
            "show-access-roles", {"limit": limit, "offset": offset, "details-level": "standard"}
        )
        if not res.success:
            print(f"Failed to fetch access roles: {res.error_message}")
            raise Exception(f"API Error: {res.error_message}")

        batch = res.data.get("objects", [])
        
        # Filter only roles starting with "Sec"
        for role in batch:
            if role.get("name", "").startswith("Sec"):
                Secroles.append(role)

        if len(batch) == 0 or (offset + limit) >= res.data.get("total", 0):
            break
        
        offset += limit

    print(f"Successfully retrieved {len(Secroles)} 'Sec' access roles.")
    return Secroles


def replace_access_roles_with_Secroles(
    server, username, password, input_json, layer_name
):
    client_args = APIClientArgs(server=server)
    with APIClient(client_args) as client:
        # 1. Login
        login_res = client.login(username, password)
        if not login_res.success:
            print(f"Login failed: {login_res.error_message}")
            sys.exit(1)

        try:
            # 2. Read input JSON file
            with open(input_json, "r") as json_file:
                rules = json.load(json_file)
            # 3. Identify rules where the source contains at least one access-role
            target_rules = []
            for rule in rules:
                sources = rule.get("source", [])
                if any(src.get("type") == "access-role" for src in sources):
                    target_rules.append(rule)

            if not target_rules:
                print("No rules found with 'access-role' in the source field. Exiting.")
                return

            print(
                f"Found {len(target_rules)} rule(s) containing access-roles in the source."
            )
            # 4. Fetch existing Sec access roles
            Secroles = get_Secaccess_roles(client)
            total_Secroles = len(Secroles)

            if total_Secroles == 0:
                raise Exception("No 'Sec' access roles found on the server to use for replacement.")
            # 5. Replace access roles dynamically
            role_index = 0 

            for rule in target_rules:
                rule_uid = rule.get("uid")
                rule_num = rule.get("rule_number")
                original_sources = rule.get("source", [])
                
                new_source_uids = []
                replacement_log = []
                # Evaluate each object in the source field independently
                for src in original_sources:
                    if src.get("type") == "access-role":
                        # Pick a role, wrapping around if we exceed the total available
                        assigned_role = Secroles[role_index % total_Secroles]
                        new_source_uids.append(assigned_role["uid"])
                        
                        replacement_log.append(f"[{src.get('name')}] -> [{assigned_role['name']}]")
                        role_index += 1
                    else:
                        # Keep original non-access-role object
                        new_source_uids.append(src.get("uid"))
                # Prepare payload with the mixed/new list of UIDs
                payload = {
                    "layer": layer_name,
                    "uid": rule_uid,
                    "source": new_source_uids,
                }

                print(f"\nUpdating Rule #{rule_num} (UID: {rule_uid})...")
                for log_msg in replacement_log:
                    print(f"  Replaced: {log_msg}")

                update_res = client.api_call("set-access-rule", payload)
                if update_res.success:
                    print(f"  -> Rule #{rule_num} updated successfully.")
                else:
                    error_msg = update_res.error_message
                    print(f"  -> Failed to update Rule #{rule_num}: {error_msg}")
                    raise Exception(f"Failed to update rule '{rule_uid}': {error_msg}")
            # 6. Publish changes
            print("\nPublishing changes...")
            publish_res = client.api_call("publish", {})
            if publish_res.success:
                print("Changes published successfully.")
            else:
                print(f"Failed to publish changes: {publish_res.error_message}")
                raise Exception(
                    f"Publish failed: {publish_res.error_message}"
                )
        finally:
            # 7. Logout safely
            client.api_call("logout")
            print("Logged out from Management Server.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Replace access-roles in rule sources with Sec access roles, looping them if necessary."
    )
    parser.add_argument("server", help="Management Server IP/Hostname")
    parser.add_argument("username", help="Admin Username")
    parser.add_argument("password", help="Admin Password")
    parser.add_argument("input_json", help="Path to the resolved rules JSON file")
    parser.add_argument(
        "layer_name",
        help="Name of the Access Layer where rules exist (e.g., 'new_feat_tst8120 Network')",
    )

    args = parser.parse_args()

    try:
        replace_access_roles_with_Secroles(
            args.server,
            args.username,
            args.password,
            args.input_json,
            args.layer_name,
        )
    except Exception as e:
        print(f"\nExecution Error: {e}")
        sys.exit(1)
