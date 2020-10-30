# liste_blanche_backend

### Setup Virtual Environment
```terminal
python3 -m venv venv
source venv/bin/activate
```

### Store Requirements
```terminal
pip freeze > requirements.txt
```

### Install Requirements
```terminal
pip install -r requirements.txt
```

### Migrate Database
```terminal
python flask db init
python flask db migrate
python flask db upgrade
```

### Run Summary
The user_email must be save in the database
```terminal
python summary.py <user_email>
```

### Run email scan
The user_email must be save in the database
```terminal
python email_scan.py <user_email>
```
