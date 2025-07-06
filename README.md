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

