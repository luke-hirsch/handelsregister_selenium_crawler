import time
from datetime import datetime
import os, shutil
from src.utility import (
    recreate_directory,
    write_to_terminal,
    clean_list,
    read_csv,
    append_to_csv,
    initialize_csv,
    move_and_rename_files,
    waiting_for_godot,
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.reader import DataXML

DOWNLOAD_DIR = "downloads"
RESULTS_DIR = "results"
BACKUP_DIR = "storage"
PDF_DIR = os.path.join(RESULTS_DIR, "PDF")
XML_DIR = os.path.join(RESULTS_DIR, "XML")
RESULT_CSV = os.path.join(RESULTS_DIR, "results.csv")
TIME_MIN = 30
LINK = "https://www.handelsregister.de/rp_web/erweitertesuche.xhtml"


class MyConnector:
    chrome_options = webdriver.ChromeOptions()
    download_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)

    def __init__(self, link) -> None:
        self.driver.get(link)

    def init_wait(self):
        self.wait = WebDriverWait(self.driver, 50)

    # #.until(EC.url_to_be(destination))
    # until(EC.element_to_be_clickable((By.ID, 'form:btnSuche')))

    def search(
        self,
        search_key: str,
        searchfieldID="form:schlagwoerter",
        mode="all",
        similar=False,
        submitID="form:btnSuche",
        state=None,
        zip_code=None,
        zip_ID="form:postleitzahl",
        city=None,
        city_ID="form:ort",
        street=None,
        street_ID="form:strasse",
        register=None,
        register_ID="form:registerNummer",
    ):
        self.wait.until(EC.url_to_be(LINK))
        searchfield = self.driver.find_element(By.ID, searchfieldID)
        searchfield.clear()
        searchfield.send_keys(search_key)

        if state:
            state_input_id = f"form:{state}_input"
            state_input = self.driver.find_element(By.ID, state_input_id)
            if state_input.get_attribute("aria-checked") == "false":
                state_id = f"form:{state}"
                state_checkbox = self.driver.find_element(By.ID, state_id)
                self.wait.until(EC.element_to_be_clickable(state_checkbox))
                state_checkbox.click()

        zip_input = self.driver.find_element(By.ID, zip_ID)
        zip_input.clear()
        if zip_code:
            zip_input.send_keys(zip_code)

        city_input = self.driver.find_element(By.ID, city_ID)
        city_input.clear()
        if city:
            city_input.send_keys(city)

        street_input = self.driver.find_element(By.ID, street_ID)
        street_input.clear()
        if street:
            street_input.send_keys(street)

        register_input = self.driver.find_element(By.ID, register_ID)
        register_input.clear()
        if register:
            register_input.send_keys(register)

        self.select_search_options(mode, similar)

        submit_button = self.driver.find_element(By.ID, submitID)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        self.wait.until(EC.element_to_be_clickable(submit_button))

        submit_button.click()

    def reset_search(
        self,
        state=None,
        searchfieldID="form:schlagwoerter",
        zip_ID="form:postleitzahl",
        city_ID="form:ort",
        street_ID="form:strasse",
        register_ID="form:registerNummer",
    ):
        self.wait.until(EC.url_to_be(LINK))
        searchfield = self.driver.find_element(By.ID, searchfieldID)
        searchfield.clear()

        if state:
            state_input_id = f"form:{state}_input"
            state_input = self.driver.find_element(By.ID, state_input_id)
            check_state = state_input.get_attribute("aria-checked")
            if check_state == "true":
                state_id = f"form:{state}"
                state_checkbox = self.driver.find_element(By.ID, state_id)
                self.wait.until(EC.element_to_be_clickable(state_checkbox))
                state_checkbox.click()

        zip_input = self.driver.find_element(By.ID, zip_ID)
        zip_input.clear()
        city_input = self.driver.find_element(By.ID, city_ID)
        city_input.clear()
        street_input = self.driver.find_element(By.ID, street_ID)
        street_input.clear()
        register_input = self.driver.find_element(By.ID, register_ID)
        register_input.clear()
        self.select_search_options("all", False)

    def select_search_options(self, mode="all", similar=False):
        options_form = self.driver.find_element(By.ID, "form:schlagwortOptionen")
        radio_buttons = options_form.find_elements(By.CLASS_NAME, "ui-g")
        if mode == "all":
            childdivs = radio_buttons[0].find_elements(By.CSS_SELECTOR, "div")
            self.wait.until(EC.element_to_be_clickable(childdivs[1]))
            childdivs[1].click()
        elif mode == "exact":
            childdivs = radio_buttons[2].find_elements(By.CSS_SELECTOR, "div")
            self.wait.until(EC.element_to_be_clickable(childdivs[1]))
            childdivs[1].click()
        elif mode == "min":
            childdivs = radio_buttons[1].find_elements(By.CSS_SELECTOR, "div")
            self.wait.until(EC.element_to_be_clickable(childdivs[1]))
            childdivs[1].click()
        else:
            self.log_error("search mode not available")

        if similar:
            similar_checkbox = self.driver.find_element(By.ID, "form:aenlichLautendeSchlagwoerterBoolChkbox")
            self.wait.until(EC.element_to_be_clickable(similar_checkbox))
            similar_checkbox.click()

    def close_connection(self):
        self.driver.close()

    def results_count(self):
        self.wait.until(EC.url_to_be("https://www.handelsregister.de/rp_web/ergebnisse.xhtml"))
        self.wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "table")))
        count = len(self.driver.find_elements(By.TAG_NAME, "table")) - 1
        return count

    def save_results(self, tablenumber: int = 1):
        try:
            self.save_result_xml(tablenumber)
        except Exception as e:
            self.log_error("XML konnte nicht gespeichert werden", str(e))

        self.driver.back()
        try:
            self.save_result_pdf(tablenumber)
        except Exception as e:
            self.log_error("PDF konnte nicht gespeichert werden", str(e))
        self.driver.back()
        return True

    def save_result_xml(self, tablenumber: int = 1):
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        rows = tables[tablenumber].find_elements(By.TAG_NAME, "tr")
        colums = rows[1].find_elements(By.TAG_NAME, "td")
        links = colums[3].find_elements(By.TAG_NAME, "a")
        links[-1].click()
        self.wait.until(EC.url_to_be("https://www.handelsregister.de/rp_web/chargeinfo.xhtml"))
        download_button = self.driver.find_element(By.ID, "form:kostenpflichtigabrufen")
        download_button.click()

    def save_result_pdf(self, tablenumber: int = 1):
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        rows = tables[tablenumber].find_elements(By.TAG_NAME, "tr")
        colums = rows[1].find_elements(By.TAG_NAME, "td")
        links = colums[3].find_elements(By.TAG_NAME, "a")
        links[0].click()
        self.wait.until(EC.url_to_be("https://www.handelsregister.de/rp_web/chargeinfo.xhtml"))
        download_button = self.driver.find_element(By.ID, "form:kostenpflichtigabrufen")
        download_button.click()

    def log_error(self, msg):
        print("error occurred:", msg)
        raise Exception(msg)


