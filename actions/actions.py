import logging
import re
from typing import Any, Text, Dict, List, Union, Optional
import spacy
from rasa_sdk import Action, Tracker
from rasa_sdk.events import Restarted, EventType, SlotSet, FollowupAction, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction, REQUESTED_SLOT
from selenium.webdriver.chrome.options import Options
import geocoder
from datetime import date
from selenium import webdriver
from bs4 import BeautifulSoup
import getpass
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import time
import requests
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
import requests
import json
import re

logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_md")

latest_action = {}
latest_action["ACTION"] = {}
medical_shop_info = {}
medical_shop_info["OXYGEN"] = {}
medical_shop_info["AMBULANCE"] = {}
medical_shop_info["MEDICAL_STORE"] = {}
medical_shop_info["CONTACT_HOSPITAL"] = {}
medical_dic = {}
oxygen_dic = {}
ambulance_dic = {}
hospital_dic = {}


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def current_location(driver):
    # chrome_options = Options()
    # chrome_options.add_argument("--use-fake-ui-for-media-stream")
    timeout = 20
    # driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("https://mycurrentlocation.net/")
    wait = WebDriverWait(driver, timeout)
    longitude = driver.find_elements_by_xpath('//*[@id="longitude"]')
    longitude = [x.text for x in longitude]
    longitude = str(longitude[0])
    latitude = driver.find_elements_by_xpath('//*[@id="latitude"]')
    latitude = [x.text for x in latitude]
    latitude = str(latitude[0])
    #driver.quit()
    return [latitude,longitude]


driver = get_driver()
co_ordinates = current_location(driver)


def named_entity_spacy_parser(text: str) -> Text:
    """
    This function extracts name from text and return it's value
    :param text: str
    :return: str
    """
    spacy_nlp = spacy.load('en_core_web_md')
    doc = spacy_nlp(text.strip())
    name = set()
    data = {}

    for i in doc.ents:
        entry = str(i.lemma_).lower()
        text = text.replace(str(i).lower(), "")

        # extract artifacts, events and natural phenomenon from text
        if i.label_ in ["ART", "EVE", "NAT", "PERSON"]:
            name.add(entry.title())
    data['name'] = list(name)
    try:
        return data['name'][0]
    except Exception as e:
        return text


class ActionMenu(Action):

    def name(self) -> Text:
        return "action_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        carouselDict = {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "dims": {
                    "width": 100,
                    "height": 100
                },
                "elements": [{
                    "title": "🔎 Local Medical Stores",
                    "subtitle": "",
                    "image_url": "https://img.freepik.com/premium-photo/portrait-smiling-healthcare-worker-modern-pharmacy_109710-1703.jpg?w=2000",
                    "dims": {
                        "width": 50,
                        "height": 50
                    },
                    "buttons": [
                        {
                            "title": "🔎 Search",
                            "type": "postback",
                            "payload": "/action_medicine_store"
                        }]
                },
                    {
                        "title": "Oxygen Tank/Refilling",
                        "subtitle": "",
                        "image_url": "https://media.istockphoto.com/photos/closeup-of-medical-oxygen-flow-meter-shows-low-oxygen-or-an-nearly-picture-id1131194018?k=20&m=1131194018&s=612x612&w=0&h=2Wv-i0yUXeNup_77004ATPzJZEw5mSmWAxe5Moz1uc4=",
                        "dims": {
                            "width": 50,
                            "height": 50
                        },
                        "buttons": [
                            {
                                "title": "🔎 Search",
                                "type": "postback",
                                "payload": "/action_oxygen"
                            }]
                    },
                    {
                        "title": "🚑 Emergency Ambulance Services",
                        "subtitle": "",
                        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSiGlT152tPistCAzqNuHqkGZetLCw6JMq38w&usqp=CAU",
                        "dims": {
                            "width": 50,
                            "height": 50
                        },
                        "buttons": [
                            {
                                "title": "🔎 Search",
                                "type": "postback",
                                "payload": "/action_ambulance"
                            }]
                    },
                    {
                        "title": "🏥 Contact Hospital",
                        "subtitle": "",
                        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSIqzPnxNt51e9nRPs97qAplWFBmFcNGvqZsg&usqp=CAU",
                        "dims": {
                            "width": 50,
                            "height": 50
                        },
                        "buttons": [
                            {
                                "title": "🔎 Search",
                                "type": "postback",
                                "payload": "/action_contact_hospital"
                            }]
                    },
                    {
                        "title": "Preventive Medicines",
                        "subtitle": "",
                        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvt8ofkJ7FeltZni35NemAAu66pS07ILFy5A&usqp=CAU",
                        "dims": {
                            "width": 50,
                            "height": 50
                        },
                        "buttons": [
                            {
                                "title": "🔎 Search",
                                "type": "postback",
                                "payload": "/action_preventive_medicines"
                            }]
                    },
                    {
                        "title": "👩‍⚕ Ask a Doctor ?",
                        "subtitle": "",
                        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTn8LCpQhGvSAmA-rDbflA9MnBB56m5RLLTjA&usqp=CAU",
                        "dims": {
                            "width": 50,
                            "height": 50
                        },
                        "buttons": [
                            {
                                "title": "🔎 Search",
                                "type": "postback",
                                "payload": "/action_ask_doctor"
                            }]
                    },
                    {
                        "title": "Support",
                        "subtitle": "",
                        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSIURfc9XBTog4TcSVJ8DncSlpFLaFMQOqN6g&usqp=CAU",
                        "dims": {
                            "width": 50,
                            "height": 50
                        },
                        "buttons": [
                            {
                                "title": "🔎 Search",
                                "type": "postback",
                                "payload": "/action_support"
                            }]
                    },
                    {
                        "title": "Hospital Beds Enquiry",
                        "subtitle": "",
                        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQazKW7v9IGzgrsLjchCN3aJYgPZhZl3EjPPw&usqp=CAU",
                        "dims": {
                            "width": 50,
                            "height": 50
                        },
                        "buttons": [
                            {
                                "title": "🔎 Search",
                                "type": "postback",
                                "payload": "/start_district_form"
                            }]
                    },
                ]}}

        text = "Please select from the below options.\n\n"
        dispatcher.utter_message(text=text)
        return dispatcher.utter_message(attachment=carouselDict)


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = "Hi I'm DocBot 👨‍⚕️,\n here to help you out,\n in fight against Corona Virus.\n"
        print("IN ACTION HELLO WORLD")
        dispatcher.utter_message(text=text)
        dispatcher.utter_message(
            image='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9FqQYM4E9mhuv7qof408LmEG6IMGIwZqE4A&usqp=CAU')
        # return [FollowupAction("utter_greet")]
        return [FollowupAction("action_menu")]


