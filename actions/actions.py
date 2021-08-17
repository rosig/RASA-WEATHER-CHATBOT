# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
import json
from pathlib import Path
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import spacy
import random
import requests
import re

class GetWeatherActionCheckEntities(Action):
    gpe = None
    date = None
    time = None

    def name(self) -> Text:
      return "action_check_weather_entities"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
      print("🐍 [RUN][action_check_weather_entities]")

      self.gpe = None
      self.date = None
      self.time = None

      entities = tracker.latest_message['entities']
      textInput = tracker.latest_message['text']

      print(textInput)
      textInput = textInput.lower()

      # Special cases need to be done before
      # if slot_value.contains('now')  
    
      if len(entities) > 0:
        for entity in entities:
          
          entityType = entity['entity']
          entityValue = entity['value']

          if entityType == 'GPE':
            self.gpe = entityValue
          elif entityType == 'DATE':
            self.date = entityValue
          elif entityType == 'TIME':
            self.time = entityValue

    #se o extrator ainda assim nao pegou(verifica variavel se estao com none)
      if ' this' in textInput and self.date == None:
        self.date = "today"
      if ' tomorrow' in textInput or 'tomorrow ' in textInput and self.date == None:
        self.date = "tomorrow"
      if ' tonight' in textInput or 'tonight ' in textInput and self.time == None and self.date == None:
        self.date = "today"
        self.time = "evening"
      if ' night' in textInput or 'night ' in textInput and self.time == None: #pode ser a noite de outro dia...
        self.time = "evening"
      if ' night' in textInput or 'night ' in textInput and self.time == None and self.date == None: #senao achei nem o dia, assuma q é hoje
        self.date = "today"
        self.time = "evening"
      if ' now' in textInput or ' now' in textInput and self.time == None and self.date == None :  
        #deixar com espaco pois tem now e know... que pode dá pau
        self.date = "today"
        self.time = "afternoon" # forca aqui ser a tarde
        # o ideal seria ter um outro tipo de utter_response somente com date e where. Pois na frase nao tem time... mas podemos supor que sempre que nao vier será a tarde...

      if self.date != None and self.time != None:
        if self.date in self.time:
          self.time = self.time.replace(self.date, "")


      print("🚨 LOCAL:", self.gpe, "DATA:", self.date, "HORÁRIO:", self.time)
      return[SlotSet("where_info", self.gpe), SlotSet("when_info", self.date), SlotSet("time_info", self.time)]

