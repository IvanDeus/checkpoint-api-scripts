# replace_roles_with_groups.py
# script that reads your exported JSON rules (from python3 export_rules.py localhost admin qqqq), fetches all existing network groups from the Check Point Management Server, 
# and replaces the access-role in the rule's source with a network group sequentially (1st matched rule gets the 1st group, 
# 2nd matched rule gets the 2nd group, and so on).
# Whenever the script finds an item with "type": "access-role", it will swap just that item for the next available network group in line, 
# while preserving any other objects (like hosts, IPs, or networks) that might exist alongside it in the source field. Infinite Wrap-Around

import argparse
import json
import sys
from cpapi import APIClient, APIClientArgs


def get_all_network_groups(client):
    """Fetches all existing network groups from the Management Server."""
    groups = []
    offset = 0
    limit = 500

    print("Fetching existing network groups from the server...")
    while True:
        res = client.api_call(
            "show-groups", {"limit": limit, "offset": offset, "details-level": "standard"}
        )
        if not res.success:
            print(f"Failed to fetch network groups: {res.error_message}")
            raise Exception(f"API Error: {res.error_message}")

        batch = res.data.get("objects", [])
        groups.extend(batch)

        if len(groups) >= res.data.get("total", 0) or len(batch) == 0:
            break
        offset += limit

    print(f"Successfully retrieved {len(groups)} network groups.")
    return groups


def replace_access_roles_with_groups(
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

            # 4. Fetch existing network groups
            network_groups = get_all_network_groups(client)
            total_groups = len(network_groups)

            if total_groups == 0:
                raise Exception("No network groups found on the server to use for replacement.")

            # 5. Replace access roles dynamically
            group_index = 0  # Running counter for cycling through groups

            for rule in target_rules:
                rule_uid = rule.get("uid")
                rule_num = rule.get("rule_number")
                original_sources = rule.get("source", [])
                
                new_source_uids = []
                replacement_log = []

                # Evaluate each object in the source field independently
                for src in original_sources:
                    if src.get("type") == "access-role":
                        # Pick a group, wrapping around if we exceed the total available
                        assigned_group = network_groups[group_index % total_groups]
                        new_source_uids.append(assigned_group["uid"])
                        
                        replacement_log.append(f"[{src.get('name')}] -> [{assigned_group['name']}]")
                        group_index += 1
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
        description="Replace access-roles in rule sources with network groups, looping groups if necessary."
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
        replace_access_roles_with_groups(
            args.server,
            args.username,
            args.password,
            args.input_json,
            args.layer_name,
        )
    except Exception as e:
        print(f"\nExecution Error: {e}")
        sys.exit(1)


