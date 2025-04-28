# StegaMark V2.1

**StegaMark V2.1** is a web-based application designed to embed and detect watermarks in images using basic steganography techniques.  
It was developed as part of the *Image Processing* course at **Imam Abdulrahman Bin Faisal University**.

## Project Overview

StegaMark allows users to:
- Upload an image.
- Embed a hidden watermark text into the image.
- Download the watermarked image.
- Extract and read the hidden watermark from a watermarked image.

The system is designed with a simple web interface using **Flask** for the backend and **HTML/CSS/JavaScript** for the frontend.

---

## Features

- **Image Uploading**: Users can upload PNG/JPG images.
- **Watermark Embedding**: Hide custom text into an image.
- **Watermark Extraction**: Retrieve hidden text from a watermarked image.
- **Simple UI**: Easy-to-use web interface.
- **Lightweight Backend**: Built with Python Flask.

---

## Team Members

- **Turki Alshuaibi** — Team Leader
- **Ahmed Alakder** — Head Developer
- **Anas Algamdi** — Developer
- **Hamza Alzahrani** — Developer
- **Khalid Alomair** — Developer

---

## How to Run the Project

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Turki-Sh/StegaMark_V2.1.git
   cd StegaMark_V2.1
   ```

2. **Install the Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask Application**:
   ```bash
   python app.py
   ```

4. **Open the Web App**:
   Navigate to `http://localhost:5000` in your web browser.

---

## Project Structure

```
StegaMark_V2.1/
├── app.py             # Flask backend handling upload and watermark logic
├── index.html         # Main frontend page
├── main.js            # JavaScript for handling frontend actions
├── style.css          # Styling for the web app
├── requirements.txt   # Required Python packages
├── python/            # Contains watermarking logic (encoding/decoding)
│   ├── watermark.py
├── git/               # Git-related configuration (if used)
├── StegaMarkLogo.webp # Logo image
```

---

## Technologies Used

- **Python 3**
- **Flask**
- **HTML5**
- **CSS3**
- **JavaScript**

---

## Screenshots

> *(You can add screenshots here to show how the app looks!)*

---

## Future Improvements

- Improve watermark robustness.
- Support more image formats.
- Add password protection for watermarking.

---

## Acknowledgments

This project was developed as part of an academic requirement under the supervision of the Department of Computer Science, Imam Abdulrahman Bin Faisal University.
