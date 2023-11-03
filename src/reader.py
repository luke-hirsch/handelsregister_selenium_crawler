import xml.etree.ElementTree as ET


class DataXML:
    def __init__(self, xmlpath, namespace={"tns": "http://www.xjustiz.de"}) -> None:
        self.xmlpath = xmlpath
        self.root = ET.parse(self.xmlpath)
        self.namespaces = namespace

    def extract_person_info(self):
        # This list will hold dictionaries of person information
        person_list = []

        # Find all 'beteiligung' elements as they contain both role and personal data
        beteiligung_elements = self.root.findall(".//tns:beteiligung", namespaces=self.namespaces)

        for beteiligung in beteiligung_elements:
            # Find the role code within the 'beteiligung' element
            code_elem = beteiligung.find(".//tns:rollenbezeichnung/code", namespaces=self.namespaces)
            code = code_elem.text.strip() if code_elem is not None else None

            # Find the 'beteiligter' element within the 'beteiligung' element
            beteiligter_elem = beteiligung.find(".//tns:beteiligter", namespaces=self.namespaces)

            if beteiligter_elem is not None:
                # Extract the names from the 'natuerlichePerson' structure within 'beteiligter'
                natuerliche_person_elem = beteiligter_elem.find(".//tns:natuerlichePerson", namespaces=self.namespaces)

                if natuerliche_person_elem is not None:
                    vorname_elem = natuerliche_person_elem.find(".//tns:vorname", namespaces=self.namespaces)
                    nachname_elem = natuerliche_person_elem.find(".//tns:nachname", namespaces=self.namespaces)

                    vorname = vorname_elem.text.strip() if vorname_elem is not None else None
                    nachname = nachname_elem.text.strip() if nachname_elem is not None else None

                    # Append the extracted information to the person list
                    person_list.append({"Vorname": vorname, "Nachname": nachname, "Code": code})

        return person_list

    def extract_organization_info(self):
        organization_list = []
        beteiligung_elements = self.root.findall(".//tns:beteiligung", namespaces=self.namespaces)

        for beteiligung in beteiligung_elements:
            code_elem = beteiligung.find(".//tns:rollenbezeichnung/code", namespaces=self.namespaces)
            if code_elem is not None and code_elem.text.strip() == "288":
                continue

            beteiligter_elem = beteiligung.find(".//tns:beteiligter", namespaces=self.namespaces)
            if beteiligter_elem is not None:
                organisation_elem = beteiligter_elem.find(".//tns:organisation", namespaces=self.namespaces)
                if organisation_elem is not None:
                    bezeichnung_elem = organisation_elem.find(
                        ".//tns:bezeichnung/tns:bezeichnung.aktuell", namespaces=self.namespaces
                    )
                    rechtsform_elem = organisation_elem.find(
                        ".//tns:angabenZurRechtsform/tns:rechtsform/code", namespaces=self.namespaces
                    )
                    registernummer_elem = organisation_elem.find(
                        ".//tns:registereintragung/tns:registernummer", namespaces=self.namespaces
                    )

                    bezeichnung = bezeichnung_elem.text.strip() if bezeichnung_elem is not None else None
                    rechtsform = rechtsform_elem.text.strip() if rechtsform_elem is not None else None
                    registernummer = registernummer_elem.text.strip() if registernummer_elem is not None else None

                    organization_list.append(
                        {"Bezeichnung": bezeichnung, "Rechtsform": rechtsform, "Registernummer": registernummer}
                    )

        return organization_list

    def extract_vertretung(self):
        result = {"texts": None, "codes": None}

        freitext_path = ".//tns:basisdatenRegister/tns:vertretung/tns:allgemeineVertretungsregelung/tns:auswahl_vertretungsbefugnis/tns:vertretungsbefugnisFreitext"
        freitext_elem = self.root.find(freitext_path, namespaces=self.namespaces)
        if freitext_elem is not None and freitext_elem.text:
            result["texts"] = freitext_elem.text.strip()

        codes_path = ".//tns:basisdatenRegister/tns:vertretung//tns:code"
        codes_elems = self.root.findall(codes_path, namespaces=self.namespaces)
        codes = [elem.text.strip() for elem in codes_elems if elem.text]
        if codes:
            result["codes"] = ", ".join(codes)

        if not result["texts"]:
            texts_path = ".//tns:basisdatenRegister/tns:vertretung//tns:text"
            texts_elems = self.root.findall(texts_path, namespaces=self.namespaces)
            texts = [elem.text.strip() for elem in texts_elems if elem.text]
            if texts:
                result["texts"] = ", ".join(texts)

        return result
