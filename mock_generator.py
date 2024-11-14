import json
import os
import random
from datetime import datetime, timedelta
import uuid

class MockDataGenerator:
    def __init__(self):
        self.output_dir = "output"
        self.base_timestamp = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
        self.namespace = str(random.randint(200, 300))
        self.sites = ["dal3", "stk1"]
        self.vendors = ["paloalto", "aruba"]
        self.vnf_types = {"paloalto": "sse", "aruba": "gateway"}
        self.ip_blocks = {}
        self.vlan_uuids = {}
        
    def create_output_dir(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_ref(self, kind, namespace, name):
        return {
            "kind": kind,
            "version": "v1alpha",
            "namespace": namespace,
            "name": name
        }

    def generate_address(self, site):
        addresses = {
            "dal3": {
                "line1": "1950 N Stemmons Fwy",
                "city": "Dallas",
                "state": "Texas",
                "zipcode": "75207",
                "country": "USA",
                "latitude": 32.80139,
                "longitude": -96.819534,
                "glid": "US8645R52J+F5FBS00"
            },
            "stk1": {
                "line1": "11 Esbogatan",
                "city": "Kista",
                "state": "Stockholms län",
                "zipcode": "164 74",
                "country": "SE",
                "latitude": 59.422306,
                "longitude": 17.918524,
                "glid": "SE9FFVCWC8+RJHBS00"
            }
        }
        return {**addresses.get(site, addresses["dal3"]), "line2": None}

    def generate_metadata(self, labels=None):
        return {
            "dateCreated": self.base_timestamp,
            "dateUpdated": self.base_timestamp + 1000,
            "labels": labels or {}
        }

    def generate_account(self):
        return [{
            "kind": "account",
            "version": "v1alpha",
            "namespace": self.namespace,
            "name": self.namespace,
            "metadata": self.generate_metadata({
                "network-code": "DATAPA",
                "source": "cmd",
                "cmd-company-id": "93",
                "net-lla-naas-aruba-api-classifier": "cmd-backfill"
            }),
            "spec": {
                "networkCode": "DATAPA",
                "name": "Mock Company",
                "kicker": {"id": 780},
                "sid": None,
                "customerGroupRef": self.generate_ref("customergroup", f"cg-93", "cg-93"),
                "connectbase": {"advCpqAccountId": 1077494}
            }
        }]

    def generate_customergroup(self):
        return [{
            "kind": "customergroup",
            "version": "v1alpha",
            "namespace": "cg-93",
            "name": "cg-93",
            "metadata": self.generate_metadata({
                "source": "cmd",
                "cmd-id": "93",
                "net-lla-naas-aruba-api-classifier": "cmd-backfill"
            }),
            "spec": {
                "name": "Mock Company",
                "accountRefs": [self.generate_ref("account", self.namespace, self.namespace)]
            }
        }]

    def generate_site(self):
        sites = []
        for site in self.sites:
            sites.append({
                "kind": "site",
                "version": "v1alpha",
                "namespace": "lla",
                "name": site,
                "metadata": self.generate_metadata({
                    "network": "core",
                    "type": "vpop"
                }),
                "spec": {
                    "address": self.generate_address(site),
                    "friendly": f"{site.upper()} Network Function Virtualization Pod",
                    "vpop": {
                        "name": site,
                        "routers": [
                            {
                                "router": f"cr6-{site}",
                                "routerFqdn": f"cr6-{site}.ip4.lla.net",
                                "primary": True,
                                "interface": "ae11",
                                "group": 192,
                                "inheritGroup": 193,
                                "inheritIntf": "ae11.10",
                                "asn": 3257
                            },
                            {
                                "router": f"cr5-{site}",
                                "routerFqdn": f"cr5-{site}.ip4.lla.net",
                                "primary": False,
                                "interface": "ae11",
                                "group": 192,
                                "inheritGroup": 193,
                                "inheritIntf": "ae11.10",
                                "asn": 3257
                            }
                        ]
                    }
                }
            })
        return sites

    def generate_edge(self):
        edges = []
        for site in self.sites:
            edges.append({
                "kind": "edge",
                "version": "v1alpha",
                "namespace": "lla",
                "name": site,
                "metadata": self.generate_metadata({
                    "network": "core",
                    "type": "vpop"
                }),
                "spec": {
                    "type": "vpop",
                    "siteRef": self.generate_ref("site", "lla", site)
                }
            })
        return edges

    def generate_ipamblock(self):
        blocks = []
        ip_counter = 240
        for site in self.sites:
            for vendor in self.vendors:
                for interface in ["wan1", "lan1"]:
                    name = f"{site}-{vendor}-{interface}"
                    cidr = f"70.66.58.{ip_counter}/29"
                    self.ip_blocks[name] = cidr
                    blocks.append({
                        "kind": "ipamblock",
                        "version": "v1alpha",
                        "namespace": self.namespace,
                        "name": name,
                        "metadata": self.generate_metadata(),
                        "spec": {
                            "prefix": 29,
                            "cidr": cidr,
                            "siteRef": self.generate_ref("site", "lla", site),
                            "type": "IPv4",
                            "slid": "2096796-11669615",
                            "allocationType": "MPLS",
                            "pool": "MPLS WAN"
                        }
                    })
                    ip_counter += 8
        return blocks

    def generate_vlan(self):
        vlans = []
        for site in self.sites:
            for vendor in self.vendors:
                for interface in ["wan1", "lan1"]:
                    name = f"{site}-{vendor}-{interface}"
                    self.vlan_uuids[name] = str(uuid.uuid4())
                    vlans.append({
                        "kind": "vlan",
                        "version": "v1alpha",
                        "namespace": self.namespace,
                        "name": name,
                        "metadata": self.generate_metadata(),
                        "spec": {
                            "uuid": self.vlan_uuids[name],
                            "type": "VPOP-MPLS",
                            "vlanId": 1370,
                            "accessRef": self.generate_ref("access", self.namespace, name)
                        }
                    })
        return vlans

    def generate_firewall(self):
        firewalls = []
        for site in self.sites:
            firewalls.append({
                "kind": "firewall",
                "version": "v1alpha",
                "namespace": self.namespace,
                "name": f"gtwy-{site}-{self.namespace}",
                "metadata": self.generate_metadata({
                    "network": "coporate",
                    "type": "sse"
                }),
                "spec": {
                    "type": "sse",
                    "slid": "2096796-11669615",
                    "size": "Palo-50_PREM-BASIC-YU",
                    "speed": "25m",
                    "edgeSelector": {
                        "edgeRef": self.generate_ref("edge", "lla", site)
                    },
                    "vendor": {"name": "paloalto"}
                }
            })
        return firewalls

    def generate_sdwan(self):
        sdwans = []
        for site in self.sites:
            sdwans.append({
                "kind": "sdwan",
                "version": "v1alpha",
                "namespace": self.namespace,
                "name": f"gtwy-{site}-{self.namespace}",
                "metadata": self.generate_metadata({
                    "network": "coporate",
                    "type": "gateway"
                }),
                "spec": {
                    "type": "gateway",
                    "slid": "2096796-11669615",
                    "size": "SP-50",
                    "speed": "25m",
                    "edgeSelector": {
                        "edgeRef": self.generate_ref("edge", "lla", site)
                    },
                    "vendor": {"name": "aruba"}
                }
            })
        return sdwans

    def generate_orchestrator(self):
        orchestrators = []
        for vendor in self.vendors:
            orchestrators.append({
                "kind": "orchestrator",
                "version": "v1alpha",
                "namespace": self.namespace,
                "name": f"{vendor}-{self.namespace}",
                "metadata": self.generate_metadata({
                    "network": "coporate"
                }),
                "spec": {
                    "slid": "2096796-11669614",
                    "hostname": f"{vendor}-{self.namespace}",
                    "siteRef": self.generate_ref("site", "lla", "dal3"),
                    "vendor": {"name": vendor}
                }
            })
        return orchestrators

    def generate_vnf(self):
        vnfs = []
        for site in self.sites:
            for vendor in self.vendors:
                vnf_type = self.vnf_types[vendor]
                ref_kind = "firewall" if vnf_type == "sse" else "sdwan"
                vnfs.append({
                    "kind": "vnf",
                    "version": "v1alpha",
                    "namespace": self.namespace,
                    "name": f"{site}-{vendor}",
                    "metadata": self.generate_metadata(),
                    "spec": {
                        "type": vnf_type,
                        "slid": "2096796-11669615",
                        "speed": "25m",
                        f"{ref_kind}Ref": self.generate_ref(ref_kind, self.namespace, f"gtwy-{site}-{self.namespace}"),
                        "edgeRef": self.generate_ref("edge", "lla", site),
                        "licenseRef": self.generate_ref("license", self.namespace, f"{site}-{vendor}"),
                        "vendor": {"name": vendor}
                    }
                })
        return vnfs

    def generate_access(self):
        accesses = []
        for site in self.sites:
            for vendor in self.vendors:
                for interface in ["wan1", "lan1"]:
                    name = f"{site}-{vendor}-{interface}"
                    if name not in self.ip_blocks:
                        continue
                        
                    cidr = self.ip_blocks[name]
                    network = cidr.split('/')[0].rsplit('.', 1)[0]
                    base_host = int(cidr.split('/')[0].rsplit('.', 1)[1])
                    
                    accesses.append({
                        "kind": "access",
                        "version": "v1alpha",
                        "namespace": self.namespace,
                        "name": name,
                        "metadata": self.generate_metadata({
                            "workflow-id": str(uuid.uuid4())
                        }),
                        "spec": {
                            "type": "VPOP-MPLS",
                            "siteRef": self.generate_ref("site", "lla", site),
                            "edgeRef": self.generate_ref("edge", "lla", site),
                            "vnfRef": self.generate_ref("vnf", self.namespace, f"{site}-{vendor}"),
                            "ipamBlockRef": self.generate_ref("ipamblock", self.namespace, name),
                            "vlanRef": self.generate_ref("vlan", self.namespace, name),
                            "ipV4": f"{network}.{base_host + 6}",
                            "ipV4Gateway": f"{network}.{base_host + 1}",
                            "ipV4Prefix": 29,
                            "router": {
                                "router": f"cr6-{site}",
                                "routerFqdn": f"cr6-{site}.ip4.lla.net",
                                "primary": True,
                                "group": 192,
                                "asn": 3257,
                                "inheritGroup": 193,
                                "inheritIntf": "ae11.10",
                                "interface": "ae11"
                            },
                            "address": self.generate_address(site),
                            "slid": "2096796-11669615",
                            "vlanId": 1370,
                            "vrfId": random.randint(30101, 30199),
                            "speed": "25m",
                            "status": [{
                                "phase": "provision",
                                "description": "Provision MPLS access.",
                                "status": "completed",
                                "startDate": self.base_timestamp + 1000,
                                "endDate": self.base_timestamp + 2000
                            }]
                        }
                    })
        return accesses

    def generate_all_files(self):
        self.create_output_dir()
        
        # First, generate IP blocks to establish the lookup tables
        self.generate_ipamblock()
        
        # Now generate and save all files in the correct order
        files_to_generate = {
            'site.json': self.generate_site(),
            'edge.json': self.generate_edge(),
            'account.json': self.generate_account(),
            'customergroup.json': self.generate_customergroup(),
            'ipamblock.json': self.generate_ipamblock(),
            'vlan.json': self.generate_vlan(),
            'orchestrator.json': self.generate_orchestrator(),
            'firewall.json': self.generate_firewall(),
            'sdwan.json': self.generate_sdwan(),
            'vnf.json': self.generate_vnf(),
            'access.json': self.generate_access()
        }

        for filename, data in files_to_generate.items():
            output_path = os.path.join(self.output_dir, filename)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Generated {filename}")

if __name__ == "__main__":
    generator = MockDataGenerator()
    generator.generate_all_files()
