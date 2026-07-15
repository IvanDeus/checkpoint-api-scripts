# replace_roles_with_groups.py
# script that reads your exported JSON rules, fetches all existing network groups from the Check Point Management Server, 
# and replaces the access-role in the rule's source with a network group sequentially (1st matched rule gets the 1st group, 
# 2nd matched rule gets the 2nd group, and so on).
# 
import argparse
import json
import sys
from cpapi import APIClient, APIClientArgs


def get_all_network_groups(client):
    """Fetches all existing network groups from the Management Server."""
    groups = []
    offset = 0
    limit = 200

    print("Fetching existing network groups from the server...")
    while True:
        res = client.api_call(
            "show-groups", {"limit": limit, "offset": offset, "details-level": "basic"}
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

            # 3. Identify rules where the source contains an access-role
            target_rules = []
            for rule in rules:
                sources = rule.get("source", [])
                # Check if any source item has type 'access-role'
                if any(src.get("type") == "access-role" for src in sources):
                    target_rules.append(rule)

            if not target_rules:
                print("No rules found with 'access-role' in the source field. Exiting.")
                return

            print(
                f"Found {len(target_rules)} rule(s) containing an access-role in the source."
            )

            # 4. Fetch existing network groups
            network_groups = get_all_network_groups(client)

            if len(network_groups) < len(target_rules):
                raise Exception(
                    f"Not enough network groups available ({len(network_groups)}) "
                    f"to replace {len(target_rules)} rules."
                )

            # 5. Replace access roles sequentially
            for index, rule in enumerate(target_rules):
                rule_uid = rule.get("uid")
                rule_num = rule.get("rule_number")
                old_sources = [s.get("name") for s in rule.get("source", [])]
                assigned_group = network_groups[index]

                # Prepare payload: replace entire source with the assigned network group UID/name
                payload = {
                    "layer": layer_name,
                    "uid": rule_uid,
                    "source": [assigned_group["uid"]],
                }

                print(
                    f"\nUpdating Rule #{rule_num} (UID: {rule_uid})..."
                    f"\n  Old Source(s): {old_sources}"
                    f"\n  New Source:    {assigned_group['name']} (UID: {assigned_group['uid']})"
                )

                update_res = client.api_call("set-access-rule", payload)
                if update_res.success:
                    print(f"Rule #{rule_num} updated successfully.")
                else:
                    error_msg = update_res.error_message
                    print(f"Failed to update Rule #{rule_num}: {error_msg}")
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
        description="Replace access-roles in rule sources with network groups sequentially."
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
