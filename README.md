# checkpoint-api-scripts
Check Point firewall management API add or modify multiple objects api scripts
cpapi required, can run directly from R8x.xx management machine

---

## 📄 Script: `addaccessrolefromfile.py`

### ✅ Purpose:
This script creates **Access Roles** in a Check Point Firewall using data from a JSON file. It connects to the Check Point Management Server via the API, logs in, creates roles based on the input JSON data, publishes the changes, and logs out.

Each Access Role is defined with a name and associated networks (by name), with default permissions set to allow "any" for machines, remote access clients, and users.

---

## ⚙️ Usage Example

### Command Line:
```bash
python addaccessrolefromfile.py <server> <username> <password> <json_file>
```

### Example:
```bash
python addaccessrolefromfile.py 192.168.1.10 admin securepass123 access_roles.json
```

Where:
- `192.168.1.10` – IP address of your Check Point Management Server
- `admin` – administrator username
- `securepass123` – password for the user
- `access_roles.json` – path to the JSON file containing access role definitions

---

## 📁 Input File Format (`access_roles.json`)

Each object in the JSON array must include `"Access Role"` and `"Networks"` keys:

```json
[
    {
        "Access Role": "HR_Access_Role",
        "Networks": [
            {"name": "HR_Network_1"},
            {"name": "HR_Network_2"}
        ]
    },
    {
        "Access Role": "DevTeam_Access_Role",
        "Networks": [
            {"name": "Development_Network"}
        ]
    }
]
```

---

## 🧾 What the Script Does:

1. Logs into the Check Point Management Server.
2. Iterates through each access role definition in the JSON file.
3. Creates an access role linked to specified network objects.
4. Publishes all changes.
5. Logs out from the session.

---

## 📄 Script: `addoneaccrolewithnetnldapgrp.py`

### ✅ Purpose:
This script creates a **single Access Role** in a Check Point Firewall with specific network access and LDAP-based user group restrictions using the Check Point Management API.

It is useful for scenarios where you want to define an access role that allows access only to certain networks and restricts users to a specific LDAP group.

---

## ⚙️ Usage Example

### Command Line:
> **Note:** This script is **hardcoded**, meaning most parameters like server, username, password, and role details are defined inside the script. You can optionally modify it to accept command-line arguments.

```bash
python addoneaccrolewithnetnldapgrp.py
```

### Example Output:
```bash
{'name': 'r017', 'machines': 'any', 'networks': ['hub(1.1.2.1)', 'Net10-8'], 'remote-access-clients': 'any', 'users': {'source': 'bnk', 'selection': 'SecFW_2', 'base-dn': 'OU=GroupsFW,OU=GEN3,OU=Ka,DC=bnk,DC=com'}}
New access role 'r017' created successfully.
Changes published successfully.
```

---

## 📁 Configuration Inside Script

The following variables are hardcoded and should be edited directly in the script:

```python
server = "localhost"  # IP of Check Point Management Server
username = "admin"    # Admin username
password = "111"      # Admin password
new_access_role_name = "r017"  # Name of new access role
```

The access role will be configured with:

| Field | Value |
|-------|-------|
| Machines | any |
| Networks | `hub(1.1.2.1)`, `Net10-8` |
| Remote Access Clients | any |
| Users (LDAP) | Source: `bnk`, Selection: `SecFW_2`, Base DN: `OU=GroupsFW,OU=GEN3,OU=Ka,DC=bnk,DC=com` |

---

## 🧾 What the Script Does:

1. Connects to the local or remote Check Point Management Server.
2. Logs in with provided credentials.
3. Creates one access role with:
   - Specified name
   - Network access to listed objects
   - LDAP-based user group restriction
4. Publishes the session to apply changes.
5. Logs out from the session.

---

## 📄 Script: `getldapgrpsfromaccessroles.py`

### ✅ Purpose:
This script retrieves **Access Roles** from a Check Point Firewall using the Management API and extracts **LDAP user group information** associated with each role. It outputs or saves the data in a structured JSON format that can be used later to recreate or modify access roles using another script (e.g., `addaccessrolefromfile.py`).

It supports pagination to handle large environments and allows saving output to a file.

---

## ⚙️ Usage Example

### Command Line:
```bash
python getldapgrpsfromaccessroles.py <server> <username> <password> [--save <output_file.json>]
```

### Example 1 – Print Output to Console:
```bash
python getldapgrpsfromaccessroles.py 192.168.1.10 admin securepass123
```

### Example 2 – Save Output to File:
```bash
python getldapgrpsfromaccessroles.py 192.168.1.10 admin securepass123 --save access_roles_ldap.json
```

Where:
- `192.168.1.10` – IP address of your Check Point Management Server
- `admin` – administrator username
- `securepass123` – password for the user
- `--save` (optional) – save the result into a JSON file instead of printing it

---

## 📁 Output Format (`access_roles_ldap.json`)

The output will be an array containing each access role and its associated LDAP users/groups:

