# Doc Vision

## Overview

**Doc Vision** is a powerful Frappe app that utilizes OpenAI to scan business or other types of cards and automatically create Contact, Lead, Customer, or Supplier records within the Frappe framework. It enhances productivity by automating data extraction and entry, saving users the hassle of manual input.

### Key Features

- **Card Scanning**: Easily scan business cards or other cards directly within the Contact, Lead, Customer, or Supplier doctypes.
- **AI-Powered Data Extraction**: Utilizes OpenAI's cutting-edge technology to accurately extract data from card images, including names, phone numbers, emails, companies, and addresses.
- **Seamless Integration**: Works smoothly with core Frappe doctypes, providing a streamlined workflow.
- **User-Friendly Interface**: Simple and intuitive card scanning, data extraction, and record creation.

---

## Installation

### Pre-requisites

1. Frappe Framework version 14 or higher.
2. An OpenAI API key for accessing data extraction services.

### Steps to Install

1. Run the following commands to install the **Doc Vision** app:

   ```bash
   # Get the Doc Vision app from the repository
   bench get-app https://github.com/finbyz/DocVision.git

   # Install Doc Vision on your site
   bench --site [your-site-name] install-app docvision
   ```

2. Configure the OpenAI API key:

   - Navigate to **Doc Vision Settings** in the Frappe desk.
   - Enter your OpenAI API key to enable AI-based data extraction.

---

## Usage Guide

### Scanning a Card

1. **Access the Doctype**: 
   Go to the **Contact**, **Lead**, **Customer**, or **Supplier** doctype where you want to add a new record.
![](https://finbyz.tech/files/access_documentd0fa05.png)
    
2. **Scan Card**: 
   Click the "Scan Card" button located in the sidebar to start the scanning process.
![](https://finbyz.tech/files/access_document5b9ac1.png)

3. **Upload or Capture Image**:
   - Either use your device camera to capture an image of the business card, or upload an image from your files.
![](https://finbyz.tech/files/upload_card.png)
   
4. **AI Data Extraction**:
   - The app will utilize OpenAI to extract relevant data from the card, such as name, contact details, and company information.

5. **Review and Edit**:
   - Review the extracted information for accuracy. You can edit or update any fields before finalizing the record.
![](https://finbyz.tech/files/after_scane.png)

6. **Save the Record**:
   - Once satisfied, select the type of record you want to create (Contact, Lead, Customer, or Supplier) and save the new entry.

---

## Configuration

### OpenAI API Setup

To use OpenAI for data extraction, you need to configure the app with your OpenAI API key.

1. Navigate to **Doc Vision Settings**.
2. Enter your **OpenAI API Key**.
3. Enter your **Base Url**.
4. Save the settings.

> **Note**: You can use any other API that supports OpenAI and JSON output.

You can also adjust settings like field mapping to ensure the extracted data is stored in the appropriate Frappe fields.

---

## Troubleshooting

### Common Issues

1. **API Key Not Configured**: 
   - Make sure the OpenAI API key is correctly entered in the Doc Vision settings.
   
2. **Incomplete Data Extraction**: 
   - Ensure the card image is clear and contains relevant information. OCR might not work well with poor quality images.

3. **Installation Issues**:
   - If the app fails to install, check your Frappe version and make sure it meets the minimum requirements.

---

## License

Doc Vision is licensed under the [GNU GENERAL PUBLIC LICENSE](license.txt).

---

## Support

If you encounter any issues or have questions about the app, feel free to open an issue on the [GitHub repository](https://github.com/finbyz/DocVision/issues).