class ActionSupport(Action):
    logger.info(msg="Class called: ActionContactUs")

    def name(self) -> Text:
        return "action_support"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = "Welcome to AntiCovid Bot Support. Tell me how to help you.\n"

        buttons = [{"title": "Preventive Medicines", "payload": "/action_preventive_medicines"},
                   {"title": "👩‍⚕ Ask a Doctor ?", "payload": "/action_ask_doctor"}]
        dispatcher.utter_button_message(text, buttons)

        return []


class FormContactUs(FormAction):

    def name(self) -> Text:
        return "form_contact_us"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill
           :param: tracker: Tracker
           :return: List[Text]
        """
        return ["name", "email", "phone_number"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """
            This function maps the slot values
            :return: Dict[Text, Union[Dict, List[Dict]]]
        """
        return {
            "name": self.from_text(not_intent=["chitchat"]),
            "email": self.from_text(not_intent=["chitchat"]),
            "phone_number": self.from_text(not_intent=["chitchat"]),
        }

    def validate_name(self,
                      value: Text,
                      dispatcher: CollectingDispatcher,
                      tracker: Tracker,
                      domain: Dict[Text, Any],
                      ) -> Dict[Text, Any]:

        name = named_entity_spacy_parser(value).lower()
        for i in name:
            if ord(i) >= ord('a') and ord(i) <= ord('z'):
                pass
            elif i == ' ':
                pass
            else:
                dispatcher.utter_message("Please don't use special characters in name")
                return {"name": None}
        return {"name": name}

    def validate_phone_number(self,
                              value: Text,
                              dispatcher: CollectingDispatcher,
                              tracker: Tracker,
                              domain: Dict[Text, Any],
                              ) -> Dict[Text, Any]:

        phone = re.findall(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]", value)
        if len(phone) != 0:
            phone = phone[0]
        try:
            if '+' in phone and len(phone) == 13 and type(int(phone.replace('+', ''))) == int:
                return {"phone_number": phone}
        except Exception as e:
            dispatcher.utter_message("Please mention phone number in this format\n +918888888888")
            return {"phone_number": None}
        try:
            if '+' not in phone and len(phone) == 10 and type(int(phone)) == int:
                return {"phone_number": phone}
        except Exception as e:
            dispatcher.utter_message("Please mention phone number in this format\n +918888888888")
            return {"phone_number": None}

    def validate_email(self,
                       value: Text,
                       dispatcher: CollectingDispatcher,
                       tracker: Tracker,
                       domain: Dict[Text, Any],
                       ) -> Dict[Text, Any]:

        mail = value
        r = re.compile(r'[\w\.-]+@[\w\.-]+')
        if r.findall(mail) == []:
            dispatcher.utter_message("I am unable yo validate this email address, can you tell your email again.")
            return {"email": None}
        mail = r.findall(mail)[0].split('@')
        domain = mail[-1].split('.')
        if len(mail) != 2:
            dispatcher.utter_message("Try email in this format abc@gmail.com")
            return {"email": None}
        elif len(domain) != 2:
            dispatcher.utter_message("Try email in this format abc@gmail.com")
            return {"email": None}
        else:
            return {"email": value}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:

        """
            This function retrieves slots information and performs the next step
            :param: dispatcher: CollectingDispatcher
            :param: tracker: Tracker
            :param: domain: Dict[Text, Any]
            :return: AllslotReset(), FollowupAction('action_live_agent')
            """
        name = tracker.get_slot("name")
        email = tracker.get_slot("email")
        phone_number = tracker.get_slot("phone_number")
        dispatcher.utter_message(f"Received these details:- \n{name}\n{email}\n{phone_number}")
        dispatcher.utter_message("Thank You so much for details. Someone from our team will shortly contact you.")
        return [AllSlotsReset()]


class FormGetOtp(FormAction):

    def name(self) -> Text:
        return "form_get_otp"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill
           :param: tracker: Tracker
           :return: List[Text]
        """
        return ["OTP", "name", "age"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """
            This function maps the slot values
            :return: Dict[Text, Union[Dict, List[Dict]]]
        """
        return {
            "OTP": self.from_text(not_intent=["chitchat"]),
            "name": self.from_text(not_intent=["chitchat"]),
            "age": self.from_text(not_intent=["chitchat"]),
        }

    def validate_OTP(self,
                     value: Text,
                     dispatcher: CollectingDispatcher,
                     tracker: Tracker,
                     domain: Dict[Text, Any],
                     ) -> Dict[Text, Any]:
        return {"OTP": value}

    def validate_name(self,
                      value: Text,
                      dispatcher: CollectingDispatcher,
                      tracker: Tracker,
                      domain: Dict[Text, Any],
                      ) -> Dict[Text, Any]:

        name = named_entity_spacy_parser(value).lower()
        for i in name:
            if ord(i) >= ord('a') and ord(i) <= ord('z'):
                pass
            elif i == ' ':
                pass
            else:
                dispatcher.utter_message("Please don't use special characters in name")
                return {"name": None}
        return {"name": name}

    def validate_age(self,
                     value: Text,
                     dispatcher: CollectingDispatcher,
                     tracker: Tracker,
                     domain: Dict[Text, Any],
                     ) -> Dict[Text, Any]:
        return {"age": value}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:

        """
            This function retrieves slots information and performs the next step
            :param: dispatcher: CollectingDispatcher
            :param: tracker: Tracker
            :param: domain: Dict[Text, Any]
            :return: AllslotReset(), FollowupAction('action_live_agent')
            """
        OTP = tracker.get_slot("OTP")
        name = tracker.get_slot("name")
        age = tracker.get_slot("age")

        dispatcher.utter_message(f"Received these details:- \n{OTP}\n{name}\n{age}\n")
        return [FollowupAction("action_get_otp")]


class ActionGetOtp(Action):
    def name(self) -> Text:
        return "action_get_otp"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = tracker.get_slot("name")
        OTP = tracker.get_slot("OTP")
        age = tracker.get_slot("age")

        time.sleep(3)
        for i in driver.find_elements_by_name('otp'):
            try:
                i.clear()
                i.send_keys(OTP)
            except:
                pass
        for i in driver.find_elements_by_id('submitOtp'):
            try:
                i.click()
            except:
                pass
        time.sleep(3)
        driver.find_element_by_name('username').send_keys(name)
        driver.find_element_by_name('ageYears').send_keys(age)
        for i in driver.find_elements_by_tag_name('button'):
            if "SUBMIT" in i.text:
                i.click()

        dispatcher.utter_message("\n\nThank You so much for details. Someone from our team will shortly contact you.")
        return [AllSlotsReset(), FollowupAction("action_menu")]


class FormAskDoctor(FormAction):

    def name(self) -> Text:
        return "form_ask_doctor"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill
           :param: tracker: Tracker
           :return: List[Text]
        """
        return ["email", "phone_number", "message"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """
            This function maps the slot values
            :return: Dict[Text, Union[Dict, List[Dict]]]
        """
        return {
            "email": self.from_text(not_intent=["chitchat"]),
            "phone_number": self.from_text(not_intent=["chitchat"]),
            "message": self.from_text(not_intent=["chitchat"]),

        }

    def validate_phone_number(self,
                              value: Text,
                              dispatcher: CollectingDispatcher,
                              tracker: Tracker,
                              domain: Dict[Text, Any],
                              ) -> Dict[Text, Any]:

        phone = re.findall(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]", value)
        if len(phone) != 0:
            phone = phone[0]
        try:
            if '+' in phone and len(phone) == 13 and type(int(phone.replace('+', ''))) == int:
                return {"phone_number": phone}
        except Exception as e:
            dispatcher.utter_message("Please mention phone number in this format\n +918888888888")
            return {"phone_number": None}
        try:
            if '+' not in phone and len(phone) == 10 and type(int(phone)) == int:
                return {"phone_number": phone}
        except Exception as e:
            dispatcher.utter_message("Please mention phone number in this format\n +918888888888")
            return {"phone_number": None}

    def validate_email(self,
                       value: Text,
                       dispatcher: CollectingDispatcher,
                       tracker: Tracker,
                       domain: Dict[Text, Any],
                       ) -> Dict[Text, Any]:

        mail = value
        r = re.compile(r'[\w\.-]+@[\w\.-]+')
        if r.findall(mail) == []:
            dispatcher.utter_message("I am unable yo validate this email address, can you tell your email again.")
            return {"email": None}
        mail = r.findall(mail)[0].split('@')
        domain = mail[-1].split('.')
        if len(mail) != 2:
            dispatcher.utter_message("Try email in this format abc@gmail.com")
            return {"email": None}
        elif len(domain) != 2:
            dispatcher.utter_message("Try email in this format abc@gmail.com")
            return {"email": None}
        else:
            return {"email": value}

    def validate_message(self,
                         value: Text,
                         dispatcher: CollectingDispatcher,
                         tracker: Tracker,
                         domain: Dict[Text, Any],
                         ) -> Dict[Text, Any]:
        print("IN VALIDATE MESSAGE :- ", value)
        return {"message": value}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:

        """
            This function retrieves slots information and performs the next step
            :param: dispatcher: CollectingDispatcher
            :param: tracker: Tracker
            :param: domain: Dict[Text, Any]
            :return: AllslotReset(), FollowupAction('action_live_agent')
            """
        email = tracker.get_slot("email")
        phone_number = tracker.get_slot("phone_number")
        message = tracker.get_slot("message")

        dispatcher.utter_message(f"Received these details:- \n{email}\n{phone_number}\n{message}\n")
        return [FollowupAction("action_get_doctor")]


class ActionGetDoctor(Action):
    def name(self) -> Text:
        return "action_get_doctor"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        email = tracker.get_slot("email")
        phone_number = tracker.get_slot("phone_number")
        message = tracker.get_slot("message")

        driver.get('https://www.lybrate.com/lp/questions/ask')
        counter = 0
        while True:
            try:
                if "Get brief answers" in driver.find_element_by_tag_name('h1').text:
                    break
            except Exception as e:
                pass
            time.sleep(1)
            if counter > 10:
                dispatcher.utter_message(text="Server down. Please try again later.")
                return [FollowupAction("action_hello_world")]
            counter += 1
        time.sleep(1)
        text_box = driver.find_element_by_id('askMessage')
        text_box.click()
        text_box.clear()
        text_box.send_keys(message)
        time.sleep(1)
        driver.find_element_by_xpath('//span[@class="lybPad-right"]').click()
        mail = driver.find_element_by_name('email')
        mail.click()
        mail.clear()
        mail.send_keys(email)
        time.sleep(1)
        phone = driver.find_element_by_name('phone')
        phone.click()
        phone.clear()
        phone.send_keys(phone_number)
        driver.find_element_by_id('submitQuestion').click()
        time.sleep(2)

        dispatcher.utter_message("\n\nThank You so much for these details. Now you will receive an OTP.")
        return []


class FormDistrict(FormAction):

    def name(self) -> Text:
        return "form_district"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill
           :param: tracker: Tracker
           :return: List[Text]
        """
        return ["district"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """
            This function maps the slot values
            :return: Dict[Text, Union[Dict, List[Dict]]]
        """
        return {
            "district": self.from_text(not_intent=["chitchat"]),
        }

    def validate_district(self,
                          value: Text,
                          dispatcher: CollectingDispatcher,
                          tracker: Tracker,
                          domain: Dict[Text, Any],
                          ) -> Dict[Text, Any]:

        District = ["ARARIA", "ARWAL", "AURANGABAD", "BANKA", "BEGUSARAI", "BHAGALPUR", "BHOJPUR", "BUXAR", "DARBHANGA",
                    "EAST CHAMPARAN", "GAYA", "GOPALGANJ", "JAMUI", "JEHANABAD", "KAIMUR", "KATIHAR", "KHAGARIA",
                    "KISHANGANJ", "LAKHISARAI", "MADHEPURA", "MADHUBANI", "MUNGER", "MUZAFFARPUR", "NALANDA", "NAWADA",
                    "PATNA", "PURNIA", "ROHTAS", "SAHARSA", "SAMASTIPUR", "SARAN", "SHEIKHPURA", "SHEOHAR", "SITAMARHI",
                    "SIWAN", "SUPAUL", "VAISHALI", "WEST CHAMPARAN"]

        if value.upper() in District:
            return {"district": District[District.index(value.upper())]}
        elif value.upper() not in District:
            for i in District:
                if value.upper() in i:
                    return {"district": i}
        return {"district": None}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:

        """
            This function retrieves slots information and performs the next step
            :param: dispatcher: CollectingDispatcher
            :param: tracker: Tracker
            :param: domain: Dict[Text, Any]
            :return: AllslotReset(), FollowupAction('action_live_agent')
            """
        district = tracker.get_slot("district")

        dispatcher.utter_message(f"Received these details:- \n{district}\n")
        return [FollowupAction("action_hospital_bed")]


class ActionFallback(Action):

    def name(self) -> Text:
        return "action_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # doc = nlp(tracker.latest_message["text"])
        #
        # noun = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "PROPN"]]
        # print("NOUN in FALLBACK ", noun)
        # # No noun found in user input
        # if len(noun) == 0:
        #     print("In IF Condition")
        #     text = "I am sorry, I couldn't help you with that.<br>Try something else!"
        #     # qr = QuickReply.QuickReply()
        #     # qr.add_postback(text=text, title="Start Again", payload="/action_restart")
        #     # message = qr.get_qr()
        #     # print("Message TYPE ",type(message), message)
        #     # dispatcher.utter_message(json_message=message)
        #     dispatcher.utter_message(text=text)
        #     return []
        # products = search(' '.join([str(elem) for elem in noun]))
        # print("PRODUCTS in FALLBACK ", products)
        # if not products:
        #     print("In IF NOT Condition")
            text = "I am sorry, I couldn't help you with that.<br>Try something else!"
            # qr = QuickReply.QuickReply()
            # qr.add_postback(text=text, title="Start Again", payload="/action_restart")
            # message = qr.get_qr()
            # dispatcher.utter_message(json_message=message)
            dispatcher.utter_message(text=text)

            # return []

            return [FollowupAction('action_menu')]


class ActionMapRedirect1(Action):
    def name(self) -> Text:
        return "action_map_redirect_1"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[0]
            values = list(medical_shop_info["OXYGEN"].values())[0]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[0]
            values = list(medical_shop_info["AMBULANCE"].values())[0]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[0]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[0]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[0]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[0]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect2(Action):
    def name(self) -> Text:
        return "action_map_redirect_2"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[1]
            values = list(medical_shop_info["OXYGEN"].values())[1]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[1]
            values = list(medical_shop_info["AMBULANCE"].values())[1]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[1]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[1]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[1]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[1]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect3(Action):
    def name(self) -> Text:
        return "action_map_redirect_3"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[2]
            values = list(medical_shop_info["OXYGEN"].values())[2]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[2]
            values = list(medical_shop_info["AMBULANCE"].values())[2]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[2]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[2]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[2]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[2]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect4(Action):
    def name(self) -> Text:
        return "action_map_redirect_4"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[3]
            values = list(medical_shop_info["OXYGEN"].values())[3]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[3]
            values = list(medical_shop_info["AMBULANCE"].values())[3]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[3]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[3]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[3]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[3]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass
            buttons = [{"title": "Menu", "payload": "/action_menu"}, ]

        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect5(Action):
    def name(self) -> Text:
        return "action_map_redirect_5"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[4]
            values = list(medical_shop_info["OXYGEN"].values())[4]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[4]
            values = list(medical_shop_info["AMBULANCE"].values())[4]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[4]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[4]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[4]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[4]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        buttons = [{"title": "Menu", "payload": "/action_menu"}, ]
        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect6(Action):
    def name(self) -> Text:
        return "action_map_redirect_6"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[5]
            values = list(medical_shop_info["OXYGEN"].values())[5]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[5]
            values = list(medical_shop_info["AMBULANCE"].values())[5]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[5]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[5]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[5]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[5]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        buttons = [{"title": "Menu", "payload": "/action_menu"}, ]
        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect7(Action):
    def name(self) -> Text:
        return "action_map_redirect_7"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[6]
            values = list(medical_shop_info["OXYGEN"].values())[6]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[6]
            values = list(medical_shop_info["AMBULANCE"].values())[6]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[6]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[6]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[6]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[6]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        buttons = [{"title": "Menu", "payload": "/action_menu"}, ]
        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect8(Action):
    def name(self) -> Text:
        return "action_map_redirect_8"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[7]
            values = list(medical_shop_info["OXYGEN"].values())[7]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[7]
            values = list(medical_shop_info["AMBULANCE"].values())[7]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[7]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[7]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[7]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[7]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        buttons = [{"title": "Menu", "payload": "/action_menu"}, ]
        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect9(Action):
    def name(self) -> Text:
        return "action_map_redirect_9"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[8]
            values = list(medical_shop_info["OXYGEN"].values())[8]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[8]
            values = list(medical_shop_info["AMBULANCE"].values())[8]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[8]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[8]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[8]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[8]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        buttons = [{"title": "Menu", "payload": "/action_menu"}, ]
        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect10(Action):
    def name(self) -> Text:
        return "action_map_redirect_10"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "\nPlease click on the above link to view it on map 🌍.\n"
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[9]
            values = list(medical_shop_info["OXYGEN"].values())[9]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[9]
            values = list(medical_shop_info["AMBULANCE"].values())[9]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[9]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[9]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[9]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[9]
            try:
                dispatcher.utter_message(f"{keys} \n Additional Info :- {values[1]} \n")
            except:
                pass
            try:
                dispatcher.utter_message(f"Website :- {values[0]} \n")
            except:
                pass

        buttons = [{"title": "Menu", "payload": "/action_menu"}, ]
        dispatcher.utter_button_message(text, buttons)

        return []


class ActionMapRedirect11(Action):
    def name(self) -> Text:
        return "action_map_redirect_11"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[10]
            values = list(medical_shop_info["OXYGEN"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[10]
            values = list(medical_shop_info["AMBULANCE"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[10]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[10]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect12(Action):
    def name(self) -> Text:
        return "action_map_redirect_12"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[11]
            values = list(medical_shop_info["OXYGEN"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[11]
            values = list(medical_shop_info["AMBULANCE"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[11]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[11]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect13(Action):
    def name(self) -> Text:
        return "action_map_redirect_13"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[12]
            values = list(medical_shop_info["OXYGEN"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[12]
            values = list(medical_shop_info["AMBULANCE"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[12]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[12]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect14(Action):
    def name(self) -> Text:
        return "action_map_redirect_14"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[13]
            values = list(medical_shop_info["OXYGEN"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[13]
            values = list(medical_shop_info["AMBULANCE"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[13]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[13]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect15(Action):
    def name(self) -> Text:
        return "action_map_redirect_15"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[14]
            values = list(medical_shop_info["OXYGEN"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[14]
            values = list(medical_shop_info["AMBULANCE"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[14]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[14]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect16(Action):
    def name(self) -> Text:
        return "action_map_redirect_16"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[15]
            values = list(medical_shop_info["OXYGEN"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[15]
            values = list(medical_shop_info["AMBULANCE"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[15]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[15]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect17(Action):
    def name(self) -> Text:
        return "action_map_redirect_17"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[16]
            values = list(medical_shop_info["OXYGEN"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[16]
            values = list(medical_shop_info["AMBULANCE"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[16]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[16]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect18(Action):
    def name(self) -> Text:
        return "action_map_redirect_18"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[17]
            values = list(medical_shop_info["OXYGEN"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[17]
            values = list(medical_shop_info["AMBULANCE"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[17]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[17]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect19(Action):
    def name(self) -> Text:
        return "action_map_redirect_19"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[18]
            values = list(medical_shop_info["OXYGEN"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[18]
            values = list(medical_shop_info["AMBULANCE"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[18]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[18]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect20(Action):
    def name(self) -> Text:
        return "action_map_redirect_20"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[19]
            values = list(medical_shop_info["OXYGEN"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[19]
            values = list(medical_shop_info["AMBULANCE"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[19]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[19]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # qr = QuickReply.QuickReply()
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False,
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMedicalStore(Action):

    def name(self) -> Text:
        return "action_medicine_store"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        print("LATEST ACTION ", latest_action["ACTION"])
        if len(medical_shop_info["MEDICAL_STORE"]) == 0:

            msg = 'Let me check for nearby medical stores. 😎'
            dispatcher.utter_message(text=msg)

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Medical Stores near me")
            driver.find_element_by_id('searchbox-searchbutton').click()
            time.sleep(3)

            barCounter = 0
            while True:
                try:
                    bar = driver.find_element_by_xpath(
                        '/html/body/div[3]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]')
                    break
                except Exception as e:
                    print("Finding Scroll Bar")

                if barCounter > 200:
                    break
                barCounter += 1

            scroll = 0
            while scroll < 100:
                try:
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                    scroll += 1
                except Exception as e:
                    break

            for i in driver.find_elements_by_class_name('hfpxzc'):
                medical_dic[i.get_attribute('aria-label')] = [i.get_attribute('href')]

            for i in driver.find_elements_by_class_name("lI9IFe"):
                if i.text.split("\n")[0] in medical_dic:
                    medical_dic[i.text.split("\n")[0]].append(
                        i.text.replace("Directions", "").replace("Website", "").replace(i.text.split("\n")[0], ''))

            print("MEDICAL DICTIONARY ", medical_dic)
            medical_shop_info["MEDICAL_STORE"] = medical_dic

        text = "Here are the search results :- \n\n"

        buttons = [{"title": list(medical_dic.keys())[0], "payload": "/action_map_redirect_1"},
                   {"title": list(medical_dic.keys())[1], "payload": "/action_map_redirect_2"},
                   {"title": list(medical_dic.keys())[2], "payload": "/action_map_redirect_3"},
                   {"title": list(medical_dic.keys())[3], "payload": "/action_map_redirect_4"},
                   {"title": list(medical_dic.keys())[4], "payload": "/action_map_redirect_5"},
                   {"title": list(medical_dic.keys())[5], "payload": "/action_map_redirect_6"},
                   {"title": list(medical_dic.keys())[6], "payload": "/action_map_redirect_7"},
                   {"title": list(medical_dic.keys())[7], "payload": "/action_map_redirect_8"},
                   {"title": list(medical_dic.keys())[8], "payload": "/action_map_redirect_9"},
                   {"title": list(medical_dic.keys())[9], "payload": "/action_map_redirect_10"},
                   {"title": "Menu", "payload": "/action_menu"},
                   ]
        dispatcher.utter_button_message(text, buttons)

        # dispatcher.utter_message(text=text)
        return []


class ActionOxygen(Action):

    def name(self) -> Text:
        medical_shop_info = {}
        return "action_oxygen"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        if len(medical_shop_info["OXYGEN"]) == 0:

            msg = 'Let me see 👓 ....oxygen containers availability. '
            dispatcher.utter_message(text=msg)

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Oxygen Gas near me")
            driver.find_element_by_id('searchbox-searchbutton').click()
            time.sleep(3)

            barCounter = 0
            while True:
                try:
                    bar = driver.find_element_by_xpath(
                        '/html/body/div[3]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]')
                    break
                except Exception as e:
                    print("Finding Scroll Bar")

                if barCounter > 200:
                    break
                barCounter += 1

            scroll = 0
            while scroll < 100:
                try:
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                    scroll += 1
                except Exception as e:
                    break

            for i in driver.find_elements_by_class_name('hfpxzc'):
                oxygen_dic[i.get_attribute('aria-label')] = [i.get_attribute('href')]

            for i in driver.find_elements_by_class_name("lI9IFe"):
                if i.text.split("\n")[0] in medical_dic:
                    oxygen_dic[i.text.split("\n")[0]].append(
                        i.text.replace("Directions", "").replace("Website", "").replace(i.text.split("\n")[0], ''))

            print("OXYGEN DICTIONARY ", oxygen_dic)
            medical_shop_info["OXYGEN"] = oxygen_dic

        text = "Here are the search results :-\n\n"
        buttons = [{"title": list(oxygen_dic.keys())[0], "payload": "/action_map_redirect_1"},
                   {"title": list(oxygen_dic.keys())[1], "payload": "/action_map_redirect_2"},
                   {"title": list(oxygen_dic.keys())[2], "payload": "/action_map_redirect_3"},
                   {"title": list(oxygen_dic.keys())[3], "payload": "/action_map_redirect_4"},
                   {"title": list(oxygen_dic.keys())[4], "payload": "/action_map_redirect_5"},
                   {"title": list(oxygen_dic.keys())[5], "payload": "/action_map_redirect_6"},
                   {"title": list(oxygen_dic.keys())[6], "payload": "/action_map_redirect_7"},
                   {"title": list(oxygen_dic.keys())[7], "payload": "/action_map_redirect_8"},
                   {"title": list(oxygen_dic.keys())[8], "payload": "/action_map_redirect_9"},
                   {"title": list(oxygen_dic.keys())[9], "payload": "/action_map_redirect_10"},
                   {"title": "Menu", "payload": "/action_menu"},
                   ]
        dispatcher.utter_button_message(text, buttons)
        return []


class ActionRestart(Action):

    def name(self) -> Text:
        return "action_restart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Conversation Restarted !")

        return [Restarted(), FollowupAction('action_hello_world')]


class ActionAmbulance(Action):

    def name(self) -> Text:
        medical_shop_info = {}
        return "action_ambulance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        print("LATEST ACTION ", latest_action["ACTION"])
        if len(medical_shop_info["AMBULANCE"]) == 0:

            msg = 'Let me check any ambulances 🚑 service is available or not. '
            dispatcher.utter_message(text=msg)

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Ambulance Service near me")
            driver.find_element_by_id('searchbox-searchbutton').click()
            time.sleep(3)

            barCounter = 0
            while True:
                try:
                    bar = driver.find_element_by_xpath(
                        '/html/body/div[3]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]')
                    break
                except Exception as e:
                    print("Finding Scroll Bar")

                if barCounter > 200:
                    break
                barCounter += 1

            scroll = 0
            while scroll < 100:
                try:
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                    scroll += 1
                except Exception as e:
                    break

            for i in driver.find_elements_by_class_name('hfpxzc'):
                ambulance_dic[i.get_attribute('aria-label')] = [i.get_attribute('href')]

            for i in driver.find_elements_by_class_name("lI9IFe"):
                if i.text.split("\n")[0] in medical_dic:
                    ambulance_dic[i.text.split("\n")[0]].append(
                        i.text.replace("Directions", "").replace("Website", "").replace(i.text.split("\n")[0], ''))

            print("AMBULANCE DICTIONARY ", ambulance_dic)
            medical_shop_info["AMBULANCE"] = ambulance_dic

        text = "Here are the search results :-\n\n"
        buttons = [{"title": list(ambulance_dic.keys())[0], "payload": "/action_map_redirect_1"},
                   {"title": list(ambulance_dic.keys())[1], "payload": "/action_map_redirect_2"},
                   {"title": list(ambulance_dic.keys())[2], "payload": "/action_map_redirect_3"},
                   {"title": list(ambulance_dic.keys())[3], "payload": "/action_map_redirect_4"},
                   {"title": list(ambulance_dic.keys())[4], "payload": "/action_map_redirect_5"},
                   {"title": list(ambulance_dic.keys())[5], "payload": "/action_map_redirect_6"},
                   {"title": list(ambulance_dic.keys())[6], "payload": "/action_map_redirect_7"},
                   {"title": list(ambulance_dic.keys())[7], "payload": "/action_map_redirect_8"},
                   {"title": list(ambulance_dic.keys())[8], "payload": "/action_map_redirect_9"},
                   {"title": list(ambulance_dic.keys())[9], "payload": "/action_map_redirect_10"},
                   {"title": "Menu", "payload": "/action_menu"},
                   ]
        dispatcher.utter_button_message(text, buttons)
        return []


class ActionHospitalBed(Action):
    def name(self) -> Text:
        return "action_hospital_bed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = "Please select the bed category:-"
        quick_reply_buttons = [
            {
                "action_type": "postback",
                "title": "ICU Bed",
                "payload": "/action_icu_bed"
            },
            {
                "action_type": "postback",
                "title": "General Bed",
                "payload": "/action_general_bed"
            },
        ]
        # dispatcher.utter_message(
        #     json_message=create_quick_replies(tracker.get_latest_input_channel(), text, quick_reply_buttons))

        return []


class ActionIcuBed(Action):
    def name(self) -> Text:
        return "action_icu_bed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        df = pd.read_html("https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied")
        df = df[0]
        hospital_detail = {}
        query = tracker.get_slot("district")
        for i in range(df.shape[0]):
            if df["District"][i] == query:
                hospital_detail[df["Facility Name"][i]] = [
                    df["Total ICU Beds"][i], df["ICU Beds Vacant"][i],
                    df["Contact"][i], df["Last Updated"][i]
                ]

        text = "ICU bed information in selected district"
        dispatcher.utter_message(text=text)
        # cr = Carousel.Carousel()
        # category = []
        # for i in hospital_detail:
        #     category.append((
        #                     f"{i}:-<br>Total ICU Bed->{hospital_detail[i][0]}<br>Vacant->{hospital_detail[i][1]}<br>Contact-{hospital_detail[i][2]}<br>Last Updated->{hospital_detail[i][3]}",
        #                     "https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied"))
        #
        # images = ["https://cdn.apollohospitals.com/dev-apollohospitals/2021/04/apolloprism-6076b56144ba8.jpg"] * len(
        #     category)
        #
        # for i in range(len(category)):
        #     cr.add_element(
        #         title=category[i][0],
        #         image_url=images[i],
        #         buttons=[{
        #             "type": "web_url",
        #             "url": category[i][1],
        #             "title": "Show"
        #         }]
        #     )
        #
        # dispatcher.utter_message(json_message=cr.get_message())
        # # Show menu after products
        # text = "What else i can help you with? "
        # menu = [
        #     ("Menu", "postback", "/action_menu"),
        #     ("Ambulance Services 🚑", "postback", "/action_ambulance"),
        # ]
        # qr = QuickReply.QuickReply(text=text)
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionGeneralBed(Action):
    def name(self) -> Text:
        return "action_general_bed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        df = pd.read_html("https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied")
        df = df[0]
        hospital_detail = {}
        query = tracker.get_slot("district")
        for i in range(df.shape[0]):
            if df["District"][i] == query:
                hospital_detail[df["Facility Name"][i]] = [
                    df["Total Beds"][i], df["Vacant"][i],
                    df["Contact"][i], df["Last Updated"][i]
                ]

        text = "General bed information in selected district"
        dispatcher.utter_message(text=text)
        # cr = Carousel.Carousel()
        # category = []
        # for i in hospital_detail:
        #     category.append((
        #                     f"{i}:-<br>Total General Bed->{hospital_detail[i][0]}<br>Vacant->{hospital_detail[i][1]}<br>Contact-{hospital_detail[i][2]}<br>Last Updated->{hospital_detail[i][3]}",
        #                     "https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied"))
        #
        # images = ["https://images-na.ssl-images-amazon.com/images/I/61aU0ZCFTqL._AC_SX355_.jpg"] * len(category)
        #
        # for i in range(len(category)):
        #     cr.add_element(
        #         title=category[i][0],
        #         image_url=images[i],
        #         buttons=[{
        #             "type": "web_url",
        #             "url": category[i][1],
        #             "title": "Show"
        #         }]
        #     )
        #
        # dispatcher.utter_message(json_message=cr.get_message())
        # # Show menu after products
        # text = "What else i can help you with? "
        # menu = [
        #     ("Menu", "postback", "/action_menu"),
        #     ("Ambulance Services 🚑", "postback", "/action_ambulance"),
        # ]
        # qr = QuickReply.QuickReply(text=text)
        # for item in menu:
        #     if item[1] == "postback":
        #         qr.add_generic_(
        #             type="postback",
        #             text=text,
        #             title=item[0],
        #             payload=item[2]
        #         )
        #     else:
        #         qr.add_generic_(
        #             type="web_url",
        #             text=text,
        #             title=item[0],
        #             web_url=item[2],
        #             extension=False
        #         )
        # dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionContactHospital(Action):
    def name(self) -> Text:
        return "action_contact_hospital"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        print("LATEST ACTION ", latest_action["ACTION"])
        if len(medical_shop_info["CONTACT_HOSPITAL"]) == 0:

            msg = 'Let me search for nearby Hospitals  🏥. '
            dispatcher.utter_message(text=msg)

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Hospitals near me")
            driver.find_element_by_id('searchbox-searchbutton').click()
            time.sleep(3)

            barCounter = 0
            while True:
                try:
                    bar = driver.find_element_by_xpath(
                        '/html/body/div[3]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]')
                    break
                except Exception as e:
                    print("Finding Scroll Bar")

                if barCounter > 200:
                    break
                barCounter += 1

            scroll = 0
            while scroll < 100:
                try:
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                    scroll += 1
                except Exception as e:
                    break

            for i in driver.find_elements_by_class_name('hfpxzc'):
                hospital_dic[i.get_attribute('aria-label')] = [i.get_attribute('href')]

            for i in driver.find_elements_by_class_name("lI9IFe"):
                if i.text.split("\n")[0] in hospital_dic:
                    hospital_dic[i.text.split("\n")[0]].append(
                        i.text.replace("Directions", "").replace("Website", "").replace(i.text.split("\n")[0], ''))

            print("HOSPITAL DICTIONARY ", hospital_dic)
            medical_shop_info["CONTACT_HOSPITAL"] = hospital_dic

        text = "Here are the search results :-\n\n"
        buttons = [{"title": list(hospital_dic.keys())[0], "payload": "/action_map_redirect_1"},
                   {"title": list(hospital_dic.keys())[1], "payload": "/action_map_redirect_2"},
                   {"title": list(hospital_dic.keys())[2], "payload": "/action_map_redirect_3"},
                   {"title": list(hospital_dic.keys())[3], "payload": "/action_map_redirect_4"},
                   {"title": list(hospital_dic.keys())[4], "payload": "/action_map_redirect_5"},
                   {"title": list(hospital_dic.keys())[5], "payload": "/action_map_redirect_6"},
                   {"title": list(hospital_dic.keys())[6], "payload": "/action_map_redirect_7"},
                   {"title": list(hospital_dic.keys())[7], "payload": "/action_map_redirect_8"},
                   {"title": list(hospital_dic.keys())[8], "payload": "/action_map_redirect_9"},
                   {"title": list(hospital_dic.keys())[9], "payload": "/action_map_redirect_10"},
                   {"title": "Menu", "payload": "/action_menu"},
                   ]
        dispatcher.utter_button_message(text, buttons)
        return []


class ActionPreventiveMedicines(Action):
    def name(self) -> Text:
        return "action_preventive_medicines"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = "The FDA has issued an EUA for tixagevimab plus cilgavimab (Evusheld), a medicine used in adults and children ages 12 years and older. Evusheld consists of 2 monoclonal antibodies provided together to help prevent infection with the virus that causes COVID-19."
        # dispatcher.utter_message(text=text)

        msg = {"type": "video", "payload": {"title": "Medicine for COVID-19 prevention",
                                            "src": "https://www.youtube.com/embed/TE0nH1u9kXo"}}
        dispatcher.utter_message(text=text, attachment=msg)
        return [FollowupAction("utter_menu")]


class ActionAskDoctor(Action):
    def name(self) -> Text:
        return "action_ask_doctor"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = "Before getting in touch with doc you will need to provide us some information.\n"

        dispatcher.utter_message(text=text)

        return [FollowupAction("form_ask_doctor")]
