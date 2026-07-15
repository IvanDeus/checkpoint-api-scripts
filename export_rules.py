# export_rules.py
# 
# Exports Check Point firewall rules to JSON with Name, UID, and Object Type
# for all sources, destinations, and services.
#
import argparse
import json
import sys
import os
from cpapi import APIClient, APIClientArgs


def select_policy_package(client):
    """Retrieves all policy packages and prompts the user to choose one."""
    print("Retrieving policy packages...")
    packages_res = client.api_call("show-packages", {"limit": 500})

    if not packages_res.success:
        print(f"Failed to retrieve packages: {packages_res.error_message}")
        sys.exit(1)

    packages = packages_res.data.get("packages", [])
    if not packages:
        print("No policy packages found on this management server.")
        sys.exit(1)

    print("\n--- Available Policy Packages ---")
    for idx, pkg in enumerate(packages, 1):
        print(f"[{idx}] {pkg.get('name')}")

    while True:
        try:
            choice = input(f"\nSelect a package (1-{len(packages)}): ").strip()
            if not choice:
                continue
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(packages):
                selected_package = packages[choice_idx].get("name")
                print(f"Selected Package: '{selected_package}'\n")
                return selected_package
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Please enter a valid number.")


def select_access_layer(client, package_name):
    """Retrieves access layers within a package and prompts selection if multiple exist."""
    print(f"Retrieving layers for package '{package_name}'...")
    package_res = client.api_call("show-package", {"name": package_name})

    if not package_res.success:
        print(f"Failed to retrieve package details: {package_res.error_message}")
        sys.exit(1)

    layers = package_res.data.get("access-layers", [])
    if not layers:
        print(f"No access layers found in package '{package_name}'.")
        sys.exit(1)

    if len(layers) == 1:
        layer = layers[0]
        print(f"Automatically selected the only access layer: '{layer.get('name')}'\n")
        return layer.get("uid"), layer.get("name")

    print("--- Available Access Layers ---")
    for idx, layer in enumerate(layers, 1):
        print(f"[{idx}] {layer.get('name')} (Type: {layer.get('type')})")

    while True:
        try:
            choice = input(f"\nSelect an access layer (1-{len(layers)}): ").strip()
            if not choice:
                continue
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(layers):
                selected_layer = layers[choice_idx]
                print(f"Selected Layer: '{selected_layer.get('name')}'\n")
                return selected_layer.get("uid"), selected_layer.get("name")
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Please enter a valid number.")


def extract_rule_details(rule):
    """Parses a raw API rule object to extract key fields defensively."""
    
    def get_object_list(field_list):
        """Safely extracts Name, UID, and Type mappings into structured dictionaries."""
        if not field_list:
            return []
        if not isinstance(field_list, list):
            field_list = [field_list]
            
        objs = []
        for item in field_list:
            if isinstance(item, dict):
                uid = item.get("uid") or item.get("name") or "Unknown"
                name = item.get("name") or uid
                obj_type = item.get("type", "Unknown")
                objs.append({
                    "name": str(name),
                    "uid": str(uid),
                    "type": str(obj_type)
                })
            elif isinstance(item, str):
                objs.append({"name": item, "uid": item, "type": "Unknown"})
            else:
                val = str(item)
                objs.append({"name": val, "uid": val, "type": "Unknown"})
        return objs

    sources = get_object_list(rule.get("source"))
    destinations = get_object_list(rule.get("destination"))
    services = get_object_list(rule.get("service"))

    # Safely handle action
    action_obj = rule.get("action")
    if isinstance(action_obj, dict):
        action = action_obj.get("name") or action_obj.get("uid")
    else:
        action = str(action_obj) if action_obj is not None else "None"

    # Safely handle tracking/logging
    track_obj = rule.get("track", {})
    if isinstance(track_obj, dict):
        track_type = track_obj.get("type", {})
        if isinstance(track_type, dict):
            log_setting = track_type.get("name") or track_type.get("uid") or "None"
        else:
            log_setting = str(track_type)
    else:
        log_setting = str(track_obj)

    return {
        "rule_number": rule.get("rule-number"),
        "uid": rule.get("uid"),
        "name": rule.get("name") or "No Name",
        "source": sources,
        "destination": destinations,
        "service": services,
        "action": action,
        "log": log_setting
    }


def parse_rulebase(rulebase_list):
    """Recursively processes the rulebase to extract rules from sections."""
    flat_rules = []
    for item in rulebase_list:
        item_type = item.get("type")
        if item_type == "access-rule":
            flat_rules.append(extract_rule_details(item))
        elif item_type == "access-section":
            flat_rules.extend(parse_rulebase(item.get("rulebase", [])))
    return flat_rules


