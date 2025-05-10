# 🌊 StegaMark Pro v2.1

**StegaMark Pro v2.1** is a modern web-based application developed for embedding and detecting watermarks in images using both **visible watermarking** and **invisible steganography techniques (LSB)**.
It was created as part of the *Image Processing* course at **Imam Abdulrahman Bin Faisal University**.

---

## 🚀 Live Demo

* **Frontend:** [StegaMark Pro GitHub Pages](https://goldenahmad.github.io/StegaMark_V2.1/)
* **Backend API:** [PythonAnywhere Endpoint](https://0QuQ.pythonanywhere.com)

---

## ✨ Features

### 🔒 Invisible Watermarking (LSB Steganography)

* Hide text or small logos inside image pixels
* Adjustable encoding strength (choose number of LSBs)
* Extract hidden messages easily

### 💧 Visible Watermarking

* Add text or logo overlays
* Customize opacity, position, color, rotation, and tiling (grid, diagonal, etc.)
* Live preview before applying

### 🖼️ User-Friendly Web Interface

* Upload and preview images
* Dark/Light theme toggle
* Download final watermarked images

### 🧪 Additional Capabilities

* Simple CLI through `app.py` for batch watermarking
* Secure backend (Flask + Pillow)
* REST API: `/watermark`, `/extract`

---

## 🛠️ Project Structure

```
StegaMark_V2.1/
├── app.py             # Flask backend
├── index.html         # Frontend HTML
├── main.js            # Frontend JS logic
├── style.css          # Styling
├── requirements.txt   # Python packages
├── python/            # Watermark encoding/decoding logic
│   └── watermark.py
├── git/               # Git-related config
├── StegaMarkLogo.webp # Logo image
```

---

## 💻 Technologies Used

* **Python 3**, **Flask**, **Pillow**
* **HTML5**, **CSS3** (Tailwind), **JavaScript**
* **GitHub Pages**, **PythonAnywhere**

---

## 📥 How to Run Locally

**Clone the Repository:**

```bash
git clone https://github.com/Turki-Sh/StegaMark_V2.1.git
cd StegaMark_V2.1
```

**Install Requirements:**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**Run Flask App:**

```bash
python app.py web
```

**Set Frontend Endpoint:**

* In `main.js`, make sure the backend URL is set:

```js
const BACKEND_URL = 'http://127.0.0.1:5000';
```

Open `index.html` in your browser.

---

## 👥 Team Members

* **Turki Alshuaibi** — Team Leader
* **Ahmed Alakder** — Head Developer
* **Anas Algamdi** — Developer
* **Hamza Alzahrani** — Developer
* **Khalid Alomair** — Developer

---

## 🔮 Future Improvements

* Add password protection for watermarking
* Support additional image formats
* Enhance watermark detection robustness

---

## 📜 License

Open source under the **MIT License**

---

## 🎓 Acknowledgments

This project was developed as an academic requirement under the supervision of the Department of Computer Science at **Imam Abdulrahman Bin Faisal University**.
