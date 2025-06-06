# dorkingoceans

A Python-based reconnaissance tool for performing automated Google dork searches to discover files and resources on target websites. This tool streamlines the process of finding publicly accessible documents and files through Google's search operators.

## 🔍 Overview

This tool automates Google dorking techniques to help security researchers, penetration testers, and bug bounty hunters discover publicly accessible files on target domains. It uses Google's `site:` and `filetype:` operators to systematically search for documents that may contain sensitive information.

## ✨ Features

- **🎯 Targeted Filetype Search**: Search for specific file extensions (PDF, DOCX, XLS, etc.)
- **📋 Comprehensive Scan**: Automatically iterate through common file types
- **🌐 Broad Discovery**: Perform general site reconnaissance without filetype restrictions  
- **🔄 Duplicate Prevention**: Automatically filters and stores only unique results
- **📁 Organized Output**: Saves results to structured text files with clear naming conventions
- **⚡ Efficient Processing**: Optimized for speed and reliability
-  also made sure to randomize the requests so you dont get a 429 from google 👌

## 🛠️ Prerequisites

- **Python 3.6+**
- Required Python packages:
  - `requests` - HTTP library for making search requests
  - `beautifulsoup4` - HTML parsing and extraction

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tarnishedcoder/dorkingoceans.git
   cd dorkingoceans
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install requests beautifulsoup4
   ```

3. **Configure output directory:**
   
   The tool saves results to a specified directory. Update the `output_base_path` variable in the script:
   ```python
   output_base_path = r"C:\Users\PC\Desktop\bounties\results"  # Windows
   # or
   output_base_path = "/home/user/results"  # Linux/macOS
   ```

## 🚀 Usage

### Basic Usage

Run the script from your terminal:
```bash
python dorker.py
```

Follow the interactive prompts:
1. **Target Website**: Enter the domain (e.g., `example.com`) without protocol
2. **Search Type**: Choose your search strategy

### Search Options

| Option | Description | Example |
|--------|-------------|---------|
| **Specific Filetype** | Search for a particular file extension | `pdf`, `docx`, `xlsx` |
| **All Filetypes** | Scan through predefined common file types | `all` |
| **Broad Search** | General site reconnaissance | `any` |

### Examples

#### 1. Searching for PDF Documents
```
Enter the target website: example.com
Enter the filetype to search for: pdf
```
**Output**: `dorked_links_pdf.txt`

#### 2. Comprehensive Filetype Scan
```
Enter the target website: example.com  
Enter the filetype to search for: all
```
**Output**: Multiple files (`dorked_links_pdf.txt`, `dorked_links_docx.txt`, etc.)

#### 3. General Site Reconnaissance
```
Enter the target website: example.com
Enter the filetype to search for: any
```
**Output**: `dorked_links_any.txt`

## 📂 Output Structure

Results are saved in organized text files:
```
results/
├── dorked_links_pdf.txt
├── dorked_links_docx.txt
├── dorked_links_xlsx.txt
└── dorked_links_any.txt
```

Each file contains unique URLs discovered during the search, one per line.

## 🔧 Configuration

### Supported File Types

The tool includes predefined searches for common file types:
- Documents: `pdf`, `doc`, `docx`, `txt`, `rtf`
- Spreadsheets: `xls`, `xlsx`, `csv`
- Presentations: `ppt`, `pptx`
- Archives: `zip`, `rar`, `tar`
- And more...

### Customization

Modify the script to:
- Add new file types to the search list
- Change output directory structure
- Adjust search parameters and filters
- Customize result formatting

## ⚖️ Legal and Ethical Considerations

**⚠️ IMPORTANT DISCLAIMER:**

This tool is intended for:
- ✅ Authorized security testing
- ✅ Bug bounty programs with proper scope
- ✅ Educational and research purposes
- ✅ Testing your own websites and applications

**DO NOT use this tool for:**
- ❌ Unauthorized reconnaissance
- ❌ Accessing private or confidential information
- ❌ Any illegal or malicious activities

Users are responsible for ensuring their use complies with applicable laws and website terms of service.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📄 License

This project is licensed under the MIT License -

## 🛡️ Security Notice

This tool is provided for legitimate security research purposes. Always ensure you have proper authorization before testing any systems you do not own.


---
