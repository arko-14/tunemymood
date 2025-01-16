# **Tunemymood** 🎵🎶

A web application designed to collect user ratings for songs based on their moods and lay the foundation for predicting songs that match a user's emotional state.

---

## **Project Overview**

This project is divided into two versions:

- **Version 1 (V1)**:
    - A website where users can rate songs based on 7 mood parameters (e.g.,soulful,chill,dramatic,love,sad,exotic,dark).
    - Collects user ratings to analyze how songs resonate with different moods.
- **Version 2 (V2)**:
    - Integrates a machine learning model to predict songs that match the user’s mood in real-time.
    - Provides personalized song recommendations and an enhanced user experience.

---

## **Features**

- Rate songs based on multiple mood categories.
- See where you position at the rating
- Efficient database for seamless data storage and retrieval.
- Dynamic and responsive web interface.
- The database is ever-increasing and linked to spotify's server.
- A handy feature has been added to install the webapp of the website in your device.

---

## **Tech Stack**

| **Component** | **Technology Used** |
| --- | --- |
| **Frontend** | HTML, CSS, Javascript |
| **Backend** | Python (Flask Framework) |
| **Database** | PostgreSQL, AWS S3|
| **Web Scraping** | Selenium |



---

## **Installation & Setup**

### **1. Clone the Repository**

```bash
bash
CopyEdit
git clone https://github.com/arko-14/tunemymood.git
cd tunemymood

```

### **2. Set Up Virtual Environment**

```bash
bash
CopyEdit
python -m venv env
source env/bin/activate   # On Windows: env\Scripts\activate

```

### **3. Install Dependencies**

```bash
bash
CopyEdit
pip install -r requirements.txt

```

### **4. Run the Application**

```bash
bash
CopyEdit
python app.py

```

The website will be accessible at `http://127.0.0.1:5000`.

---

## **Usage Instructions**

1. Open the website in your browser.
2. Search the song which you like.
3. Select a song and rate it based on the 7 mood parameters.
4. See where you stand at index of rating.

---

## **Future Plans (V2)**

- Integrate a machine learning model to analyze the collected mood data and predict songs that match a user’s emotional state.
- Add support for user authentication to save preferences and personalize recommendations.

---

## **Contributing**

Contributions are welcome! If you have suggestions or improvements, feel free to fork the repository and create a pull request.

---

## **License**

This project is licensed under the MIT License. See the LICENSE file for details.

---

## **Contact**

If you have any questions, feedback, or ideas, feel free to reach out:

📧 psandipan20@gmail.com

🌐 [LinkedIn Profile](https://www.linkedin.com/in/sandipan-paul-895915265/)

---