def main():
    recreate_directory(DOWNLOAD_DIR)
    searchmodes = [
        {"msg": "Suche nach Keywords: ", "mode": "all", "similar": False, "address": True},
        {"msg": "Suche nach Keywords: ", "mode": "all", "similar": False, "address": False},
        {"msg": "Suche nach Keywords und ähnlichen: ", "mode": "all", "similar": True, "address": True},
        {"msg": "Suche nach Keywords und ähnlichen: ", "mode": "all", "similar": True, "address": False},
        {"msg": "Suche nach allen Keywrods: ", "mode": "min", "similar": False, "address": True},
        {"msg": "Suche nach allen Keywrods: ", "mode": "min", "similar": False, "address": False},
        {"msg": "Suche nach allen Keywords und ähnlichen: ", "mode": "min", "similar": True, "address": False},
        {"msg": "Suche nach allen Keywords und ähnlichen: ", "mode": "min", "similar": True, "address": True},
        # {"msg": "Suche genau nach Keyword: ", "mode": "exact", "similar": False, "address": True},
        # {"msg": "Suche genau nach Keyword: ", "mode": "exact", "similar": False, "address": False},
        {
            "msg": "Suche genau nach Keyword und ähnlichen: ",
            "mode": "exact",
            "similar": True,
            "address": True,
        },
        {
            "msg": "Suche genau nach Keyword und ähnlichen: ",
            "mode": "exact",
            "similar": True,
            "address": False,
        },
    ]
    my_companies = read_csv("shortlist.csv")
    unwanted_stuff = [
        "und",
        "e.",
        "V.",
        "GmbH",
        "gGmbH",
        "GBR",
        "GbR",
        "/",
        "&",
        "e.V.",
        "eV",
    ]
    error_count = 0
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        os.makedirs(PDF_DIR)
        os.makedirs(XML_DIR)
        print(f"Directory '{RESULTS_DIR}' created.")
    else:
        backup = os.path.join(BACKUP_DIR, str(datetime.now()))
        shutil.move(
            RESULTS_DIR,
            backup,
        )
        os.makedirs(RESULTS_DIR)
        os.makedirs(PDF_DIR)
        os.makedirs(XML_DIR)
    initialize_csv(
        RESULT_CSV,
        [
            "Name",
            "Vorname",
            "Rolle",
            "Firma",
            "Rechtsform",
            "Registernummer",
            "Bundesland",
            "Ort",
            "PLZ",
            "Straße",
            "Code_Vertretungsberechtigung",
            "Freitext_Vertretungsberechtigung",
            "Hinweis",
        ],
    )

    connection = MyConnector(LINK)
    connection.init_wait()

    for company in my_companies:
        search_count = 0
        success = False
        time_start = time.perf_counter()
        splitted_str = str(company["Firma"]).split(" ")
        unwanted_stuff.append(str(company["Ort"]))
        keywords = clean_list(splitted_str, unwanted_stuff)
        keywords.insert(0, str(company["Firma"]))

        try:
            for word in keywords:
                if success:
                    break
                for search in searchmodes:
                    try:
                        write_to_terminal(f"{search['msg']}{word}")
                        if search["address"]:
                            connection.search(
                                search_key=word,
                                state=str(company["Bundesland"]),
                                zip_code=str(company["PLZ"]),
                                street=str(company["Straße"]),
                                mode=search["mode"],
                                similar=search["similar"],
                                city=str(company["Ort"]),
                            )
                        else:
                            connection.search(
                                search_key=word,
                                state=str(company["Bundesland"]),
                                zip_code=None,
                                street=None,
                                mode=search["mode"],
                                similar=search["similar"],
                                city=None,
                            )
                        search_count += 1

                    except Exception as e:
                        write_to_terminal(f"Fehler: {e}")
                        error_count += 1
                        continue

                    if connection.results_count() == 1:
                        write_to_terminal(f"speicher für {company['Firma']}")
                        try:
                            success = connection.save_results(1)
                            connection.driver.get(LINK)
                            connection.reset_search(state=company["Bundesland"])
                            break
                        except Exception as e:
                            try:
                                connection.save_results(1)
                                connection.driver.get(LINK)
                                connection.reset_search(state=company["Bundesland"])
                                break
                            except Exception as e:
                                line = {
                                    "Name": None,
                                    "Vorname": None,
                                    "Rolle": None,
                                    "Firma": company["Firma"],
                                    "Rechtsform": None,
                                    "Registernummer": None,
                                    "Bundesland": company["Bundesland"],
                                    "Ort": company["Ort"],
                                    "PLZ": company["PLZ"],
                                    "Straße": company["Straße"],
                                    "Code_Vertretungsberechtigung": None,
                                    "Freitext_Vertretungsberechtigung": None,
                                    "Hinweis": f"Fehler: Ergebnis gefunden, aber Selenium Treiber bricht beim Speichern der Dateien mehrfach ab.",
                                }
                                print(f"{company['Firma']} - Error: {e}")
                                append_to_csv(RESULT_CSV, line)
                                connection.driver.get(LINK)
                                connection.reset_search(state=company["Bundesland"])
                                error_count += 1
                                success = True
                                break
                        break

                    connection.driver.back()
                    connection.wait.until(EC.url_to_be(LINK))

        except Exception as e:
            line = {
                "Name": None,
                "Vorname": None,
                "Rolle": None,
                "Firma": company["Firma"],
                "Rechtsform": None,
                "Registernummer": None,
                "Bundesland": company["Bundesland"],
                "Ort": company["Ort"],
                "PLZ": company["PLZ"],
                "Straße": company["Straße"],
                "Code_Vertretungsberechtigung": None,
                "Freitext_Vertretungsberechtigung": None,
                "Hinweis": f"Fehler: Selenium Treiber bricht ab bei Suche.",
            }
            print(f"{company['Firma']} - Error: {e}")
            append_to_csv(RESULT_CSV, line)
            connection.driver.get(LINK)
            connection.reset_search(state=company["Bundesland"])
            error_count += 1
            continue
        print("\ndownload")
        xml_path, msg = move_and_rename_files(DOWNLOAD_DIR, XML_DIR, PDF_DIR, str(company["Firma"]))
        print("moved")
        write_to_terminal(msg)

        if (xml_path == None) or (not os.path.exists(xml_path)):
            line = {
                "Name": None,
                "Vorname": None,
                "Rolle": None,
                "Firma": company["Firma"],
                "Rechtsform": None,
                "Registernummer": None,
                "Bundesland": company["Bundesland"],
                "Ort": company["Ort"],
                "PLZ": company["PLZ"],
                "Straße": company["Straße"],
                "Code_Vertretungsberechtigung": None,
                "Freitext_Vertretungsberechtigung": None,
                "Hinweis": f"Fehler:Kein Eintrag gefunden :(",
            }
            print(f"{company['Firma']} - Kein Eintrag gefunden :(")
            append_to_csv(RESULT_CSV, line)
            connection.driver.get(LINK)
            connection.reset_search(state=company["Bundesland"])
            error_count += 1
            continue
        data = DataXML(xmlpath=xml_path)
        associates = data.extract_person_info()
        ass_companies = data.extract_organization_info()
        vertretung = data.extract_vertretung()
        for ass_compony in ass_companies:
            for associate in associates:
                line = {
                    "Name": associate["Nachname"],
                    "Vorname": associate["Vorname"],
                    "Rolle": associate["Code"],
                    "Firma": ass_compony["Bezeichnung"],
                    "Rechtsform": ass_compony["Rechtsform"],
                    "Registernummer": ass_compony["Registernummer"],
                    "Bundesland": company["Bundesland"],
                    "Ort": company["Ort"],
                    "PLZ": company["PLZ"],
                    "Straße": company["Straße"],
                    "Code_Vertretungsberechtigung": str(vertretung.get("codes")),
                    "Freitext_Vertretungsberechtigung": str(vertretung["texts"]).replace("\n", " ").strip(),
                }
                append_to_csv(RESULT_CSV, line)

        time_end = time.perf_counter()
        connection.driver.get(LINK)
        connection.reset_search(state=str(company["Bundesland"]))

        print(search_count)
        time_min = TIME_MIN * search_count
        waiting_for_godot(time_start=time_start, time_end=time_end, time_min=time_min)

    if error_count > 0:
        print(
            f"\n\n###############################################\n\n  Suche abgeschlossen. \n\n  Es wurden {error_count} Fehler registriert\n\n###############################################"
        )
    else:
        print(
            f"\n\n###############################################\n\n  der crawler hat geslayed\n\n###############################################\n\n"
        )
    connection.close_connection()


if __name__ == "__main__":
    main()