def extract_unique_uids(rules):
    """Finds all unique 36-character UIDs across all relevant rule fields."""
    uids = set()
    for rule in rules:
        for field in ["source", "destination", "service"]:
            for item in rule.get(field, []):
                uid = item.get("uid", "")
                if isinstance(uid, str) and len(uid) == 36 and "-" in uid:
                    uids.add(uid)
        for field in ["action", "log"]:
            val = rule.get(field)
            if isinstance(val, str) and len(val) == 36 and "-" in val:
                uids.add(val)
    return uids


def resolve_uids_in_memory(client, rules):
    """Performs secondary show-object lookups to resolve UIDs into names and types."""
    unique_uids = extract_unique_uids(rules)
    if not unique_uids:
        print("No unassigned UIDs found to resolve.")
        return rules

    print(f"Found {len(unique_uids)} unique UIDs. Starting secondary object retrieval...")
    uid_map = {}

    for idx, uid in enumerate(unique_uids, 1):
        res = client.api_call("show-object", {"uid": uid})
        if res.success:
            obj_data = res.data.get("object", {})
            obj_name = obj_data.get("name", uid)
            obj_type = obj_data.get("type", "Unknown")
            uid_map[uid] = {"name": obj_name, "type": obj_type}
        else:
            uid_map[uid] = {"name": uid, "type": "Unknown"}
        
        print(f" -> Resolving: {idx}/{len(unique_uids)} completed", end="\r")
    print("\nSecondary object retrieval complete.")

    # Map the resolved names and types back onto the rules structure
    resolved_rules = []
    for rule in rules:
        resolved_rule = rule.copy()
        
        # Resolve structured list fields (source, destination, service)
        for field in ["source", "destination", "service"]:
            resolved_list = []
            for item in rule.get(field, []):
                uid = item.get("uid", "")
                existing_name = item.get("name", uid)
                existing_type = item.get("type", "Unknown")
                
                # Retrieve from map or fallback to what we already extracted
                resolved_info = uid_map.get(uid, {"name": existing_name, "type": existing_type})
                
                # Prefer resolved values if they are valid, otherwise keep existing
                final_name = resolved_info["name"] if resolved_info["name"] != uid else existing_name
                final_type = resolved_info["type"] if resolved_info["type"] != "Unknown" else existing_type
                
                resolved_list.append({
                    "name": final_name,
                    "uid": uid,
                    "type": final_type
                })
            resolved_rule[field] = resolved_list
        
        # Resolve individual fields (keeping action and log as simple strings)
        action_val = rule.get("action")
        resolved_rule["action"] = uid_map.get(action_val, {}).get("name", action_val)
        
        log_val = rule.get("log")
        resolved_rule["log"] = uid_map.get(log_val, {}).get("name", log_val)
        
        resolved_rules.append(resolved_rule)

    return resolved_rules


def export_and_resolve_rules(server, username, password, insecure=False):
    """Orchestrates the single-session fetch, secondary resolution, and export workflow."""
    client_args = APIClientArgs(server=server, unsafe=insecure, unsafe_auto_accept=insecure)

    with APIClient(client_args) as client:
        login_res = client.login(username, password)
        if not login_res.success:
            print("Login failed:", login_res.error_message)
            sys.exit(1)

        try:
            package_name = select_policy_package(client)
            layer_uid, layer_name = select_access_layer(client, package_name)

            print(f"Step 1/2: Fetching rule structure for layer '{layer_name}'...")

            all_rules = []
            limit = 100
            offset = 0
            total = 1

            while offset < total:
                rulebase_res = client.api_call(
                    "show-access-rulebase",
                    {
                        "uid": layer_uid,
                        "limit": limit,
                        "offset": offset,
                        "details-level": "standard"
                    }
                )

                if not rulebase_res.success:
                    print(f"Failed to retrieve rules: {rulebase_res.error_message}")
                    break

                data = rulebase_res.data
                total = data.get("total", 0)
                rulebase_list = data.get("rulebase", [])

                all_rules.extend(parse_rulebase(rulebase_list))
                offset += limit
                print(f" -> Progress: Fetched {min(offset, total)}/{total} rules...", end="\r")

            print(f"\nExtracted {len(all_rules)} rules. Moving to object resolution...")

            print("Step 2/2: Resolving network objects, services, actions, and logs...")
            final_rules = resolve_uids_in_memory(client, all_rules)

            safe_package_name = package_name.lower().replace(" ", "_")
            safe_layer_name = layer_name.lower().replace(" ", "_")
            output_file = f"{safe_package_name}_{safe_layer_name}_rules_resolved.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(final_rules, f, indent=4)

            print(f"Successfully exported and resolved {len(final_rules)} rules to '{output_file}'.")

        finally:
            client.api_call("logout")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export and resolve Check Point firewall rules to JSON.")
    parser.add_argument("server", help="Management Server IP or Hostname")
    parser.add_argument("username", help="API Username")
    parser.add_argument("password", help="API Password")
    parser.add_argument(
        "-k", "--insecure",
        action="store_true",
        help="Skip SSL certificate verification"
    )

    args = parser.parse_args()

    export_and_resolve_rules(args.server, args.username, args.password, insecure=args.insecure)
