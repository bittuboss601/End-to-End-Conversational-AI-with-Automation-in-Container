## happy path
* greet
  - action_hello_world
  - utter_greet
  
## say goodbye
* goodbye
  - utter_goodbye
  
## thank you
* affirm
  - utter_affirm
  
## deny
* deny
  - utter_deny
  
## mood happy
* mood_great
  - utter_mood_great
  
## mood sad
* mood_unhappy
  - utter_mood_unhappy

## bot challenge
* bot_challenge
  - utter_iamabot
  
## chitchat
* chitchat
    - respond_chitchat
  
## start_form
* start_form
  - utter_start_form
  - form_contact_us
  
## greet + contact_us form 
* greet
  - action_hello_world
* start_form
  - utter_start_form
  - form_contact_us
  
## greet + contact_us form + chitchat
* greet
  - action_hello_world
* start_form
  - utter_start_form
  - form_contact_us
* chitchat
  - respond_chitchat
  - form_contact_us
  - form{"name": "form_contact_us"}
* chitchat
  - respond_chitchat
  - form_contact_us
  - form{"name": "form_contact_us"}
  
## greet + form 
* greet
  - action_hello_world
* start_form
  - form_contact_us
  - form{"name":"form_contact_us"}
  
## greet + hello world + mecical store + 1
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_1
  - action_map_redirect_1
  
## greet + hello world + mecical store + 2
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_2
  - action_map_redirect_2
  
## greet + hello world + mecical store + 3
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_3
  - action_map_redirect_3
  
## greet + hello world + mecical store + 4
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_4
  - action_map_redirect_4
  
## greet + hello world + mecical store + 5
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_5
  - action_map_redirect_5
  
## greet + hello world + mecical store + 6
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_6
  - action_map_redirect_6
  
## greet + hello world + mecical store + 7
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_7
  - action_map_redirect_7
  
## greet + hello world + mecical store + 8
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_8
  - action_map_redirect_8
  
## greet + hello world + mecical store + 9
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_9
  - action_map_redirect_9
  
## greet + hello world + mecical store + 10
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_10
  - action_map_redirect_10
  
## greet + hello world + mecical store + 11
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_11
  - action_map_redirect_11
  
## greet + hello world + mecical store + 12
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_12
  - action_map_redirect_12
  
## greet + hello world + mecical store + 13
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_13
  - action_map_redirect_13
  
## greet + hello world + mecical store + 14
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_14
  - action_map_redirect_14
  
## greet + hello world + mecical store + 15
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_15
  - action_map_redirect_15
  
## greet + hello world + mecical store + 16
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_16
  - action_map_redirect_16
  
## greet + hello world + mecical store + 17
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_17
  - action_map_redirect_17
  
## greet + hello world + mecical store + 18
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_18
  - action_map_redirect_18
  
## greet + hello world + mecical store + 19
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_19
  - action_map_redirect_19
  
## greet + hello world + mecical store + 20
* greet
  - action_hello_world
* action_medicine_store
  - action_medicine_store
* action_map_redirect_20
  - action_map_redirect_20
  
## action medicine store 
* action_medicine_store
  - action_medicine_store

## greet + hello world + oxygen
* greet
  - action_hello_world
* action_oxygen
  - action_oxygen
  
## greet + hello world + preventive medicine
* greet
  - action_hello_world
* action_preventive_medicines
  - action_preventive_medicines
  
## greet + hello world + ambulance
* greet
  - action_hello_world
* action_ambulance
  - action_ambulance
  
## greet + hello world + contact hospital
* greet
  - action_hello_world
* action_contact_hospital
  - action_contact_hospital
  
## greet + hello world + support
* greet
  - action_hello_world
* action_support
  - action_support 
  
## action preventive medicine
* action_preventive_medicines
  - action_preventive_medicines

## action contact hospital
* action_contact_hospital
  - action_contact_hospital
  
## action ambulance
* action_ambulance
  - action_ambulance
  
## action oxygen
* action_oxygen
  - action_oxygen
  
## Menu
* action_menu
  - action_menu
  
## action support
* action_support
  - action_support
  
## greet + action_hospital_bed + action_icu_bed
* greet
  - action_hello_world
* start_district_form
  - utter_ask_district
  - form_district
* action_hospital_bed
  - action_hospital_bed
* action_icu_bed
  - action_icu_bed
  
## greet + action_hospital_bed + action_general_bed
* greet
  - action_hello_world
* start_district_form
  - utter_ask_district
  - form_district
* action_hospital_bed
  - action_hospital_bed
* action_general_bed
  - action_general_bed
  
## greet + hello world + ask doctor
* greet
  - action_hello_world
* action_ask_doctor
  - action_ask_doctor
  - form_ask_doctor
  - form{"name":"form_ask_doctor"}
* action_get_otp
  - action_get_otp
  - form_get_otp
  - form{"name":"form_get_otp"}
  
## ask doctor
* action_ask_doctor
  - action_ask_doctor
  - form_ask_doctor
  - form{"name":"form_ask_doctor"}
* action_get_otp
  - action_get_otp
  - form_get_otp
  - form{"name":"form_get_otp"}  
  
## greet + ask doctor form + chitchat
* greet
  - action_hello_world
* action_ask_doctor
  - action_ask_doctor
  - form_ask_doctor
* chitchat
  - respond_chitchat
  - form_ask_doctor
  - form{"name": "form_ask_doctor"}
* chitchat
  - respond_chitchat
  - form_ask_doctor
  - form{"name": "form_ask_doctor"}
* action_get_otp
  - action_get_otp
  - form_get_otp
  - form{"name":"form_get_otp"}  
* chitchat 
  - respond_chitchat
  - form_get_otp
  - form{"name":"form_get_otp"} 
  
## intent local medical stores
* local_medical_stores
  - action_medicine_store
  
## intent oxygen tank
* oxygen_tank
  - action_oxygen



