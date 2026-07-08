# bale-course-proposal-bot

A Python-based chatbot for **Bale Messenger** designed for **National Skills University** to collect and manage course proposals submitted by professors.

## 🚀 Features

- Submit course proposals through Bale Messenger
- Multi-step conversational workflow
- Professor, Admin, and Super Admin roles
- Excel export for submitted records
- SQLite3 database integration
- Persian/Arabic digit normalization
- Dynamic course count support
- Weekly schedule collection
- Compatible with Bale Messenger API

## 🛠 Tech Stack

- Python
- python-telegram-bot
- SQLite3
- Bale Messenger API
- OpenPyXL

## 📦 Installation

```bash
git clone https://github.com/your-username/bale-course-proposal-bot.git
cd bale-course-proposal-bot
pip install -r requirements.txt
python main.py
```

## 📊 Admin Features

- View submitted records
- Export records to Excel
- Delete records
- Manage administrators
- Role-based access control

## 🔗 Bale API Integration

```python
ApplicationBuilder().token(TOKEN).base_url(
    "https://tapi.bale.ai/bot"
).build()
```

## 📝 License

This project is licensed under the MIT License.
