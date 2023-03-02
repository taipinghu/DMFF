import xml.etree.ElementTree as ET
from xml.dom import minidom


def genStrDict(olddict):
    newdict = {}
    for k, v in olddict.items():
        newdict[k] = f"{v}"
    return newdict


class XMLIO:

    def __init__(self):
        self._data = {
            "AtomTypes": [],
            "Residues": [],
            "Forces": {}
        }

    def clean(self):
        self._data = {
            "AtomTypes": [],
            "Residues": [],
            "Forces": {}
        }

    def loadXML(self, xml: str):
        root = ET.parse(xml).getroot()
        for child in root:
            # AtomTypes
            if child.tag == "AtomTypes":
                for atom in child:
                    if atom.tag == "Type":
                        self._data["AtomTypes"].append(atom)
            # Residues
            elif child.tag == "Residues":
                for residue in child:
                    if residue.tag == "Residue":
                        self._data["Residues"].append(residue)
            # Forces
            else:
                if "Force" in child.tag:
                    if child.tag not in self._data["Forces"]:
                        self._data["Forces"][child.tag] = []
                    self._data["Forces"][child.tag].append(child)

    def parseXML(self):
        ret = {
            "AtomTypes": [],
            "Residues": [],
            "Forces": {}
        }
        ret["AtomTypes"] = self.parseAtomTypes()
        ret["Residues"] = self.parseResidues()
        for force in self._data["Forces"].keys():
            ret["Forces"][force] = self.parseForce(self._data["Forces"][force])
        return ret

    def parseAtomTypes(self):
        ret = []
        for atype in self._data["AtomTypes"]:
            ret.append(atype.attrib)
            if "element" not in ret[-1]:
                ret[-1]["element"] = "none"
        return ret

    def parseResidues(self):
        ret = []
        for residue in self._data["Residues"]:
            res = {
                "name": None, "particles": [], "bonds": [], "externals": [], "vsites": []
            }
            res["name"] = residue.attrib["name"]
            for item in residue:
                if item.tag == "Atom":
                    ainner = {}
                    for key in item.attrib:
                        if key in ["name", "type"]:
                            ainner[key] = item.attrib[key]
                        else:
                            ainner[key] = float(item.attrib[key])
                    res["particles"].append(ainner)
                if item.tag == "VirtualSite":
                    vinner = {}
                    for key in item.attrib.keys():
                        val = item.attrib[key]
                        if "atom" in key or "index" in key:
                            vinner[key] = int(val)
                        elif "weight" in key:
                            vinner[key] = float(val)
                        else:
                            vinner[key] = val
                    res["vsites"].append(vinner)
                if item.tag == "Bond":
                    res["bonds"].append(item.attrib)
                if item.tag == "ExternalBond":
                    res["externals"].append(item.attrib["atomName"])
            ret.append(res)
        return ret

    def parseForce(self, nodes):
        ret = {"meta": nodes[0].attrib, "node": []}
        for node in nodes:
            for child in node:
                inner = {}
                inner["name"] = child.tag
                inner["attrib"] = child.attrib
                ret["node"].append(inner)
        return ret

    def writeXML(self, out: str, ffinfo: dict, write_residues=True, write_atomtypes=True, write_forces=True):
        root = ET.Element("ForceField")
        if write_atomtypes:
            atype = ET.SubElement(root, "AtomTypes")
            for atp in ffinfo["AtomTypes"]:
                new = ET.SubElement(atype, "Type")
                new.attrib = genStrDict(atp)
        if write_residues:
            residues = ET.SubElement(root, "Residues")
            for res in ffinfo["Residues"]:
                residue = ET.SubElement(residues, "Residue")
                residue.attrib = {"name": res["name"]}
                # write Atom
                for atom in res["particles"]:
                    anode = ET.SubElement(residue, "Atom")
                    anode.attrib = genStrDict(atom)
                for vsite in res["vsites"]:
                    vnode = ET.SubElement(residue, "VirtualSite")
                    vnode.attrib = genStrDict(vsite)
                # write Bonds
                for bond in res["bonds"]:
                    bnode = ET.SubElement(residue, "Bond")
                    bnode.attrib = (bond)
                # write External
                for external in res["externals"]:
                    enode = ET.SubElement(residue, "ExternalBond")
                    enode.attrib = genStrDict({"atomName": external})

        if write_forces:
            for force_name in ffinfo["Forces"].keys():
                force_info = ffinfo["Forces"][force_name]
                fnode = ET.SubElement(root, force_name)
                fnode.attrib = genStrDict(force_info["meta"])
                for node in force_info["node"]:
                    subnode = ET.SubElement(fnode, node["name"])
                    subnode.attrib = genStrDict(node["attrib"])

        tree = ET.ElementTree(root)
        xmlstr = minidom.parseString(
            ET.tostring(root)).toprettyxml(indent="   ")
        with open(out, "w") as f:
            f.write(xmlstr)
