import json
import openai
from openai import OpenAI
from pytesseract import pytesseract
import io
from PIL import Image
import requests
from enum import Enum
import frappe

def get_openai_client():
    settings = frappe.get_single("DocVision Settings")
    base_url = settings.base_url
    api_key = settings.get_password("api_key")
    
    if not base_url:
        frappe.throw((
            "Base URL is not set in DocVision Settings"
            f"Please set the base URL in <a href='{settings.get_url()}'>DocVision Settings</a>"
        ))
    if not api_key:
        frappe.throw((
            "API Key is not set in DocVision Settings"
            f"Please set the API key in <a href='{settings.get_url()}'>DocVision Settings</a>"
        ))
    
    client = OpenAI(
        base_url=base_url,
        api_key=api_key, 
    )
    return client

def get_text_from_image(file_id):
    name = frappe.db.get("File", {"file_url": file_id}).name
    content = frappe.get_doc("File", name).get_content()
    img_io = io.BytesIO(content)
    img = Image.open(img_io)
    img = img.convert("L")  
    text = pytesseract.image_to_string(img)
    return text.strip()

# Define output schema for structured data
contact_schema = json.dumps(
{
    "first_name": "?",
    "last_name": "?",
    "middle_name": "?",
    "full_name": "?",
    "email_id": "?",
    "phone": "?",
    "mobile_no": "?",
    "gender": "<can you guess gender based on name>",
    "designation": "?",
    "salutation": "<can you guess salutation based on name>",
    "company_name": "?",
    "doctype": "Contact",
    "address": {
        "address_title": "full_name",
        "address_type": "Billing",
        "address_line1": "?",
        "city": "?",
        "state": "?",
        "country": "?",
        "pincode": "?",
        "doctype": "Address",
    },
    "email_ids": [
        {
            "email_id": "?",
            "is_primary": 1,
            "parentfield": "email_ids",
            "parenttype": "Contact",
            "doctype": "Contact Email",
        }
    ],
})

customer_schema = json.dumps(
    {
    "doctype": "Customer",
    "customer_name": "?",
    "customer_type": "Company",
    "email_address": "?",
    "mobile_number": "?",
    "address_line1": "?",
    "address_line2": "?",
    "city": "?",
    "state": "?",
    "country": "?",
    "pincode": "?"
})

supplier_schema = json.dumps({
  "doctype": "Supplier",
  "salutation": "<can you guess salutation based on name>",
  "first_name": "?",
  "middle_name": "?",
  "last_name": "?",
  "job_title": "?",
  "gender": "<can you guess salutation based on name>",
  "status": "Active",
  "email_id": "?",
  "website": "?",
  "mobile_no": "?",
  "phone": "?",
  "company_name": "?",
  "city": "?",
  "state": "?",
  "country": "?",
  "company": "?"
})

lead_schema = json.dumps({
  "doctype": "Supplier",
  "first_name": "?",
  "middle_name": "?",
  "last_name": "?",
  "job_title": "?",
  "status": "Lead",
  "source": "Reference",
  "salutation": "<can you guess salutation based on name>",
  "gender": "<can you guess salutation based on name>",
  "email_id": "?",
  "website": "?",
  "mobile_no": "?",
  "phone": "?",
  "company_name": "?",
  "city": "?",
  "state": "?",
  "country": "?",
})
contact_messages = [
    {
        "role": "user",
        "content": "Format mobile number as a text field, do not include any spaces or other characters.",
    },
    {
        "role": "user",
        "content": "Based on the address details, automatically determine and populate the related fields for the address field, such as country, state, city, pincode, etc.",
    },
]

def extract_structured_data(text,output_schema,user_messages=None):
    user_messages = user_messages or []
    client = get_openai_client()
    settings = frappe.get_single("DocVision Settings")
    messages = [
                {
                    "role": "system",
                    "content": "You are an AI that extracts structured data from text. Fill all ? with appropriate values. if not available, replace with blank.",
                },
                {
                    "role": "assistant",
                    "content": "adjust country name used in the address field to match the country list in ERPNext",
                },
                {
                    "role": "assistant",
                    "content": "if first_name is not available, use the company name as the first_name",
                },
                {
                    "role": "assistant",
                    "content": "guess salutation based on the name here is a list of salutations: Prof, Master, Miss, Madam, Mrs, Dr, Mx, Ms, Mr",
                },
                {
                    "role": "user",
                    "content": f"Extract the relevant information from the following text and format it in the provided JSON format: {text} \nThe format is: {output_schema}",
                },
            ] + user_messages
    try:
        response = client.chat.completions.create(
            model=settings.default_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.9,
        )
        json_response = json.loads(response.choices[0].message.content)
    except openai.RateLimitError as e:
        frappe.throw("Rate limit error")
        return
    except Exception as e:
        frappe.throw("We are unable to extract structured data from the image. Please try again later.")
        return None
    
    return json_response


@frappe.whitelist()
def extract_data_from_image(file_id):
    text = get_text_from_image(file_id)
    structured_data = extract_structured_data(text,contact_schema,contact_messages)
    if not structured_data:
        frappe.throw("Rate limit error")
    structured_data = create_link_field(structured_data)
    return structured_data

def create_link_field(structured_data):
    updated_values = {}
    for key,value in structured_data.items():
        if type(value) == dict and value.get("doctype"):
            try:
                value = create_link_field(value)
                doc = frappe.get_doc(value)
                doc.save()
                updated_values[key] = doc.name
            except Exception as e:
                frappe.log_error(f"Error creating link field for {key}",e)
                updated_values[key] = ""
    structured_data.update(updated_values)
    return structured_data


@frappe.whitelist()
def extract_customer_from_image(file_id):
    text = get_text_from_image(file_id)
    customer_data = extract_structured_data(text,customer_schema,contact_messages)
    if not customer_data:
        frappe.throw("Rate limit error")
    customer_data = create_link_field(customer_data)
    return customer_data

@frappe.whitelist()
def extract_supplier_from_image(file_id):
    text = get_text_from_image(file_id)
    supplier_data = extract_structured_data(text,supplier_schema,contact_messages)
    if not supplier_data:
        frappe.throw("Rate limit error")
    supplier_data = create_link_field(supplier_data)
    return supplier_data

@frappe.whitelist()
def extract_lead_from_image(file_id):
    text = get_text_from_image(file_id)
    supplier_data = extract_structured_data(text,lead_schema,contact_messages)
    if not supplier_data:
        frappe.throw("Rate limit error")
    supplier_data = create_link_field(supplier_data)
    return supplier_data