class ValidateWeatherForm(FormValidationAction):
    temp_info = ''
    temp_feels_like = ''

    def name(self) -> Text:
        return "validate_get_weather_form"

    def requestAPI(self, placeName):
      api_url = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&APPID=5cf0a118ed3fb5b03ff1ee5227cf0b4f".format(placeName)
        
      try:
        data = requests.get(api_url).json()
      except requests.exceptions.RequestException as e:  # This is the correct syntax
        dispatcher.utter_message(text=f"API Error 😰")

      return data

    def validate_where_info(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("[RUN][validate_where_info]")

        data = self.requestAPI(slot_value)

        if data.get('message') and data['cod'] == '404': #place not found
          print(0)
          placeEntityValue = None

          print("tokeziner where")
          nlp = spacy.load('en_core_web_sm')
          doc = nlp(slot_value)

          for entity in doc.ents:
            if entity.label_ == 'GPE':
              print("achou GPE")
              print(entity.text, entity.label_)
              placeEntityValue = entity.text

          if placeEntityValue != None:
            data = self.requestAPI(placeEntityValue)
            
            if data.get('message') and data['cod'] == '404':
              print(1)
              dispatcher.utter_message(text=f"I couldn't find the place you wrote. 🙄")
              return {"where_info": None}

            self.temp_info = data['main']['temp']
            self.temp_feels_like = data['main']['feels_like']
            return {"where_info": placeEntityValue}
          
          print(2)
          dispatcher.utter_message(text=f"I couldn't find the place you wrote. 🙄")
          return {"where_info": None}
        else:
          self.temp_info = data['main']['temp']
          self.temp_feels_like = data['main']['feels_like']
          return {"where_info": slot_value}
       
    def validate_when_info(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("[RUN][validate_when_info]")

        dateEntityValue = None

        slot_value = "Hum, " + slot_value
        print("tokeziner when")
        print(slot_value)
        print(type(slot_value))

        slot_value.lower()


        nlp = spacy.load('en_core_web_sm')
        doc = nlp(slot_value)

        for entity in doc.ents:
          if entity.label_ == 'DATE':
            dateEntityValue = entity.text

        if dateEntityValue == None:
          if 'current' in slot_value or ' current' in slot_value or 'current ' in slot_value or ' current ' in slot_value:
            dateEntityValue = 'current'
          if 'today' in slot_value or ' today' in slot_value or 'today ' in slot_value or ' today ' in slot_value:
            dateEntityValue = 'today'
          if 'now' in slot_value or ' now' in slot_value or 'now ' in slot_value or ' now ' in slot_value:
            dateEntityValue = 'now'
          if 'right now' in slot_value or ' right now' in slot_value or 'right now ' in slot_value or ' right now ' in slot_value:
            dateEntityValue = 'right now'
          if 'present' in slot_value or ' present' in slot_value or ' present ' in slot_value or ' present ' in slot_value:
            dateEntityValue = 'present'
          if 'present moment' in slot_value or ' present moment' in slot_value or 'present moment ' in slot_value or ' present moment ' in slot_value:
            dateEntityValue = 'present moment'
        
         

        if dateEntityValue != None:
          return {"when_info": dateEntityValue, "temp_info": "is {}°C, with feels like of {}ºC".format(self.temp_info, self.temp_feels_like)} 
        else:
          dispatcher.utter_message(text=f"I didn't understand what you said 1 😰")
          return {"when_info": None}
    
    
    def validate_time_info(  
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("[RUN][validate_time_info]")

        timeEntityValue = None

        nlp = spacy.load('en_core_web_sm')
        doc = nlp(slot_value)

        for entity in doc.ents:
          if entity.label_ == 'TIME':
            timeEntityValue = entity.text

        if timeEntityValue != None:
          return {"time_info": timeEntityValue} 
        else:
          dispatcher.utter_message(text=f"I didn't understand what you said 2 😰")
          return {"time_info": None}

class SetWeatherAlertActionCheckEntities(Action):
    def name(self) -> Text:
      return "action_check_alert_weather_entities"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
      print("🐍 [RUN][action_check_alert_weather_entities]")

      self.gpe = None
      self.date = None
      self.time = None

      entities = tracker.latest_message['entities']
      textInput = tracker.latest_message['text']

      print(textInput)
      textInput = textInput.lower()

      # Special cases need to be done before
      # if slot_value.contains('now')  
    
      if len(entities) > 0:
        for entity in entities:
          
          entityType = entity['entity']
          entityValue = entity['value']

          if entityType == 'GPE':
            self.gpe = entityValue
          elif entityType == 'DATE':
            self.date = entityValue
          elif entityType == 'TIME':
            self.time = entityValue

    #se o extrator ainda assim nao pegou(verifica variavel se estao com none)
      if ' this' in textInput and self.date == None:
        self.date = "today"
      if ' tomorrow' in textInput or 'tomorrow ' in textInput and self.date == None:
        self.date = "tomorrow"
      if ' tonight' in textInput or 'tonight ' in textInput and self.time == None and self.date == None:
        self.date = "today"
        self.time = "evening"
      if ' night' in textInput or 'night ' in textInput and self.time == None: #pode ser a noite de outro dia...
        self.time = "evening"
      if ' night' in textInput or 'night ' in textInput and self.time == None and self.date == None: #senao achei nem o dia, assuma q é hoje
        self.date = "today"
        self.time = "evening"
      if ' now' in textInput or ' now' in textInput and self.time == None and self.date == None :  
        #deixar com espaco pois tem now e know... que pode dá pau
        self.date = "today"
        self.time = "afternoon" # forca aqui ser a tarde
        # o ideal seria ter um outro tipo de utter_response somente com date e where. Pois na frase nao tem time... mas podemos supor que sempre que nao vier será a tarde...

      if self.date != None and self.time != None:
        if self.date in self.time:
          self.time = self.time.replace(self.date, "")

      print("🚨 LOCAL:", self.gpe, "DATA:", self.gpe, "HORÁRIO:", self.gpe)
      return[SlotSet("place_alert", self.gpe), SlotSet("date_alert", self.gpe), SlotSet("time_day_alert", self.gpe)]

class ValidateSetAlertWeatherForm(FormValidationAction):
    # places = Path("data/locations.txt").read_text().split("\n")
    place_alert = ''
    date_alert = ''
    time_day_alert = ''

    def name(self) -> Text:
        return "validate_set_weather_alert_form"

  def requestAPI(self, placeName):
        api_url = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&APPID=5cf0a118ed3fb5b03ff1ee5227cf0b4f".format(placeName)
          
        try:
          data = requests.get(api_url).json()
        except requests.exceptions.RequestException as e:  # This is the correct syntax
          dispatcher.utter_message(text=f"API Error 😰")

        return data

    def validate_place_alert(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("[RUN][validate_place_alert]")
        data = self.requestAPI(slot_value)

        if data.get('message') and data['cod'] == '404': #place not found
          print(0)
          placeEntityValue = None

          print("tokeziner where")
          nlp = spacy.load('en_core_web_sm')
          doc = nlp(slot_value)

          for entity in doc.ents:
            if entity.label_ == 'GPE':
              print("achou GPE")
              print(entity.text, entity.label_)
              placeEntityValue = entity.text

          if placeEntityValue != None:
            data = self.requestAPI(placeEntityValue)
            
            if data.get('message') and data['cod'] == '404':
              print(1)
              dispatcher.utter_message(text=f"I couldn't find the place you wrote. 🙄")
              return {"place_alert": None}

            self.temp_info = data['main']['temp']
            self.temp_feels_like = data['main']['feels_like']
            return {"place_alert": placeEntityValue}
          
          print(2)
          dispatcher.utter_message(text=f"I couldn't find the place you wrote. 🙄")
          return {"place_alert": None}
        else:
          self.temp_info = data['main']['temp']
          self.temp_feels_like = data['main']['feels_like']
          return {"place_alert": slot_value}

    def validate_date_alert(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("[RUN][validate_date_alert]")

        dateEntityValue = None

        nlp = spacy.load('en_core_web_sm')
        doc = nlp(slot_value)

        for entity in doc.ents:
          if entity.label_ == 'DATE':
            dateEntityValue = entity.text

        if dateEntityValue != None:
          self.date_alert = dateEntityValue
          return {"date_alert": dateEntityValue}
        else:
          dispatcher.utter_message(text=f"I didn't understand what you said 3😰")
          return {"date_alert": None}

        # matched = re.match("^[0-3]?[0-9]/[0-3]?[0-9]/(?:[0-9]{2})?[0-9]{2}$", slot_value)
        # if bool(matched):
        #   self.date_alert = slot_value
        #   return {"date_alert": slot_value}
        # else:
        #   dispatcher.utter_message(text=f"Invalid date format 🚨")
        #   return {"date_alert": None}

    def validate_time_day_alert(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("[RUN][validate_time_day_alert]")

        timeEntityValue = None

        nlp = spacy.load('en_core_web_sm')
        doc = nlp(slot_value)

        for entity in doc.ents:
          if entity.label_ == 'TIME':
            timeEntityValue = entity.text

        if timeEntityValue != None:
          self.time_day_alert = timeEntityValue
          return {"time_day_alert": timeEntityValue} 
        else:
          dispatcher.utter_message(text=f"I didn't understand what you said 4 😰")
          return {"time_day_alert": None}

        # matched = re.match(r'^(([01]\d|2[0-3]):([0-5]\d)|24:00)$', slot_value)
        # if bool(matched):
        #   self.time_day_alert = slot_value
        #   return {"time_day_alert": slot_value}
        # else:
        #   dispatcher.utter_message(text=f"Invalid time format 🚨")
        #   return {"time_day_alert": None}

