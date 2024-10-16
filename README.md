# Doc Vision

**Doc Vision** is a Frappe app that leverages OpenAI to scan business cards or other types of cards and automatically create records such as Contacts, Leads, Customers, or Suppliers. The app simplifies data entry by extracting and organizing information from physical cards into digital records.

## Features

- **Card Scanning**: Use the "Scan Card" option directly within the Contact, Lead, Supplier, or Customer doctypes to scan business or other cards.
- **AI-Powered Data Extraction**: Uses OpenAI's advanced technology to extract relevant information such as name, phone number, email, company, and address from the scanned card.
- **Automatic Record Creation**: Based on the extracted data, create a Contact, Lead, Customer, or Supplier record effortlessly.
- **User-friendly Workflow**: Review the extracted data before saving to ensure accuracy.

## Installation

1. **Pre-requisites**: Ensure you have Frappe installed and an API key for OpenAI.
2. Run the following commands to install Doc Vision:

```bash
# Install the app in your Frappe environment
bench get-app https://github.com/finbyz/DocVision.git
bench install-app docvision
```

3. **OpenAI Configuration**: After installation, configure your OpenAI API key in the app settings.

## Usage

1. Once installed, the "Scan Card" option will be available in the Contact, Lead, Supplier, and Customer doctypes.
2. Click "Scan Card" to initiate the card scanning process.
3. Capture a card image using your device or upload an image file.
4. OpenAI processes the image and extracts relevant data.
5. Review and adjust the extracted information before saving it as a new Contact, Lead, Supplier, or Customer record.

## Contributions

Contributions are welcome! Feel free to submit a pull request or report any issues on the [GitHub repository](https://github.com/finbyz/DocVision.git).

## License

This project is licensed under the MIT License. See the [LICENSE](license.txt) file for more details.