```json
[
    {
        "Access Role": "HR_Access",
        "Users": [
            {
                "name": "SecTeam",
                "cn": "SecTeam",
                "dn": "OU=Security,DC=example,DC=com"
            }
        ]
    },
    {
        "Access Role": "Dev_Access",
        "Users": [
            {
                "name": "Developers",
                "cn": "Developers",
                "dn": "OU=Development,DC=example,DC=com"
            }
        ]
    }
]
```

Each entry includes:
- The full name of the user/group
- The Common Name (CN)
- The Distinguished Name (DN), split for easier reuse in other scripts

---

## 🧾 What the Script Does:

1. Logs into the Check Point Management Server.
2. Retrieves all access roles using pagination (supports large setups).
3. For each access role, extracts LDAP-based user/group information.
4. Structures the data into a custom JSON format useful for automation.
5. Either prints the data or saves it to a file.
6. Logs out after completing the operation.

---

## 🛠 Tips for Use

- This script is ideal for backing up or analyzing current access role configurations tied to LDAP groups.
- The generated JSON file can be edited and reused with scripts like `addaccessrolefromfile.py` to restore or replicate access roles.

---

## 📄 Script: `getnetworksfromaccessroles.py`

### ✅ Purpose:
This script retrieves all **Access Roles** from a Check Point Firewall using the Management API and extracts the **network objects** associated with each role. The result is saved in a structured JSON file or printed to the console.

This is especially useful for:
- Auditing access roles
- Backing up configurations
- Preparing input files for other scripts like `addaccessrolefromfile.py`

Supports pagination to handle environments with many access roles.

---

## ⚙️ Usage Example

### Command Line:
```bash
python getnetworksfromaccessroles.py <server> <username> <password> [--save <output_file.json>]
```

### Example 1 – Print Output to Console:
```bash
python getnetworksfromaccessroles.py 192.168.1.10 admin securepass123
```

### Example 2 – Save Output to File:
```bash
python getnetworksfromaccessroles.py 192.168.1.10 admin securepass123 --save access_roles_networks.json
```

Where:
- `192.168.1.10` – IP address of your Check Point Management Server
- `admin` – administrator username
- `securepass123` – password for the user
- `--save` (optional) – save the result into a JSON file instead of printing it

---

## 📁 Output Format (`access_roles_networks.json`)

The output will be an array where each entry contains the access role name and its associated networks:

```json
[
    {
        "Access Role": "HR_Access_Role",
        "Networks": [
            {"name": "HR_Network_1"},
            {"name": "HR_Network_2"}
        ]
    },
    {
        "Access Role": "DevTeam_Access_Role",
        "Networks": [
            {"name": "Development_Network"}
        ]
    },
    {
        "Access Role": "All_Networks_Role",
        "Networks": [
            {"name": "any"}
        ]
    }
]
```

Each network object includes:
- `"name"` – the name of the network object in Check Point
- If the access role allows access to `"any"` network, it's marked accordingly

---

## 🧾 What the Script Does:

1. Logs into the Check Point Management Server.
2. Retrieves all access roles using pagination (supports large setups).
3. For each access role, extracts the list of assigned networks.
4. Structures the data into a custom JSON format suitable for automation.
5. Either prints the data or saves it to a file.
6. Logs out after completing the operation.

---

## 🛠 Tips for Use

- This script works well as a **data extraction tool** before bulk updates or backups.
- The generated JSON file can be edited and used as input for scripts that recreate or update access roles.
- Ideal for integration into configuration management or CI/CD pipelines.

---

## 📄 Script: `getoneaccessroleinfo.py`

### ✅ Purpose:
This script retrieves detailed information about a **specific Access Role** from a Check Point Firewall using the Management API. It logs into the server, fetches full details of the specified access role, and prints the raw JSON response to the console.

It’s useful for:
- Troubleshooting access roles
- Viewing configuration details
- Integrating into automation or validation workflows

---

## ⚙️ Usage Example

### Command Line:
```bash
python getoneaccessroleinfo.py <server> <username> <password> <access_role_name>
```

### Example:
```bash
python getoneaccessroleinfo.py 192.168.1.10 admin securepass123 HR_Access_Role
```

Where:
- `192.168.1.10` – IP address of your Check Point Management Server
- `admin` – administrator username
- `securepass123` – password for the user
- `HR_Access_Role` – name of the access role you want to inspect

---

## 🧾 What the Script Does:

1. Logs into the Check Point Management Server.
2. Calls the `show-access-role` API with `"details-level": "full"` for the specified role.
3. Outputs the complete JSON response, showing all configured properties (networks, users, permissions, etc.).
4. Logs out after retrieving the data.

---

## 📁 Sample Output (formatted JSON):

```json
{
  "name": "HR_Access_Role",
  "uid": "123e4567-e89b-12d3-a456-426614174000",
  "type": "access-role",
  "networks": [
    {
      "name": "HR_Network_1",
      "uid": "a1b2c3d4-5678-efgh-90ab-cdef12345678"
    }
  ],
  "users": [
    {
      "dn": "CN=HRGroup,OU=Groups,DC=example,DC=com",
      "name": "HRGroup"
    }
  ],
  "machines": "any",
  "remote-access-clients": "any"
}
```

This gives you full visibility into how the access role is configured in Check Point.

---

## 🛠 Tips for Use

- This script is ideal when you need to debug or document existing access roles.

---
